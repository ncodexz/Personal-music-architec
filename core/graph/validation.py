from typing import Tuple, Optional


def validate_strategy(strategy: Optional[dict]) -> Tuple[bool, Optional[str]]:
    """
    Validate the generated strategy structure.

    Returns:
        (is_valid, clarification_message)
    """

    if strategy is None:
        return False, "I could not understand your request. Could you clarify what you would like to build?"

    subsets = strategy.get("subsets", [])

    if not subsets:
        return False, "I need at least one artist or album to build a playlist."

    for subset in subsets:
        subset_type = subset.get("type")
        name = subset.get("name")

        if subset_type not in ["artist", "album"]:
            return False, f"Unsupported subset type '{subset_type}'. Please use an artist or album."

        if not name or not isinstance(name, str):
            return False, "Each subset must include a valid name."

    max_tracks = strategy.get("max_tracks")

    if max_tracks is not None:
        if not isinstance(max_tracks, int) or max_tracks <= 0:
            return False, "The maximum number of tracks must be a positive integer."

    return True, None


def validate_composition_result(result_tracks: Optional[list]) -> Tuple[bool, Optional[str]]:
    """
    Validate the result of deterministic composition.
    """

    if not result_tracks:
        return False, "I could not find tracks matching your request. Would you like to adjust the criteria?"

    return True, None