from typing import TypedDict, Optional, List


class MusicState(TypedDict):
    """
    Shared state object that travels through the LangGraph workflow.
    """

    # Original user request
    user_input: str

    # Validated strategy dictionary
    strategy: Optional[dict]

    # Resulting track IDs after deterministic composition
    result_tracks: Optional[List[str]]

    # Error message if something fails
    error: Optional[str]

    # Whether clarification is required
    needs_clarification: bool

    # Clarification message to return to the user
    clarification_message: Optional[str]

    # Whether the user confirmed execution
    confirmed: bool
    
    # Classified intent
    intent: str