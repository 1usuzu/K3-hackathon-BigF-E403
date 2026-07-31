from dataclasses import dataclass, field
from typing import List

@dataclass
class NodeLinkMatch:
    node_id: str
    node_stable_id: str
    confidence_score: float
    match_reasons: List[str] = field(default_factory=list)
