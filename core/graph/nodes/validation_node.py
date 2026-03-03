from core.graph.state import MusicState
from core.graph.validation import validate_strategy


def validation_node(state: MusicState) -> MusicState:
    """
    Inject conversational memory first, then validate structure.
    """

    strategy = state.get("strategy")
    print("DEBUG last_strategy in validation:", state.get("last_strategy"))
    if not strategy:
        state["needs_clarification"] = True
        state["clarification_message"] = "Invalid strategy."
        return state

    goal = strategy.get("goal")

    # -------------------------------------------------
    # PLAYLIST MEMORY INJECTION
    # -------------------------------------------------

    if goal == "modify":
        target = strategy.get("target", {})
        identifier = target.get("identifier")

        if not identifier and state.get("last_playlist_name"):
            strategy["target"]["identifier"] = state["last_playlist_name"]

    # -------------------------------------------------
    # SOURCE INHERITANCE FOR ADD
    # -------------------------------------------------

    if goal == "modify":
        modification = strategy.get("modification", {})
        action = modification.get("action")

        if action == "add":

            sources = strategy.get("sources", [])

            # If user did not specify sources explicitly
            if not sources:

                last_strategy = state.get("last_strategy")

                if not last_strategy:
                    state["needs_clarification"] = True
                    state["clarification_message"] = (
                        "Please specify which songs or artist you would like to add."
                    )
                    return state

                last_goal = last_strategy.get("goal")

                # -----------------------------------------
                # Case 1: last strategy had explicit sources
                # -----------------------------------------

                if last_goal in ["build", "modify"]:
                    last_sources = last_strategy.get("sources", [])

                    if isinstance(last_sources, list) and len(last_sources) == 1:

                        inherited_source = last_sources[0].copy()
                        inherited_filters = inherited_source.get("filters", {}).copy()

                        # Reset limit to avoid inheriting previous quantity
                        inherited_filters["limit"] = None
                        inherited_source["filters"] = inherited_filters

                        strategy["sources"] = [inherited_source]

                    else:
                        state["needs_clarification"] = True
                        state["clarification_message"] = (
                            "Please specify which songs or artist you would like to add."
                        )
                        return state

                # -----------------------------------------
                # Case 2: last strategy was info about artist
                # -----------------------------------------

                elif last_goal == "info":

                    info_type = last_strategy.get("info_type")
                    parameters = last_strategy.get("parameters", {}) or {}

                    if info_type == "artist_in_library":
                        artist_name = parameters.get("artist_name")

                        if artist_name:
                            strategy["sources"] = [{
                                "type": "artist",
                                "filters": {
                                    "name": artist_name,
                                    "limit": None,
                                    "timeframe": None,
                                    "track_ids": None
                                }
                            }]
                        else:
                            state["needs_clarification"] = True
                            state["clarification_message"] = (
                                "Please specify which songs or artist you would like to add."
                            )
                            return state
                    else:
                        state["needs_clarification"] = True
                        state["clarification_message"] = (
                            "Please specify which songs or artist you would like to add."
                        )
                        return state

                else:
                    state["needs_clarification"] = True
                    state["clarification_message"] = (
                        "Please specify which songs or artist you would like to add."
                    )
                    return state
    # -------------------------------------------------
    # ENSURE PLAYLIST EXISTS FOR MODIFY
    # -------------------------------------------------

    if goal == "modify":
        target = strategy.get("target", {})
        identifier = target.get("identifier")

        if not identifier:
            state["needs_clarification"] = True
            state["clarification_message"] = (
                "Please specify which playlist you would like to modify."
            )
            return state
        
    # -------------------------------------------------
    # FINAL STRUCTURAL VALIDATION
    # -------------------------------------------------

    is_valid, message = validate_strategy(strategy)

    if not is_valid:
        state["needs_clarification"] = True
        state["clarification_message"] = message
        return state

    return state