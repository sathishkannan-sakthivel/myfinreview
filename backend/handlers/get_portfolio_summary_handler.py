import json
from services.portfolio_service import PortfolioService
from ai.insight_service import InsightService
from news.news_service import NewsService
from repositories.dynamo_client import DynamoClient

portfolio_service = PortfolioService()
insight_service = InsightService()
news_service = NewsService()
client = DynamoClient()

def lambda_handler(event, context):
    try:
        query_params = event.get('queryStringParameters', {}) or {}
        user_id = query_params.get('user_id', 'test_user')

        # 1. Fetch Core Portfolio Summary
        summary = portfolio_service.get_portfolio_summary(user_id)
        
        # 2. Fetch Latest AI Insights
        summary['ai_insights'] = insight_service.get_latest_insights(user_id)
        
        # 3. Fetch Portfolio-specific News
        symbols = [h.get('symbol') for h in summary.get('holdings', [])]
        summary['latest_news'] = news_service.get_user_news(symbols)

        # 4. Fetch Latest Rebalance Plan
        summary['rebalance_plan'] = client.get_item(f'USER#{user_id}', 'REBALANCE#LATEST') or {}

        # 5. Fetch Latest Fund Overlap
        summary['fund_overlap'] = client.get_item(f'USER#{user_id}', 'OVERLAP#LATEST') or {}
        
        return {
            'statusCode': 200,
            'body': json.dumps(summary)
        }
    except Exception as e:
        print(f"Error fetching portfolio summary: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'body': json.dumps({'message': str(e)})
        }
