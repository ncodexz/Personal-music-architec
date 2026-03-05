from core.graph.state import MusicState
from core.graph.validation import validate_strategy


def validation_node(state: MusicState) -> MusicState:
    """
    Inject conversational memory first, then validate structure.
    """

    strategy = state.get("strategy")

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
    # RENAME FIX (LLM misinterpretation correction)
    # -------------------------------------------------

    if goal == "modify":
        modification = strategy.get("modification", {})
        action = modification.get("action")

        if action == "rename":
            target = strategy.get("target", {})
            identifier = target.get("identifier")
            new_name = modification.get("parameters", {}).get("new_name")

            if (
                identifier
                and new_name
                and identifier == new_name
                and state.get("last_playlist_name")
            ):
                strategy["target"]["identifier"] = state["last_playlist_name"]

    # -------------------------------------------------
    # SOURCE INHERITANCE FOR ADD
    # -------------------------------------------------

    if goal == "modify":
        modification = strategy.get("modification", {})
        action = modification.get("action")

        if action == "add":

            sources = strategy.get("sources", [])

            if not sources:

                last_strategy = state.get("last_strategy")

                if not last_strategy:
                    state["needs_clarification"] = True
                    state["clarification_message"] = (
                        "Please specify which songs or artist you would like to add."
                    )
                    return state

                last_goal = last_strategy.get("goal")

                # Case 1: inherit from build/modify with single source
                if last_goal in ["build", "modify"]:
                    last_sources = (last_strategy or {}).get("sources", [])

                    if (
                        isinstance(last_sources, list)
                        and len(last_sources) == 1
                        and last_sources[0].get("type") in ["artist", "album", "semantic_anchor"]
                    ):

                        inherited_source = last_sources[0].copy()
                        inherited_filters = inherited_source.get("filters", {}).copy()

                        inherited_filters["limit"] = None
                        inherited_source["filters"] = inherited_filters

                        strategy["sources"] = [inherited_source]

                    else:
                        state["needs_clarification"] = True
                        state["clarification_message"] = (
                            "Please specify which songs or artist you would like to add."
                        )
                        
                        return state

                # Case 2: inherit from info about artist
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
    # STRICT DELETE LOGIC
    # -------------------------------------------------

    if goal == "modify":
        modification = strategy.get("modification", {})
        action = modification.get("action")

        if action == "delete_tracks":

            parameters = modification.get("parameters", {}) or {}
            delete_all = parameters.get("delete_all", False)
            sources = strategy.get("sources", [])

            if delete_all and not sources:
                state["needs_clarification"] = True
                state["clarification_message"] = (
                    "To delete all matching tracks, a valid source must be specified."
                )
                return state

            if not delete_all and not sources:
                state["needs_clarification"] = True
                state["clarification_message"] = (
                    "To delete specific tracks, you must explicitly specify the exact songs."
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