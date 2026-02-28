from datetime import datetime, timedelta
from typing import Dict, Any

from session.context import SessionContext, SessionPhase
from core.graph.state import MusicState


class SessionManager:

    def __init__(self, graph, timeout_seconds: int = 60):
        self.graph = graph
        self.context = SessionContext()
        self.timeout = timedelta(seconds=timeout_seconds)

    # =====================================================
    # PUBLIC ENTRY
    # =====================================================

    def handle(self, user_input: str) -> MusicState:

        self._check_timeout()
        self.context.update_timestamp()

        # 1️⃣ Confirmation handling
        if self._is_confirmation(user_input):
            return self._handle_confirmation()

        # 2️⃣ Reference-based explicit build
        explicit_strategy = self._build_explicit_strategy_if_reference(user_input)

        if explicit_strategy:
            state = self._build_state(user_input, explicit_strategy, intent="build")
        else:
            state = self._build_default_state(user_input)

        result_state = self.graph.invoke(state)

        self._update_context(result_state)

        return result_state

    # =====================================================
    # CONFIRMATION FLOW
    # =====================================================

    def _is_confirmation(self, user_input: str) -> bool:
        if self.context.phase == SessionPhase.WAITING_CONFIRMATION:
            normalized = user_input.strip().lower()
            return normalized in ["yes", "y", "ok", "confirm", "si", "sí"]
        return False

    def _handle_confirmation(self) -> MusicState:

        if not self.context.last_strategy:
            self.context.reset()
            return self._build_default_state("")

        state: MusicState = {
            "user_input": "",
            "strategy": self.context.last_strategy,
            "result_tracks": self.context.last_result_tracks,
            "error": None,
            "needs_clarification": False,
            "clarification_message": None,
            "confirmed": True,
            "intent": self.context.last_intent,
        }

        result_state = self.graph.invoke(state)

        self._update_context(result_state)

        return result_state

    # =====================================================
    # STATE BUILDERS
    # =====================================================

    def _build_default_state(self, user_input: str) -> MusicState:
        return {
            "user_input": user_input,
            "strategy": None,
            "result_tracks": None,
            "error": None,
            "needs_clarification": False,
            "clarification_message": None,
            "confirmed": False,
            "intent": "",
        }

    def _build_state(self, user_input: str, strategy: Dict[str, Any], intent: str) -> MusicState:
        return {
            "user_input": user_input,
            "strategy": strategy,
            "result_tracks": None,
            "error": None,
            "needs_clarification": False,
            "clarification_message": None,
            "confirmed": False,
            "intent": intent,
        }

    # =====================================================
    # REFERENCE HANDLING
    # =====================================================

    def _build_explicit_strategy_if_reference(self, user_input: str):

        lower_input = user_input.lower()
        reference_words = ["that", "eso", "lo anterior"]

        if (
            any(word in lower_input for word in reference_words)
            and self.context.last_result_tracks
        ):
            return {
                "goal": "build",
                "target": {
                    "type": "playlist",
                    "identifier": None,
                },
                "sources": [
                    {
                        "type": "explicit",
                        "filters": {
                            "track_ids": self.context.last_result_tracks
                        },
                    }
                ],
                "modification": None,
                "constraints": {
                    "max_tracks": None,
                    "deduplicate": False,
                    "merge_strategy": None,
                },
            }

        return None

    # =====================================================
    # CONTEXT UPDATE
    # =====================================================

    def _update_context(self, state: MusicState):

        intent = state.get("intent")
        needs_clarification = state.get("needs_clarification")
        result_tracks = state.get("result_tracks")
        strategy = state.get("strategy")

        if intent == "unknown":
            self.context.reset()
            return

        if result_tracks:
            self.context.last_result_tracks = result_tracks

        if strategy:
            self.context.last_strategy = strategy

        self.context.last_intent = intent

        if needs_clarification:
            self.context.phase = SessionPhase.WAITING_CONFIRMATION
        else:
            self.context.phase = SessionPhase.ACTIVE

    # =====================================================
    # TIMEOUT
    # =====================================================

    def _check_timeout(self):
        if datetime.utcnow() - self.context.last_interaction_ts > self.timeout:
            self.context.reset()