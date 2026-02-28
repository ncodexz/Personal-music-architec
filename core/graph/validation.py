from typing import Tuple, Optional


def validate_strategy(strategy: Optional[dict]) -> Tuple[bool, Optional[str]]:
    """
    Validate the generated strategy structure for Fase 2 unified contract.

    Returns:
        (is_valid, clarification_message)
    """

    if strategy is None:
        return False, "I could not understand your request. Could you clarify what you would like to do?"

    goal = strategy.get("goal")

    if goal not in ["build", "modify"]:
        return False, "Invalid goal. Please specify a valid action."

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
                "explicit",  # NEW
            ]:
                return False, f"Unsupported source type '{source_type}'."

            filters = source.get("filters", {}) or {}

            # -------------------------
            # EXPLICIT VALIDATION
            # -------------------------
            if source_type == "explicit":
                track_ids = filters.get("track_ids")
                if not isinstance(track_ids, list) or len(track_ids) == 0:
                    return False, "Explicit source requires a non-empty list of track_ids."

            # -------------------------
            # LIMIT VALIDATION
            # -------------------------
            limit = filters.get("limit")
            if limit is not None:
                if not isinstance(limit, int) or limit <= 0:
                    return False, "Source limit must be a positive integer."

        max_tracks = constraints.get("max_tracks")
        if max_tracks is not None:
            if not isinstance(max_tracks, int) or max_tracks <= 0:
                return False, "The maximum number of tracks must be a positive integer."

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

        if action not in ["add", "delete", "rename", "adapt"]:
            return False, "Unsupported modification action."

        # If action requires sources
        if action in ["add", "delete"]:
            if not isinstance(sources, list) or len(sources) == 0:
                return False, f"To {action} tracks, I need at least one source."

        # Rename validation
        if action == "rename":
            parameters = modification.get("parameters", {})
            new_name = parameters.get("new_name")
            if not new_name or not isinstance(new_name, str):
                return False, "Please provide a valid new name for the playlist."

        return True, None

    return False, "Invalid strategy structure."