import json
from alerts.engine import AlertsEngine
from alerts.models import AlertRule, AlertType, Severity
from repositories.dynamo_client import DynamoClient
from utils.idempotency.guard import WorkerExecutionGuard

engine = AlertsEngine()
client = DynamoClient()
guard = WorkerExecutionGuard()

def lambda_handler(event, context):
    try:
        user_id = event.get('user_id', 'test_user')
        
        # --- Idempotency ---
        idem_key = guard.generate_key("alerts_evaluator", user_id, event)
        is_processed, prev_result = guard.check_and_mark(idem_key)
        if is_processed:
            return {'statusCode': 200, 'body': json.dumps({'message': 'Already processed', 'result': prev_result})}

        # 1. Load Analytics Snapshot from DynamoDB
        # PK=USER#<userId>, SK=ANALYTICS#LATEST
        analytics = client.get_item(f'USER#{user_id}', 'ANALYTICS#LATEST')
        if not analytics:
            print(f"No analytics found for {user_id}. Cannot evaluate alerts.")
            return {'statusCode': 200, 'body': 'No analytics found'}

        # --- Versioning check (Event Safety) ---
        # If the trigger event points to a specific analytics version, ensure we are not processing a stale one
        required_version = event.get('required_analytics_version', 0)
        current_version = analytics.get('version', 0)
        if required_version > 0 and current_version < required_version:
            print(f"Analytics version (v{current_version}) is behind required v{required_version}. Skipping.")
            return {'statusCode': 200, 'body': 'Analytics version mismatch'}

        # 2. Fetch User Alert Rules (MVP: Mock some rules)
        # In production, these would be in DynamoDB with PK=USER#<userId>, SK starts_with(RULE#)
        rules = [
            AlertRule("R1", user_id, AlertType.CONCENTRATION, threshold=40.0, severity=Severity.CRITICAL),
            AlertRule("R2", user_id, AlertType.PORTFOLIO_CHANGE, threshold=5.0, severity=Severity.WARNING)
        ]
        
        # 3. Prepare context for evaluation
        # analytics_result = {
        #    'PK': f'USER#{user_id}',
        #    'SK': 'ANALYTICS',
        #    'portfolio_value': float(result.portfolio_value),
        #    'xirr': float(result.xirr),
        #    'concentration_score': float(result.concentration_score),
        #    'top_holdings': result.top_holdings,
        #    'is_concentrated': result.is_concentrated,
        #    'timestamp': result.timestamp
        # }
        
        context_data = {
            'prices': {}, # In a real scenario, fetch current prices for price alerts
            'allocation': { h[0]: h[1] for h in analytics.get('top_holdings', []) },
            'concentration_score': float(analytics.get('concentration_score', 0.0)),
            'portfolio_change_pct': 0.0 # Need to compare with previous snapshots
        }

        # 4. Evaluate rules
        result = engine.evaluate_rules(rules, context_data)

        # 5. Save Alert Events to DynamoDB
        # PK=USER#<userId>, SK=ALERT#<timestamp>#<eventId>
        for event in result.events:
            alert_item = {
                'PK': f'USER#{user_id}',
                'SK': f"ALERT#{event.timestamp}#{event.event_id}",
                'rule_id': event.rule_id,
                'type': event.type.value,
                'message': event.message,
                'severity': event.severity.value,
                'timestamp': event.timestamp,
                'data': event.data
            }
            client.put_item(alert_item)
            print(f"Alert generated: {event.message}")

        # --- Finalize ---
        final_result = {'events_generated': len(result.events)}
        guard.finalize(idem_key, final_result)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Alerts evaluated',
                **final_result
            })
        }
    except Exception as e:
        print(f"Error evaluating alerts: {e}")
        import traceback
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}
