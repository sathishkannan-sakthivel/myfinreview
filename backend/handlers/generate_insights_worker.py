import json
import logging
import asyncio
from ai.insight_service import InsightService
from services.portfolio_service import PortfolioService
from change_detection.engine import ChangeDetectionEngine
from repositories.dynamo_client import DynamoClient
from datetime import datetime, timedelta
from utils.idempotency.guard import WorkerExecutionGuard

logger = logging.getLogger(__name__)

insight_service = InsightService()
portfolio_service = PortfolioService()
change_engine = ChangeDetectionEngine()
client = DynamoClient()
guard = WorkerExecutionGuard()

def lambda_handler(event, context):
    try:
        user_id = event.get('user_id', 'test_user')
        
        # --- Idempotency ---
        idem_key = guard.generate_key("generate_insights_worker", user_id, event)
        is_processed, prev_result = guard.check_and_mark(idem_key)
        if is_processed:
            return {'statusCode': 200, 'body': json.dumps({'message': 'Already processed', 'result': prev_result})}

        # 1. Fetch Current Analytics Snapshot
        curr_analytics = client.get_item(f'USER#{user_id}', 'ANALYTICS#LATEST') or {}
        
        # --- Event Safety (Versioning) ---
        required_version = event.get('required_analytics_version', 0)
        current_version = curr_analytics.get('version', 0)
        if required_version > 0 and current_version < required_version:
            logger.info(f"Waiting for latest analytics v{required_version}. Current is v{current_version}.")
            return {'statusCode': 200, 'body': 'Stale analytics for insights'}
        
        # 2. Fetch Previous Snapshot (Fetch all history and pick the one before the current)
        history = client.query_items(f'USER#{user_id}', 'ANALYTICS#HIST#')
        # Sort by timestamp descending
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        prev_analytics = history[1] if len(history) > 1 else {}

        # 3. Fetch New Alerts (last 24 hours)
        # Assuming timestamp in SK: ALERT#<timestamp>#<eventId>
        # To simplify MVP, we fetch all and filter or just take the latest 5
        alerts = client.query_items(f'USER#{user_id}', 'ALERT#')
        alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        new_alerts = alerts[:5]

        # 4. Fetch New News
        summary = portfolio_service.get_portfolio_summary(user_id)
        symbols = [h.get('symbol') for h in summary.get('holdings', [])]
        new_news = {} # Symbols -> [News]
        # Logic to fetch news for each symbol from Dynamo DB - PK=NEWS#<symbol>
        for symbol in symbols:
            news = client.query_items(f'NEWS#{symbol}', 'TS#')
            new_news[symbol] = news[:3] # Latest 3 for change detection

        # 5. Run Change Detection
        change_summary = change_engine.run(user_id, prev_analytics, curr_analytics, new_alerts, new_news)

        # 6. Store Change Summary in DynamoDB
        change_item = {
            'PK': f'USER#{user_id}',
            'SK': f"CHANGE#HIST#{change_summary.timestamp}",
            'events': [
                {
                    "type": e.type.value,
                    "description": e.description,
                    "impact": e.impact_score,
                    "metadata": e.metadata
                } for e in change_summary.events
            ],
            'total_impact': float(change_summary.total_impact),
            'summary_text': change_summary.summary_text,
            'timestamp': change_summary.timestamp
        }
        client.put_item(change_item)
        
        latest_change = change_item.copy()
        latest_change['SK'] = 'CHANGE#LATEST'
        client.put_item(latest_change)

        # 7. Generate structured AI insights
        logger.debug(f"Generating structured insights for user {user_id}...")
        # Using the refined pipeline (async)
        insights = asyncio.run(insight_service.generate_structured_insights(user_id, change_item, curr_analytics))

        # --- Finalize ---
        final_result = {'insights_count': len(insights)}
        guard.finalize(idem_key, final_result)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Change detection and insights generated successfully',
                **final_result
            })
        }
    except Exception as e:
        logger.exception(f"Error in change detection/insights worker: {e}")
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}
