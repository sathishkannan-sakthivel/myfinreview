from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

class ChangeType(Enum):
    ALLOCATION = "ALLOCATION"
    VALUE = "VALUE"
    CONCENTRATION = "CONCENTRATION"
    ALERT = "ALERT"
    NEWS = "NEWS"

@dataclass
class ChangeEvent:
    type: ChangeType
    description: str
    impact_score: float # 0 to 10 scale
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChangeSummary:
    user_id: str
    timestamp: str
    events: List[ChangeEvent]
    total_impact: float
    summary_text: Optional[str] = None
