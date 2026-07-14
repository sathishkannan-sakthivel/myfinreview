from .models import NotificationEvent, NotificationPriority, NotificationType

class NotificationPrioritizer:
    """
    Determines notification priority based on type and importance score/severity.
    """
    def prioritize(self, event_type: NotificationType, score: float) -> NotificationPriority:
        # Rules to map raw signal scores to notification priority
        if event_type == NotificationType.ALERT:
            if score >= 8.0: return NotificationPriority.URGENT
            if score >= 5.0: return NotificationPriority.HIGH
            return NotificationPriority.MEDIUM
            
        if event_type == NotificationType.REBALANCE:
            if score >= 8.0: return NotificationPriority.HIGH
            return NotificationPriority.MEDIUM

        if event_type == NotificationType.INSIGHT:
            if score >= 8.0: return NotificationPriority.MEDIUM
            return NotificationPriority.LOW
            
        return NotificationPriority.LOW

    def should_deliver_immediately(self, priority: NotificationPriority) -> bool:
        # Immediate delivery for URGENT and HIGH priority events
        return priority in [NotificationPriority.URGENT, NotificationPriority.HIGH]
