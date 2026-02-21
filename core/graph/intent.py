from core.graph.state import MusicState


def intent_node(state: MusicState, llm) -> MusicState:
    """
    Classify user intent into:
    - build
    - info
    - unknown
    """

    user_input = state["user_input"]

    prompt = f"""
    Classify the following user request into one of these categories:

    - "build" → if the user wants to create, modify, or generate a playlist.
    - "info" → if the user is asking for information about their music library.
    - "unknown" → if it does not fit clearly.

    Only return one word: build, info, or unknown.

    User request:
    "{user_input}"
    """

    response = llm.invoke(prompt)
    intent = response.content.strip().lower()

    if intent not in ["build", "info"]:
        intent = "unknown"

    state["intent"] = intent

    return state