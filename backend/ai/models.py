from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class InsightType(Enum):
    DAILY_SUMMARY = "DAILY_SUMMARY"
    RISK_INSIGHT = "RISK_INSIGHT"
    ACTION_SUGGESTION = "ACTION_SUGGESTION"
    CHANGE_EXPLANATION = "CHANGE_EXPLANATION"
    PORTFOLIO_BRIEFING = "PORTFOLIO_BRIEFING"

@dataclass
class Insight:
    user_id: str
    type: InsightType
    content: str
    importance_score: float  # 0 to 10 scale
    confidence_score: float  # 0.0 to 1.0 scale
    source_signals: List[str]  # Event IDs or types that triggered this
    explanation_data: Dict[str, Any]
    change_hash: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
