from core.graph.state import MusicState


def intent_node(state: MusicState, llm) -> MusicState:
    """
    Classifies user request into macro-intents:
    build | modify | info | unknown
    """

    # -----------------------------------------------------
    # BYPASS: If intent already injected (e.g., confirmation flow)
    # -----------------------------------------------------
    if state.get("intent"):
        return state

    user_input = state["user_input"]

    prompt = f"""
    Classify the following user request into EXACTLY one of these categories:

    - "build"   → Creating a new playlist from scratch.
    - "modify"  → Adding, deleting, renaming, or adapting an existing playlist.
    - "info"    → Asking for information or statistics.
    - "unknown" → If unclear.

    Only return the word.

    User request:
    "{user_input}"
    """

    response = llm.invoke(prompt)
    intent = response.content.strip().lower()

    valid_intents = ["build", "modify", "info"]

    if intent not in valid_intents:
        intent = "unknown"

    state["intent"] = intent

    return state