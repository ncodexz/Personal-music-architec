from typing import Dict
import json
import re
from core.graph.state import MusicState
from core.graph.validation import validate_strategy
from core.composition import build_strategic_playlist

from core.playlists import (
    create_playlist,
    add_tracks_to_playlist,
    remove_tracks_from_playlist,
    update_playlist_details,
    get_playlist_id_by_name,
)


# -------------------------
# STRATEGY NODE
# -------------------------

def strategy_node(state: MusicState, llm) -> MusicState:
    """
    Use the LLM to translate user input into the unified strategy contract.
    """

    # If strategy already injected (e.g., explicit from session layer), skip LLM
    if state.get("strategy"):
        return state

    user_input = state["user_input"]
    intent = state.get("intent")

    prompt = f"""
    Translate the following user request into a valid JSON strategy object.

    The strategy must follow ONE of these structures:

    -------------------------------------------------------
    BUILD OR MODIFY STRUCTURE
    -------------------------------------------------------

    {{
        "goal": "build" | "modify",

        "target": {{
            "type": "playlist",
            "identifier": string or null
        }},

        "sources": [
            {{
                "type": "artist" | "album" | "top_played" | "recently_added" | "explicit",
                "filters": {{
                    "timeframe": string or null,
                    "limit": int or null,
                    "name": string or null,
                    "track_ids": list or null
                }}
            }}
        ],

        "modification": {{
            "action": "add" | "delete" | "rename" | "adapt",
            "parameters": dict
        }},

        "constraints": {{
            "max_tracks": int or null,
            "deduplicate": true or false,
            "merge_strategy": "balanced" | "priority" or null
        }}
    }}

    -------------------------------------------------------
    INFO STRUCTURE
    -------------------------------------------------------

    {{
        "goal": "info",
        "info_type": "list_playlists" | "count_playlists" | "artist_in_playlists" | "artist_in_library",
        "parameters": {{
            "artist_name": string or null,
            "timeframe": string or null
        }}
    }}

    -------------------------------------------------------
    RULES
    -------------------------------------------------------

    - The goal MUST match the detected intent: "{intent}".
    - If user provides a playlist name, you MUST use it in target.identifier exactly as written.
    - Never invent playlist names.
    - Never generate default names.
    - If goal is "build", at least one source is required.
    - If goal is "modify", target.identifier is required.
    - If goal is "info", info_type is required.
    - Use null where values are not provided.
    - Always return valid JSON.
    - Do NOT include explanations.
    - Do NOT wrap in markdown.
    - Return only JSON.

    User request:
    "{user_input}"
    """

    response = llm.invoke(prompt)
    raw_output = response.content.strip()

    json_match = re.search(r"\{.*\}", raw_output, re.DOTALL)

    if json_match:
        json_str = json_match.group(0)
        try:
            strategy = json.loads(json_str)
        except json.JSONDecodeError:
            strategy = None
    else:
        strategy = None

    state["strategy"] = strategy
    state["needs_clarification"] = False
    state["clarification_message"] = None
    state["error"] = None

    return state


# -------------------------
# VALIDATION NODE
# -------------------------

def validation_node(state: MusicState) -> MusicState:
    """
    Validate strategy structure.
    """

    is_valid, message = validate_strategy(state.get("strategy"))

    if not is_valid:
        state["needs_clarification"] = True
        state["clarification_message"] = message
        return state

    return state


# -------------------------
# COMPOSITION NODE
# -------------------------

def composition_node(state: MusicState, repo) -> MusicState:
    """
    Execute deterministic logic for build, modify or info goals.
    """

    strategy = state.get("strategy")

    if not strategy:
        state["needs_clarification"] = True
        state["clarification_message"] = "Invalid strategy."
        state["error"] = None
        return state

    goal = strategy.get("goal")

    # =====================================================
    # INFO
    # =====================================================

    if goal == "info":

        info_type = strategy.get("info_type")
        parameters = strategy.get("parameters", {}) or {}

        # -------------------------
        # LIST PLAYLISTS
        # -------------------------
        if info_type == "list_playlists":

            names = repo.get_all_playlists()

            if not names:
                message = "You do not have any playlists."
            else:
                message = "Your playlists are:\n- " + "\n- ".join(names)

            state["clarification_message"] = message
            state["needs_clarification"] = False
            return state

        # -------------------------
        # COUNT PLAYLISTS
        # -------------------------
        if info_type == "count_playlists":

            count = repo.count_playlists()

            state["clarification_message"] = (
                f"You have {count} playlists."
            )
            state["needs_clarification"] = False
            return state

        # -------------------------
        # ARTIST IN LIBRARY
        # -------------------------
        if info_type == "artist_in_library":

            artist_name = parameters.get("artist_name")

            if not artist_name:
                state["needs_clarification"] = True
                state["clarification_message"] = "Please specify the artist name."
                return state

            count = repo.count_tracks_by_artist(artist_name)

            if count == 0:
                message = f"You do not have any tracks by {artist_name} in your library."
            else:
                message = f"You have {count} tracks by {artist_name} in your library."

            state["clarification_message"] = message
            state["needs_clarification"] = False
            return state

        # -------------------------
        # ARTIST IN PLAYLISTS
        # -------------------------
        if info_type == "artist_in_playlists":

            artist_name = parameters.get("artist_name")

            if not artist_name:
                state["needs_clarification"] = True
                state["clarification_message"] = "Please specify the artist name."
                return state

            count = repo.count_artist_tracks_in_playlists(artist_name)

            if count == 0:
                message = f"You do not have any tracks by {artist_name} in your playlists."
            else:
                message = f"You have {count} tracks by {artist_name} across your playlists."

            state["clarification_message"] = message
            state["needs_clarification"] = False
            return state

        state["needs_clarification"] = True
        state["clarification_message"] = "Unsupported informational request."
        return state

    # =====================================================
    # BUILD
    # =====================================================

    if goal == "build":

        result_tracks = build_strategic_playlist(repo, strategy)

        state["result_tracks"] = result_tracks
        state["needs_clarification"] = False
        state["error"] = None
        return state

    # =====================================================
    # MODIFY
    # =====================================================

    if goal == "modify":

        modification = strategy.get("modification", {})
        action = modification.get("action")

        if action in ["add", "delete"]:
            result_tracks = build_strategic_playlist(repo, strategy)
            state["result_tracks"] = result_tracks
        else:
            state["result_tracks"] = None

        state["needs_clarification"] = False
        state["error"] = None
        return state

    # =====================================================
    # FALLBACK
    # =====================================================

    state["needs_clarification"] = True
    state["clarification_message"] = "Unsupported goal."
    state["error"] = None
    return state

# -------------------------
# CONFIRMATION NODE
# -------------------------

def confirmation_node(state: MusicState) -> MusicState:
    """
    Prepare confirmation message depending on goal.
    """

    # -----------------------------------------------------
    # BYPASS: If already confirmed, skip confirmation step
    # -----------------------------------------------------
    if state.get("confirmed"):
        state["needs_clarification"] = False
        return state

    strategy = state.get("strategy")
    goal = strategy.get("goal") if strategy else None

    if goal == "build":
        tracks = state.get("result_tracks", [])
        target = strategy.get("target", {})
        name = target.get("identifier") or "AI Generated Playlist"

        message = (
            f"I found {len(tracks)} tracks. "
            f"Do you want me to create the playlist '{name}'?"
        )

        state["clarification_message"] = message
        state["needs_clarification"] = True
        return state

    if goal == "modify":
        modification = strategy.get("modification", {})
        action = modification.get("action")
        target = strategy.get("target", {})
        name = target.get("identifier")

        if action == "rename":
            new_name = modification.get("parameters", {}).get("new_name")
            message = f"Do you want me to rename the playlist '{name}' to '{new_name}'?"

        elif action == "add":
            tracks = state.get("result_tracks", [])
            message = (
                f"I found {len(tracks)} tracks to add to '{name}'. "
                "Do you want me to proceed?"
            )

        elif action == "delete":
            tracks = state.get("result_tracks", [])
            message = (
                f"I found {len(tracks)} tracks to remove from '{name}'. "
                "Do you want me to proceed?"
            )

        elif action == "adapt":
            message = f"Do you want me to adapt the playlist '{name}' as requested?"

        else:
            message = "Do you want me to proceed with the modification?"

        state["clarification_message"] = message
        state["needs_clarification"] = True
        return state

    state["clarification_message"] = "Do you want me to proceed?"
    state["needs_clarification"] = True

    return state
# -------------------------
# EXECUTION NODE
# -------------------------

from core.playlists import (
    create_playlist,
    add_tracks_to_playlist,
    remove_tracks_from_playlist,
    update_playlist_details,
    get_playlist_id_by_name,
)


def execution_node(state: MusicState, sp) -> MusicState:
    """
    Execute build or modify actions.
    Execution is direct when strategy is valid and clear.
    """

    strategy = state.get("strategy")
    goal = strategy.get("goal") if strategy else None

    if not strategy:
        state["error"] = "No valid strategy found."
        state["needs_clarification"] = False
        return state

    # =====================================================
    # BUILD
    # =====================================================

    if goal == "build":

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
        state["needs_clarification"] = False
        state["error"] = None
        return state

    # =====================================================
    # MODIFY
    # =====================================================

    if goal == "modify":

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

        # -------------------------
        # RENAME
        # -------------------------

        if action == "rename":
            new_name = modification.get("parameters", {}).get("new_name")

            if not new_name:
                state["error"] = "New name not provided."
                state["needs_clarification"] = False
                return state

            if new_name == playlist_name:
                state["clarification_message"] = "The playlist already has that name."
                state["needs_clarification"] = False
                state["error"] = None
                return state

            update_playlist_details(sp, playlist_id, name=new_name)

            state["clarification_message"] = (
                f"Playlist renamed to '{new_name}'."
            )
            state["needs_clarification"] = False
            state["error"] = None
            return state

        # -------------------------
        # ADD
        # -------------------------

        elif action == "add":

            tracks = state.get("result_tracks", [])

            if not tracks:
                state["error"] = "No tracks available to add."
                state["needs_clarification"] = False
                return state

            add_tracks_to_playlist(sp, playlist_id, tracks)

            state["clarification_message"] = (
                f"{len(tracks)} tracks added to '{playlist_name}'."
            )
            state["needs_clarification"] = False
            state["error"] = None
            return state

        # -------------------------
        # DELETE
        # -------------------------

        elif action == "delete":

            tracks = state.get("result_tracks", [])

            if not tracks:
                state["error"] = "No tracks available to remove."
                state["needs_clarification"] = False
                return state

            remove_tracks_from_playlist(sp, playlist_id, tracks)

            state["clarification_message"] = (
                f"{len(tracks)} tracks removed from '{playlist_name}'."
            )
            state["needs_clarification"] = False
            state["error"] = None
            return state

        # -------------------------
        # ADAPT
        # -------------------------

        elif action == "adapt":

            state["clarification_message"] = (
                f"Playlist '{playlist_name}' adapted successfully."
            )
            state["needs_clarification"] = False
            state["error"] = None
            return state

        else:
            state["error"] = "Unsupported modification action."
            state["needs_clarification"] = False
            return state

    state["error"] = "Unsupported goal."
    state["needs_clarification"] = False
    return state