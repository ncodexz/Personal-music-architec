from typing import Tuple, Optional


def validate_strategy(strategy: Optional[dict]) -> Tuple[bool, Optional[str]]:
    """
    Validate the generated strategy structure for unified contract.
    Returns:
        (is_valid, clarification_message)
    """

    if strategy is None:
        return False, "I could not understand your request. Could you clarify what you would like to do?"

    goal = strategy.get("goal")

    if goal not in ["build", "modify", "info"]:
        return False, "Invalid goal. Please specify a valid action."

    # =====================================================
    # INFO VALIDATION
    # =====================================================

    if goal == "info":

        info_type = strategy.get("info_type")

        if not info_type:
            return False, "Please specify what information you would like."

        return True, None

    target = strategy.get("target", {})
    sources = strategy.get("sources", [])
    modification = strategy.get("modification")
    constraints = strategy.get("constraints", {})

    # =====================================================
    # BUILD VALIDATION
    # =====================================================

    if goal == "build":

        if not isinstance(sources, list) or len(sources) == 0:
            return False, "To build a playlist, I need at least one source."

        for source in sources:
            source_type = source.get("type")

            if source_type not in [
                "artist",
                "album",
                "top_played",
                "recently_added",
                "explicit",
            ]:
                return False, f"Unsupported source type '{source_type}'."

        return True, None

    # =====================================================
    # MODIFY VALIDATION
    # =====================================================

    if goal == "modify":

        identifier = target.get("identifier")
        if not identifier or not isinstance(identifier, str):
            return False, "To modify a playlist, I need a valid playlist name."

        if not modification or not isinstance(modification, dict):
            return False, "Please specify what modification you would like to perform."

        action = modification.get("action")

        if action not in ["add", "delete_tracks", "delete_playlist", "rename", "adapt"]:
            return False, "Unsupported modification action."

        # -------------------------------------------------
        # STRICT DELETE VALIDATION
        # -------------------------------------------------

        if action == "delete_tracks":

            parameters = modification.get("parameters", {})
            delete_all = parameters.get("delete_all")

            if delete_all is None:
                return False, "Delete operation must explicitly specify whether all matching tracks should be removed."

            # Case 1: delete_all == True → must have at least one source
            if delete_all is True:
                if not isinstance(sources, list) or len(sources) == 0:
                    return False, "To delete all matching tracks, a valid source must be specified."
                return True, None

            # Case 2: delete_all == False → must have explicit track_ids
            if delete_all is False:

                if not isinstance(sources, list) or len(sources) == 0:
                    return False, "You must specify exact tracks to delete."

                has_explicit_tracks = False

                for source in sources:
                    filters = source.get("filters", {})
                    track_ids = filters.get("track_ids")

                    if isinstance(track_ids, list) and len(track_ids) > 0:
                        has_explicit_tracks = True
                        break

                if not has_explicit_tracks:
                    return False, "To delete specific tracks, you must explicitly specify the exact songs."

                return True, None

        return True, None

    return False, "Invalid strategy structure."