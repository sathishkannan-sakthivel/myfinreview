from repositories.idempotency_repository import IdempotencyRepository
import hashlib
import json

class WorkerExecutionGuard:
    def __init__(self):
        self.repo = IdempotencyRepository()

    def generate_key(self, worker_name, user_id, event_data):
        # Deterministic key based on worker name, user, and relevant event data (e.g., timestamp, request_id)
        # Convert event_data to a sorted JSON string for consistency
        event_str = json.dumps(event_data, sort_keys=True)
        raw_key = f"{worker_name}:{user_id}:{event_str}"
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def check_and_mark(self, key):
        """
        Check if the key exists.
        Returns:
            (is_processed, previous_result)
        """
        record = self.repo.get_idempotency_record(key)
        if record:
            if record.get('status') == 'COMPLETED':
                return True, record.get('result')
            if record.get('status') == 'IN_PROGRESS':
                # Replay safety: Wait or skip if already in progress
                # For Lambda, usually skip and let SQS retry if it fails
                return True, None
        
        # Mark as in progress if not already COMPLETED
        self.repo.mark_in_progress(key)
        return False, None

    def finalize(self, key, result):
        """
        Finalize the idempotency record with the result.
        """
        self.repo.save_idempotency_record(key, result)
