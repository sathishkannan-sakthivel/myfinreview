import json
from notifications.models import NotificationEvent, NotificationType, NotificationPriority
from notifications.orchestrator import NotificationOrchestrator
from utils.idempotency.guard import WorkerExecutionGuard

orchestrator = NotificationOrchestrator()
guard = WorkerExecutionGuard()

def lambda_handler(event, context):
    try:
        user_id = event.get('user_id', 'test_user')
        
        # --- Idempotency ---
        idem_key = guard.generate_key("notification_orchestrator", user_id, event)
        is_processed, prev_result = guard.check_and_mark(idem_key)
        if is_processed:
            return {'statusCode': 200, 'body': json.dumps({'message': 'Already processed', 'result': prev_result})}

        # 1. Transform raw events (Alert, Insight, Rebalance) to NotificationEvents
        # Input 'event' could be from SQS, EventBridge, or direct Lambda trigger
        source_id = event.get('source_id')
        event_type_str = event.get('type', 'ALERT') # Default for MVP
        
        try:
            ntype = NotificationType[event_type_str]
        except KeyError:
            ntype = NotificationType.ALERT

        # 2. Build NotificationEvent
        notif_event = NotificationEvent(
            event_id=event.get('request_id', 'E1'),
            user_id=user_id,
            type=ntype,
            title=event.get('title', 'Portfolio Update'),
            message=event.get('message', 'There is a new update for your portfolio.'),
            priority=NotificationPriority.MEDIUM, # Prioritizer will refine this if needed
            source_id=source_id,
            metadata=event.get('metadata', {})
        )

        # 3. Fetch User Preferences (MVP: Mock)
        user_prefs = {
            'enabled_channels': ['PUSH', 'EMAIL'],
            'enable_quiet_hours': True
        }

        # 4. Orchestrate Delivery
        print(f"Orchestrating notification for user {user_id}...")
        decision = orchestrator.process_event(notif_event, user_prefs)

        # --- Finalize ---
        final_result = {
            'delivered': decision.should_deliver,
            'reason': decision.reason,
            'channels': [str(c) for c in decision.channels]
        }
        guard.finalize(idem_key, final_result)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Notification processed',
                **final_result
            })
        }
    except Exception as e:
        print(f"Error orchestrating notification: {e}")
        import traceback
        traceback.print_exc()
        return {'statusCode': 500, 'body': json.dumps({'message': str(e)})}
