from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any


class SessionPhase(str, Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"


@dataclass
class SessionContext:
    root_intent: Optional[str] = None
    last_intent: Optional[str] = None
    last_result_tracks: Optional[List[str]] = None
    last_strategy: Optional[Dict[str, Any]] = None
    phase: SessionPhase = SessionPhase.IDLE
    last_interaction_ts: datetime = field(default_factory=datetime.utcnow)

    def update_timestamp(self):
        self.last_interaction_ts = datetime.utcnow()

    def reset(self):
        self.root_intent = None
        self.last_intent = None
        self.last_result_tracks = None
        self.last_strategy = None
        self.phase = SessionPhase.IDLE
        self.update_timestamp()