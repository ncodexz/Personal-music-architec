from typing import List, Dict


def build_strategic_playlist(repo, strategy: Dict) -> List[str]:
    """
    Deterministic playlist builder for Fase 2 unified strategy contract.
    Compatible with current Repository implementation.
    """

    goal = strategy.get("goal")
    sources = strategy.get("sources", [])
    constraints = strategy.get("constraints", {})

    all_tracks: List[str] = []

    # =====================================================
    # RESOLVE SOURCES
    # =====================================================

    for source in sources:

        source_type = source.get("type")
        filters = source.get("filters", {}) or {}

        limit = filters.get("limit")
        timeframe = filters.get("timeframe")
        name = filters.get("name")

        tracks: List[str] = []

        # -------------------------
        # EXPLICIT (NEW)
        # -------------------------
        if source_type == "explicit":
            tracks = filters.get("track_ids", []) or []

        # -------------------------
        # ARTIST
        # -------------------------
        elif source_type == "artist" and name:
            tracks = repo.get_tracks_by_artist(name)

        # -------------------------
        # ALBUM
        # -------------------------
        elif source_type == "album" and name:
            tracks = repo.get_tracks_by_album(name)

        # -------------------------
        # TOP PLAYED
        # -------------------------
        elif source_type == "top_played":
            rows = repo.get_play_history_aggregated(decay_days=30.0)

            sorted_rows = sorted(
                rows,
                key=lambda r: r[2],  # total_plays
                reverse=True
            )

            tracks = [r[0] for r in sorted_rows]

        # -------------------------
        # RECENTLY ADDED
        # -------------------------
        elif source_type == "recently_added":
            tracks = repo.get_recent_tracks(limit=limit or 20)

        # -------------------------
        # Apply per-source limit
        # -------------------------
        if limit and isinstance(limit, int):
            tracks = tracks[:limit]

        all_tracks.extend(tracks)

    # =====================================================
    # DEDUPLICATION
    # =====================================================

    if constraints.get("deduplicate", True):
        all_tracks = list(dict.fromkeys(all_tracks))

    # =====================================================
    # GLOBAL LIMIT
    # =====================================================

    max_tracks = constraints.get("max_tracks")
    if max_tracks and isinstance(max_tracks, int):
        all_tracks = all_tracks[:max_tracks]

    return all_tracks