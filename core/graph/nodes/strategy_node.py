import json
import re
from core.graph.state import MusicState


def strategy_node(state: MusicState, llm) -> MusicState:
    """
    Generate unified strategy contract using LLM.
    Intent already injected by Session layer.
    """

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
            "action": "add" | "delete_tracks" | "delete_playlist" | "rename" | "adapt",
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
    DELETE RULES (STRICT)
    -------------------------------------------------------
    If action is "delete_tracks":

    - You MUST include in modification.parameters:
        {{
            "delete_all": true | false
        }}

    - Set "delete_all": true ONLY if the user explicitly requests deleting ALL matching tracks
      (examples: "delete all", "remove all", "elimina todas", "borra todos", "every").

    - If delete_all is true:
        - You MUST include at least one valid source describing what should be deleted.
        - The source must reflect the user's request (artist, album, explicit track names, etc.).
        - NEVER leave sources empty when delete_all is true.

    - If delete_all is false:
        - The user MUST explicitly specify exact tracks using track_ids or clear unique song names.
        - Do NOT assume partial deletion by artist or quantity.

    - NEVER assume deletion of all tracks unless clearly stated.
   

    -------------------------------------------------------
    GENERAL RULES
    -------------------------------------------------------

    - The goal MUST match the detected intent: "{intent}".
    - If user provides a playlist name, you MUST use it exactly as written.
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
    - Do NOT use track_ids unless explicitly provided by the user.
    - If the user specifies a number of songs to build or add,
      you MUST set that number in:
      "constraints": {{
          "max_tracks": <number>
      }}

    - Do NOT use filters.limit to represent the requested number of songs.
      filters.limit should only be used when the limit is part of the source definition itself.
      
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

    if strategy and intent in ["build", "modify", "info"]:
        strategy["goal"] = intent

    state["strategy"] = strategy
    state["needs_clarification"] = False
    state["clarification_message"] = None
    state["error"] = None

    return state