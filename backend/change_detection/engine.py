from typing import List, Dict, Any
from datetime import datetime
from .models import ChangeEvent, ChangeSummary, ChangeType
from .detectors.allocation_change import AllocationChangeDetector
from .detectors.value_change import ValueChangeDetector
from .detectors.concentration_change import ConcentrationChangeDetector
from .detectors.new_alerts import NewAlertsDetector
from .detectors.news_impact import NewsImpactDetector

class ChangeDetectionEngine:
    def __init__(self):
        self.allocation_detector = AllocationChangeDetector()
        self.value_detector = ValueChangeDetector()
        self.concentration_detector = ConcentrationChangeDetector()
        self.alerts_detector = NewAlertsDetector()
        self.news_detector = NewsImpactDetector()

    def run(self, user_id: str, prev_snapshot: Dict[str, Any], curr_snapshot: Dict[str, Any], 
            new_alerts: List[Dict[str, Any]], new_news: Dict[str, List[Dict[str, Any]]]) -> ChangeSummary:
        
        events = []
        
        # 1. Run Snapshots Detectors
        events.extend(self.allocation_detector.detect(prev_snapshot, curr_snapshot))
        events.extend(self.value_detector.detect(prev_snapshot, curr_snapshot))
        events.extend(self.concentration_detector.detect(prev_snapshot, curr_snapshot))
        
        # 2. Run Event Detectors
        events.extend(self.alerts_detector.detect(new_alerts))
        events.extend(self.news_detector.detect(new_news))
        
        # 3. Calculate Total Impact
        total_impact = sum(e.impact_score for e in events)
        if events:
            total_impact = min(total_impact / len(events), 10.0)
            
        # 4. Generate Summary Text (Basic)
        summary_text = f"Detected {len(events)} meaningful changes in your portfolio today."
        if total_impact > 7:
            summary_text += " There are high-impact events requiring your attention."
            
        return ChangeSummary(
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat(),
            events=events,
            total_impact=total_impact,
            summary_text=summary_text
        )
