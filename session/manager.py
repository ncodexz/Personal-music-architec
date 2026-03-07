from datetime import datetime, timedelta
from core.ingestion import sync_new_tracks, sync_playlists, sync_deleted_playlists
from core.database import get_latest_added_at
from session.context import SessionContext, SessionPhase
from core.graph.state import MusicState


class SessionManager:

    def __init__(self, graph, llm, repo, sp, semantic_service, timeout_seconds: int = 60):
        self.graph = graph
        self.llm = llm
        self.repo = repo
        self.sp = sp
        self.context = SessionContext()
        self.semantic_service = semantic_service
        self.timeout = timedelta(seconds=timeout_seconds)
        self.sync_cooldown_seconds = 300  # 5 minutes

    # =====================================================
    # PUBLIC ENTRY
    # =====================================================

    def handle(self, user_input: str) -> MusicState:
        self._maybe_sync()
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

    # =====================================================
    # SYNC CONTROL
    # =====================================================
    def _maybe_sync(self):
        now = datetime.utcnow()

        last_sync_str = self.repo.get_last_sync()

        # First time ever → force sync
        if not last_sync_str:
            self._run_sync(now)
            return

        last_sync = datetime.fromisoformat(last_sync_str)
        elapsed = (now - last_sync).total_seconds()

        if elapsed > self.sync_cooldown_seconds:
            self._run_sync(now)

    def _run_sync(self, now):

        print("Checking for updates...")

        # =============================
        # TRACK SYNC
        # =============================

        new_tracks = sync_new_tracks(
            self.sp,
            self.repo
        )

        new_tracks_count = new_tracks["new_tracks_count"]
        new_tracks_ids = new_tracks["new_tracks_ids"]

        # =============================
        # PLAYLIST SYNC
        # =============================

        playlist_result = sync_playlists(
            self.sp,
            self.repo
        )
        
        deleted_playlists = sync_deleted_playlists(
            self.sp,
            self.repo
        )

        playlist_tracks_synced = playlist_result["playlist_tracks_synced"]
        anchors_updated = playlist_result["anchors_updated"]

        # =============================
        # DATABASE CHANGE CHECK
        # =============================

        if new_tracks_count > 0 or playlist_tracks_synced > 0 or deleted_playlists >0:

            print("Changes detected. Database synchronized.")

            # =============================
            # SEMANTIC LAYER UPDATE
            # =============================

            print("Updating semantic index...")

            # --- Incremental track indexing
            if new_tracks_ids:

                indexed = self.semantic_service.index_tracks(
                    new_tracks_ids
                )

                print(f"Indexed {indexed} new tracks.")

            # --- Anchor recalculation
            for anchor_id in anchors_updated:

                self.semantic_service.recalculate_anchor(
                    anchor_id
                                                        
                )

        else:

            print("No changes detected.")

        # =============================
        # UPDATE SYNC STATE
        # =============================

        self.repo.set_last_sync(now.isoformat())
    

    # =====================================================
    # STATE BUILDING
    # =====================================================

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

    # =====================================================
    # CONTEXT UPDATE
    # =====================================================

    def _update_context(self, state: MusicState):
        intent = state.get("intent")
        result_tracks = state.get("result_tracks")
        strategy = state.get("strategy")
        needs_clarification = state.get("needs_clarification")

        if intent == "unknown":
            self.context.reset()
            return

        if result_tracks and not needs_clarification:
            self.context.last_result_tracks = result_tracks

        if strategy and not needs_clarification:
            self.context.last_strategy = strategy

        created = state.get("created_playlist_name")
        if created:
            self.context.last_playlist_name = created

        deleted = state.get("deleted_playlist")
        if deleted and deleted == self.context.last_playlist_name:
            self.context.last_playlist_name = None

        self.context.last_intent = intent
        self.context.phase = SessionPhase.ACTIVE

    # =====================================================
    # TIMEOUT CONTROL
    # =====================================================

    def _check_timeout(self):
        if datetime.utcnow() - self.context.last_interaction_ts > self.timeout:
            self.context.reset()
    
    
    def _detect_intent(self, user_input: str) -> str:

        text = user_input.lower()

        # BUILD
        if any(word in text for word in [
            "create",
            "build",
            "make",
            "generate",
            "new playlist"
        ]):
            return "build"

        # MODIFY
        if any(word in text for word in [
            "add",
            "remove",
            "delete",
            "rename",
            "update"
        ]):
            return "modify"

        # INFO
        if any(word in text for word in [
            "how many",
            "list",
            "show",
            "do i have"
        ]):
            return "info"

        return "unknown"