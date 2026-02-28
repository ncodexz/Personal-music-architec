from core.graph.state import MusicState


def info_query_node(state: MusicState, repo) -> MusicState:

    user_input = state["user_input"].lower()

    # =====================================================
    # ARTIST QUERY
    # =====================================================

    if (
        "song by" in user_input
        or "songs by" in user_input
        or "music from" in user_input
        or "tracks by" in user_input
        or "canciones de" in user_input
        or "musica de" in user_input
    ):
        clean_input = user_input.replace("?", "").replace("¿", "")
        words = clean_input.split()
        artist_name = words[-1]

        track_ids = repo.get_tracks_by_artist(artist_name)
        count = len(track_ids)

        if count > 0:
            state["clarification_message"] = (
                f"Yes, you have {count} tracks by {artist_name.title()}."
            )
            state["result_tracks"] = track_ids
        else:
            state["clarification_message"] = (
                f"No, you do not have any tracks by {artist_name.title()}."
            )
            state["result_tracks"] = []

        return state

    # =====================================================
    # MOST PLAYED TRACK
    # =====================================================

    if "most played" in user_input or "más escuchada" in user_input:
        row = repo.get_most_played_track()

        if not row:
            state["clarification_message"] = (
                "You do not have enough listening data yet."
            )
            state["result_tracks"] = []
            return state

        track_id = row[0]
        track_name = repo.get_track_name(track_id)

        state["clarification_message"] = (
            f"Your most played track is '{track_name}'."
        )
        state["result_tracks"] = [track_id]

        return state

    # =====================================================
    # RECENT TRACKS ADDED TO LIBRARY
    # =====================================================

    if "recent" in user_input or "recientemente" in user_input:
        track_ids = repo.get_recent_tracks(limit=5)

        if not track_ids:
            state["clarification_message"] = (
                "You have not added any tracks recently."
            )
            state["result_tracks"] = []
            return state

        track_names = [repo.get_track_name(tid) for tid in track_ids]

        state["clarification_message"] = (
            f"Recently added tracks: {', '.join(track_names)}."
        )
        state["result_tracks"] = track_ids

        return state

    # =====================================================
    # FALLBACK
    # =====================================================

    state["clarification_message"] = (
        "I am not able to answer that informational request yet."
    )
    state["result_tracks"] = []

    return state