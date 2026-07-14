import json
from datetime import datetime
from services.portfolio_service import PortfolioService
from analytics.calculator import PortfolioAnalyticsCalculator
from analytics.models import PortfolioAnalyticsInput, CashFlow
from repositories.dynamo_client import DynamoClient
from utils.idempotency.guard import WorkerExecutionGuard

portfolio_service = PortfolioService()
calculator = PortfolioAnalyticsCalculator()
client = DynamoClient()
guard = WorkerExecutionGuard()

def lambda_handler(event, context):
    try:
        user_id = event.get('user_id', 'test_user')
        
        # --- Idempotency & Safety Layer ---
        # Generate key based on user and specific event data (like a requestId or specific window)
        # For analytics, we can use a window-based key or an event source ID
        idem_key = guard.generate_key("analytics_calculator", user_id, event)
        is_processed, prev_result = guard.check_and_mark(idem_key)
        if is_processed:
            print(f"Skipping: Analytics already processed for key {idem_key}")
            return {'statusCode': 200, 'body': json.dumps({'message': 'Already processed', 'result': prev_result})}

        # --- Versioning Check (Sequential processing) ---
        # If the event contains a version, ensure it's higher than the latest stored version
        incoming_version = event.get('analytics_version', 0)
        latest_analytics = client.get_item(f'USER#{user_id}', 'ANALYTICS#LATEST')
        if latest_analytics:
            current_version = latest_analytics.get('version', 0)
            if incoming_version > 0 and incoming_version <= current_version:
                print(f"Stale analytics request (v{incoming_version}). Current version is v{current_version}.")
                return {'statusCode': 200, 'body': json.dumps({'message': 'Stale version ignored'})}
        else:
            current_version = 0

        # --- Business Logic ---
        # 1. Fetch current portfolio summary
        summary = portfolio_service.get_portfolio_summary(user_id)
        current_valuation = summary.get('total_valuation', 0.0)
        
        # 2. Fetch all transactions for cashflow calculation
        transactions = portfolio_service.tx_repo.get_transactions(user_id)
        
        # 3. Map transactions to CashFlow objects
        # BUY = Negative Cashflow (Money out), SELL = Positive (Money in)
        cashflows = []
        for tx in transactions:
            tx_type = tx.get('type', 'BUY')
            amount = float(tx.get('quantity', 0.0)) * float(tx.get('price', 0.0))
            # Money leaving user for investment (negative)
            # Money coming in from sale (positive)
            signed_amount = -amount if tx_type == 'BUY' else amount
            
            ts_str = tx.get('timestamp')
            if ts_str:
                dt = datetime.fromisoformat(ts_str).date()
            else:
                dt = datetime.utcnow().date()
            
            cashflows.append(CashFlow(amount=signed_amount, date=dt))

        # 4. Map holdings for concentration analysis
        holdings_input = []
        for h in summary.get('holdings', []):
            holdings_input.append({
                'symbol': h.get('symbol'),
                'value': float(h.get('current_valuation', 0.0))
            })

        # 5. Build Input and Compute
        input_data = PortfolioAnalyticsInput(
            user_id=user_id,
            current_valuation=current_valuation,
            cashflows=cashflows,
            holdings=holdings_input
        )
        
        result = calculator.compute(input_data)

        # 6. Store Result in DynamoDB
        # Store as LATEST for easy retrieval
        analytics_item = {
            'PK': f'USER#{user_id}',
            'SK': 'ANALYTICS#LATEST',
            'portfolio_value': float(result.portfolio_value),
            'xirr': float(result.xirr),
            'concentration_score': float(result.concentration_score),
            'top_holdings': result.top_holdings,
            'is_concentrated': result.is_concentrated,
            'timestamp': result.timestamp,
            'version': incoming_version if incoming_version > 0 else current_version + 1
        }
        client.put_item(analytics_item)
        
        # Also store with TIMESTAMP for history
        history_item = analytics_item.copy()
        history_item['SK'] = f"ANALYTICS#HIST#{result.timestamp}"
        client.put_item(history_item)
        
        # --- Finalize Idempotency ---
        final_result = {
            'user_id': user_id,
            'xirr': float(result.xirr),
            'is_concentrated': result.is_concentrated,
            'version': analytics_item['version']
        }
        guard.finalize(idem_key, final_result)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Analytics calculated and stored',
                'user_id': user_id,
                'xirr': f"{result.xirr * 100:.2f}%",
                'is_concentrated': result.is_concentrated,
                'version': analytics_item['version']
            })
        }
    except Exception as e:
        print(f"Error calculating analytics: {e}")
        import traceback
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}

