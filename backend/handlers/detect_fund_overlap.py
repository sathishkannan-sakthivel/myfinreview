import json
from overlap.engine import OverlapEngine
from utils.idempotency.guard import WorkerExecutionGuard

engine = OverlapEngine()
guard = WorkerExecutionGuard()

def lambda_handler(event, context):
    try:
        user_id = event.get('user_id', 'test_user')
        
        # --- Idempotency ---
        idem_key = guard.generate_key("overlap_engine", user_id, event)
        is_processed, prev_result = guard.check_and_mark(idem_key)
        if is_processed:
            return {'statusCode': 200, 'body': json.dumps({'message': 'Already processed', 'result': prev_result})}

        # 1. Generate Overlap Result
        print(f"Detecting mutual fund overlap for user {user_id}...")
        result = engine.generate_overlap_result(user_id)

        if not result:
            return {'statusCode': 200, 'body': json.dumps({'message': 'No mutual fund data to analyze'})}

        # --- Finalize ---
        final_result = {
            'timestamp': result.timestamp,
            'overlap_severity': result.overlap_severity,
            'total_overlap_score': float(result.total_overlap_score)
        }
        guard.finalize(idem_key, final_result)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Overlap analysis completed',
                **final_result
            })
        }
    except Exception as e:
        print(f"Error detecting overlap: {e}")
        import traceback
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}
