from core.graph.state import MusicState
from core.composition import build_strategic_playlist


def composition_node(state: MusicState, repo, semantic_service) -> MusicState:
    """
    Deterministic resolution of tracks.
    """

    strategy = state.get("strategy")

    if not strategy:
        state["needs_clarification"] = True
        state["clarification_message"] = "Invalid strategy."
        state["error"] = None
        return state

    goal = strategy.get("goal")

    # -----------------------------------------------------
    # INFO
    # -----------------------------------------------------

    if goal == "info":

        info_type = strategy.get("info_type")
        parameters = strategy.get("parameters", {}) or {}

        if info_type == "list_playlists":
            names = repo.get_all_playlists()

            if not names:
                message = "You do not have any playlists."
            else:
                message = "Your playlists are:\n- " + "\n- ".join(names)

            state["clarification_message"] = message
            state["needs_clarification"] = False
            return state

        if info_type == "count_playlists":
            count = repo.count_playlists()
            state["clarification_message"] = f"You have {count} playlists."
            state["needs_clarification"] = False
            return state
        
        if info_type == "count_tracks":

            count = repo.count_tracks()

            state["clarification_message"] = (
                f"You have {count} songs in your library."
            )

            state["needs_clarification"] = False
            return state

        if info_type == "artist_in_library":
            artist_name = parameters.get("artist_name")

            if not artist_name:
                state["needs_clarification"] = True
                state["clarification_message"] = "Please specify an artist name."
                return state

            track_ids = repo.get_tracks_by_artist(artist_name)
            count = len(track_ids)

            if count == 0:
                message = f"You do not have any songs by {artist_name}."
            else:
                message = f"You have {count} songs by {artist_name}."

            state["clarification_message"] = message
            state["needs_clarification"] = False
            return state

        state["needs_clarification"] = True
        state["clarification_message"] = "Unsupported informational request."
        return state

    # -----------------------------------------------------
    # BUILD
    # -----------------------------------------------------

    if goal == "build":

        result_tracks = build_strategic_playlist(repo, semantic_service, strategy)

        state["result_tracks"] = result_tracks
        state["needs_clarification"] = False
        state["error"] = None
        return state

    # -----------------------------------------------------
    # MODIFY
    # -----------------------------------------------------

    if goal == "modify":

        modification = strategy.get("modification", {})
        action = modification.get("action")

        if action in ["add", "delete_tracks"]:
            result_tracks = build_strategic_playlist(repo, semantic_service, strategy)
            state["result_tracks"] = result_tracks
        else:
            state["result_tracks"] = None

        state["needs_clarification"] = False
        state["error"] = None
        return state

    # -----------------------------------------------------
    # FALLBACK
    # -----------------------------------------------------

    state["needs_clarification"] = True
    state["clarification_message"] = "Unsupported goal."
    state["error"] = None
    return state