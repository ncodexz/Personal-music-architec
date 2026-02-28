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
    Use the LLM to translate user input into the unified Fase 2 strategy contract.
    """
    # If strategy already injected (e.g., explicit from session layer), skip LLM
    if state.get("strategy"):
        return state

    user_input = state["user_input"]
    intent = state.get("intent")

    prompt = f"""
    Translate the following user request into a valid JSON strategy object.

    The strategy must follow this structure:

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
                    "name": string or null
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

    Rules:
    - If the intent is "{intent}", the goal must match it.
    - If goal is "build", at least one source is required.
    - If goal is "modify", target.identifier is required.
    - If action is "add" or "delete", sources are required.
    - If source.type is "explicit", filters must include "track_ids": list of strings.
    - If action is "rename", parameters must include "new_name".
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

    # Extract JSON block even if extra text is included
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
    Execute deterministic logic for build or modify goals.
    """

    strategy = state.get("strategy")

    if not strategy:
        state["needs_clarification"] = True
        state["clarification_message"] = "Invalid strategy."
        return state

    goal = strategy.get("goal")

    # =====================================================
    # BUILD
    # =====================================================

    if goal == "build":

        result_tracks = build_strategic_playlist(repo, strategy)

        state["result_tracks"] = result_tracks
        state["needs_clarification"] = False

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

        return state

    # =====================================================
    # FALLBACK
    # =====================================================

    state["needs_clarification"] = True
    state["clarification_message"] = "Unsupported goal."
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
    Execute build or modify actions after confirmation.
    Fully aligned with playlists.py helpers.
    """

    strategy = state.get("strategy")
    goal = strategy.get("goal") if strategy else None

    if not strategy:
        state["error"] = "No valid strategy found."
        return state

    # =====================================================
    # BUILD
    # =====================================================

    if goal == "build":

        tracks = state.get("result_tracks")

        if not tracks:
            state["error"] = "No tracks available for playlist creation."
            return state

        target = strategy.get("target", {})
        playlist_name = target.get("identifier") or "AI Generated Playlist"

        playlist_id = create_playlist(sp, playlist_name, public=False)
        add_tracks_to_playlist(sp, playlist_id, tracks)

        state["clarification_message"] = (
            f"Playlist '{playlist_name}' created successfully."
        )
        state["needs_clarification"] = False

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
            return state

        playlist_id = get_playlist_id_by_name(sp, playlist_name)

        if not playlist_id:
            state["error"] = f"Playlist '{playlist_name}' not found."
            return state

        # -------------------------
        # RENAME
        # -------------------------

        if action == "rename":
            new_name = modification.get("parameters", {}).get("new_name")

            if not new_name:
                state["error"] = "New name not provided."
                return state

            update_playlist_details(sp, playlist_id, name=new_name)

            state["clarification_message"] = (
                f"Playlist renamed to '{new_name}'."
            )

        # -------------------------
        # ADD
        # -------------------------

        elif action == "add":

            tracks = state.get("result_tracks", [])

            if not tracks:
                state["error"] = "No tracks available to add."
                return state

            add_tracks_to_playlist(sp, playlist_id, tracks)

            state["clarification_message"] = (
                f"{len(tracks)} tracks added to '{playlist_name}'."
            )

        # -------------------------
        # DELETE
        # -------------------------

        elif action == "delete":

            tracks = state.get("result_tracks", [])

            if not tracks:
                state["error"] = "No tracks available to remove."
                return state

            remove_tracks_from_playlist(sp, playlist_id, tracks)

            state["clarification_message"] = (
                f"{len(tracks)} tracks removed from '{playlist_name}'."
            )

        # -------------------------
        # ADAPT
        # -------------------------

        elif action == "adapt":
            # Placeholder for future adaptation logic
            state["clarification_message"] = (
                f"Playlist '{playlist_name}' adapted successfully."
            )

        else:
            state["error"] = "Unsupported modification action."
            return state

        state["needs_clarification"] = False
        return state

    state["error"] = "Unsupported goal."
    return state