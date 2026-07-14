from typing import List
from .models import NotificationEvent, NotificationDigest, NotificationType
from datetime import datetime

class NotificationDigestBuilder:
    """
    Batches notification events into a single digest summary.
    """
    def build(self, user_id: str, events: List[NotificationEvent]) -> NotificationDigest:
        if not events:
            return None

        # Categorize by type for the summary
        categorized = {}
        for e in events:
            etype = e.type.value
            if etype not in categorized:
                categorized[etype] = []
            categorized[etype].append(e)

        summary_lines = [f"🧞 Here's your portfolio daily digest for {datetime.utcnow().date()}:"]
        
        if NotificationType.ALERT.value in categorized:
            count = len(categorized[NotificationType.ALERT.value])
            summary_lines.append(f"- You had {count} new alert(s) today.")
            
        if NotificationType.REBALANCE.value in categorized:
            summary_lines.append("- A new rebalancing plan is available for your review.")
            
        if NotificationType.INSIGHT.value in categorized:
            count = len(categorized[NotificationType.INSIGHT.value])
            summary_lines.append(f"- We've generated {count} new AI insight(s) about your holdings.")

        summary_text = "
".join(summary_lines)

        return NotificationDigest(
            user_id=user_id,
            events=events,
            summary_text=summary_text,
            timestamp=datetime.utcnow().isoformat()
        )
