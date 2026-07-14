import json
from news.news_service import NewsService
from services.portfolio_service import PortfolioService
from utils.idempotency.guard import WorkerExecutionGuard

news_service = NewsService()
portfolio_service = PortfolioService()
guard = WorkerExecutionGuard()

def lambda_handler(event, context):
    try:
        user_id = event.get('user_id', 'test_user')
        
        # --- Idempotency ---
        # For news, we can use the current date in the event for daily ingestion idempotency
        idem_key = guard.generate_key("news_ingest_worker", user_id, event)
        is_processed, prev_result = guard.check_and_mark(idem_key)
        if is_processed:
            return {'statusCode': 200, 'body': json.dumps({'message': 'Already processed', 'result': prev_result})}

        # 1. Fetch symbols from user's holdings
        user_id = event.get('user_id', 'test_user')
        summary = portfolio_service.get_portfolio_summary(user_id)
        symbols = [h.get('symbol') for h in summary.get('holdings', [])]

        if not symbols:
            print(f"No symbols found for user {user_id}. Skipping news ingestion.")
            return {'statusCode': 200, 'body': 'No symbols found'}

        # 2. Fetch and store news for each symbol
        print(f"Ingesting news for symbols: {symbols}")
        news_service.fetch_and_store_news(symbols)

        # --- Finalize ---
        final_result = {'symbols_processed': len(symbols)}
        guard.finalize(idem_key, final_result)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'News ingested successfully',
                **final_result
            })
        }
    except Exception as e:
        print(f"Error ingesting news: {e}")
        import traceback
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}
