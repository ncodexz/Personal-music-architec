from core.playlists import (
    create_playlist,
    add_tracks_to_playlist,
    remove_tracks_from_playlist,
    update_playlist_details,
    get_playlist_id_by_name,
)


def execute_build(state, sp):
    strategy = state.get("strategy")
    tracks = state.get("result_tracks")

    if not tracks:
        state["error"] = "No tracks available for playlist creation."
        state["needs_clarification"] = False
        return state

    target = strategy.get("target", {})
    playlist_name = target.get("identifier") or "AI Generated Playlist"

    playlist_id = create_playlist(sp, playlist_name, public=False)
    add_tracks_to_playlist(sp, playlist_id, tracks)

    state["clarification_message"] = (
        f"Playlist '{playlist_name}' created successfully."
    )

    state["created_playlist_name"] = playlist_name
    state["needs_clarification"] = False
    state["error"] = None

    return state


def execute_modify(state, sp):
    strategy = state.get("strategy")
    modification = strategy.get("modification", {})
    action = modification.get("action")
    target = strategy.get("target", {})
    playlist_name = target.get("identifier")

    if not playlist_name:
        state["error"] = "Playlist name is required for modification."
        state["needs_clarification"] = False
        return state

    playlist_id = get_playlist_id_by_name(sp, playlist_name)

    if not playlist_id:
        state["error"] = f"Playlist '{playlist_name}' not found."
        state["needs_clarification"] = False
        return state

    if action == "add":

        tracks = state.get("result_tracks", [])

        if not tracks:
            state["error"] = "No tracks available to add."
            state["needs_clarification"] = False
            return state

        add_tracks_to_playlist(sp, playlist_id, tracks)

        state["clarification_message"] = (
            f"{len(tracks)} tracks added to '{playlist_name}'."
        )
        state["created_playlist_name"] = playlist_name
        state["needs_clarification"] = False
        state["error"] = None
        return state

    if action == "delete_tracks":

        tracks = state.get("result_tracks", [])

        if not tracks:
            state["error"] = "No tracks available to delete."
            state["needs_clarification"] = False
            return state

        remove_tracks_from_playlist(sp, playlist_id, tracks)

        state["clarification_message"] = (
            f"{len(tracks)} tracks removed from '{playlist_name}'."
        )
        state["created_playlist_name"] = playlist_name
        state["needs_clarification"] = False
        state["error"] = None
        return state

    if action == "delete_playlist":

        sp.current_user_unfollow_playlist(playlist_id)

        state["clarification_message"] = (
            f"Playlist '{playlist_name}' deleted successfully."
        )
        state["created_playlist_name"] = None
        state["needs_clarification"] = False
        state["error"] = None
        return state

    if action == "rename":

        new_name = modification.get("parameters", {}).get("new_name")

        if not new_name:
            state["error"] = "New name not provided."
            state["needs_clarification"] = False
            return state

        update_playlist_details(sp, playlist_id, name=new_name)

        state["clarification_message"] = (
            f"Playlist renamed to '{new_name}'."
        )
        state["created_playlist_name"] = new_name
        state["needs_clarification"] = False
        state["error"] = None
        return state

    state["error"] = "Unsupported modification action."
    state["needs_clarification"] = False
    return state