from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any


class SessionPhase(str, Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"


@dataclass
class SessionContext:
    # Intent memory
    root_intent: Optional[str] = None
    last_intent: Optional[str] = None

    # Strategy memory
    last_strategy: Optional[Dict[str, Any]] = None

    # Result memory
    last_result_tracks: Optional[List[str]] = None

    # NEW: Target memory
    last_playlist_name: Optional[str] = None

    # Lifecycle
    phase: SessionPhase = SessionPhase.IDLE
    last_interaction_ts: datetime = field(default_factory=datetime.utcnow)

    def update_timestamp(self):
        self.last_interaction_ts = datetime.utcnow()

    def reset(self):
        self.root_intent = None
        self.last_intent = None
        self.last_strategy = None
        self.last_result_tracks = None
        self.last_playlist_name = None
        self.phase = SessionPhase.IDLE
        self.update_timestamp()