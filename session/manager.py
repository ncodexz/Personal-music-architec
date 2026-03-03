from datetime import datetime, timedelta

from session.context import SessionContext, SessionPhase
from core.graph.state import MusicState


class SessionManager:

    def __init__(self, graph, llm, timeout_seconds: int = 60):
        self.graph = graph
        self.llm = llm
        self.context = SessionContext()
        self.timeout = timedelta(seconds=timeout_seconds)

    def handle(self, user_input: str) -> MusicState:

        self._check_timeout()
        self.context.update_timestamp()

        intent = self._detect_intent(user_input)

        if (
            self.context.root_intent
            and intent != self.context.root_intent
            and not (
                (self.context.root_intent == "build" and intent == "modify")
                or
                (self.context.root_intent == "info" and intent == "modify")
            )
    ):
            self.context.reset()

        if not self.context.root_intent:
            self.context.root_intent = intent

        state = self._build_default_state(user_input, intent)

        result_state = self.graph.invoke(state)

        self._update_context(result_state)

        return result_state

    def _detect_intent(self, user_input: str) -> str:

        normalized = user_input.strip().lower()

        if normalized.startswith(("add", "delete", "remove", "rename", "adapt")):
            return "modify"

        prompt = f"""
        Classify the following user request into EXACTLY one of these categories:

        - "build"
        - "modify"
        - "info"
        - "unknown"

        Only return the word.

        User request:
        "{user_input}"
        """

        response = self.llm.invoke(prompt)
        intent = response.content.strip().lower()

        if intent not in ["build", "modify", "info"]:
            return "unknown"

        return intent

    def _build_default_state(self, user_input: str, intent: str) -> MusicState:
        return {
            "user_input": user_input,
            "strategy": None,
            "result_tracks": None,
            "error": None,
            "needs_clarification": False,
            "clarification_message": None,
            "confirmed": False,
            "intent": intent,
            "last_playlist_name": self.context.last_playlist_name,
            "last_strategy": self.context.last_strategy,
            "created_playlist_name": None,
        }

    def _update_context(self, state: MusicState):

        intent = state.get("intent")
        result_tracks = state.get("result_tracks")
        strategy = state.get("strategy")
        needs_clarification = state.get("needs_clarification")

        if intent == "unknown":
            self.context.reset()
            return

        # Store result tracks only if execution happened successfully
        if result_tracks and not needs_clarification:
            self.context.last_result_tracks = result_tracks

        # Store strategy only if it passed validation
        if strategy and not needs_clarification:
            self.context.last_strategy = strategy

        # Update playlist name only if a new one was actually created
        created = state.get("created_playlist_name")
        if created:
            self.context.last_playlist_name = created
        
        #clear playlist name if it was deleted
        deleted = state.get("deleted_playlist")
        if deleted and deleted == self.context.last_playlist_name:
            self.context.last_playlist_name = None

        self.context.last_intent = intent
        self.context.phase = SessionPhase.ACTIVE


    def _check_timeout(self):
        if datetime.utcnow() - self.context.last_interaction_ts > self.timeout:
            self.context.reset()