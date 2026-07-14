import json
import logging
from rebalancing.engine import RebalancingEngine
from rebalancing.models import TargetAllocation
from utils.idempotency.guard import WorkerExecutionGuard

# This handler now performs a drift diagnostic only – no buy/sell advice.
engine = RebalancingEngine()
guard = WorkerExecutionGuard()

def lambda_handler(event, context):
    try:
        user_id = event.get('user_id', 'test_user')
        
        # --- Idempotency ---
        idem_key = guard.generate_key("rebalance_engine", user_id, event)
        is_processed, prev_result = guard.check_and_mark(idem_key)
        if is_processed:
            return {'statusCode': 200, 'body': json.dumps({'message': 'Already processed', 'result': prev_result})}

        # 1. Fetch User Target Allocations
        # In production, these are stored in DynamoDB PK=USER#<userId>, SK=TARGETS
        # For MVP, we use some defaults
        raw_targets = event.get('targets', [
            {"symbol": "AAPL", "target_weight": 40.0},
            {"symbol": "GOOGL", "target_weight": 30.0},
            {"symbol": "MSFT", "target_weight": 30.0}
        ])
        
        targets = [TargetAllocation(t['symbol'], t['target_weight']) for t in raw_targets]

        # 2. Compute drift diagnostic only
        logger = __import__('logging').getLogger(__name__)
        logger.debug(f"Computing drift diagnostic for user {user_id}...")
        diag = engine.compute_drift(user_id, targets)

        if 'error' in diag:
            return {'statusCode': 400, 'body': json.dumps({'message': diag['error']})}

        # --- Finalize ---
        guard.finalize(idem_key, diag)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Drift diagnostic computed',
                **diag
            })
        }
    except Exception as e:
        print(f"Error generating rebalance plan: {e}")
        import traceback
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}
