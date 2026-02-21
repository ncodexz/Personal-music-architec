from typing import Dict, Any
from core.graph.state import MusicState
from core.graph.validation import (
    validate_strategy,
    validate_composition_result,
)
from core.composition import build_strategic_playlist
from core.playlists import create_playlist, add_tracks_to_playlist


# -------------------------
# STRATEGY NODE
# -------------------------

def strategy_node(state: MusicState, llm) -> MusicState:
    """
    Use the LLM to translate user input into a structured strategy dict.
    """

    user_input = state["user_input"]

    # Simple structured prompt
    prompt = f"""
    Translate the following request into a strategy dictionary with this structure:

    {{
        "subsets": [
            {{
                "type": "artist" or "album",
                "name": string,
                "limit": optional int,
                "top_by": optional string
            }}
        ],
        "priority_order": list of subset types,
        "max_tracks": optional int
    }}

    User request:
    "{user_input}"
    """

    response = llm.invoke(prompt)

    try:
        strategy = eval(response.content)
    except Exception:
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

def composition_node(state: MusicState, conn) -> MusicState:
    """
    Run deterministic playlist composition.
    """

    strategy = state.get("strategy")

    result_tracks = build_strategic_playlist(conn, strategy)

    state["result_tracks"] = result_tracks

    is_valid, message = validate_composition_result(result_tracks)

    if not is_valid:
        state["needs_clarification"] = True
        state["clarification_message"] = message

    return state


# -------------------------
# CONFIRMATION NODE
# -------------------------

def confirmation_node(state: MusicState) -> MusicState:
    """
    Prepare confirmation message.
    """

    tracks = state.get("result_tracks", [])

    message = f"I found {len(tracks)} tracks. Do you want me to create the playlist?"

    state["clarification_message"] = message
    state["needs_clarification"] = True

    return state


# -------------------------
# EXECUTION NODE
# -------------------------

def execution_node(state: MusicState, sp) -> MusicState:
    """
    Create playlist and add tracks.
    """

    tracks = state.get("result_tracks")

    if not tracks:
        state["error"] = "No tracks available for execution."
        return state

    playlist_id = create_playlist(sp, "AI Generated Playlist", public=False)
    add_tracks_to_playlist(sp, playlist_id, tracks)

    state["clarification_message"] = "Playlist created successfully."
    state["needs_clarification"] = False

    return state