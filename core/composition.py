def build_strategic_playlist(conn, strategy: dict) -> list[str]:
    """
    Build a strategic playlist based on structured strategy config.
    Returns ordered list of track_ids.
    """

    subsets = {}

    for subset_cfg in strategy.get("subsets", []):
        subset_type = subset_cfg["type"]

        if subset_type == "album":
            subsets["album"] = _get_album_subset(
                conn,
                album_name=subset_cfg["name"],
                top_by=subset_cfg.get("top_by"),
                limit=subset_cfg.get("limit")
            )

        elif subset_type == "artist":
            subsets["artist"] = _get_artist_subset(
                conn,
                artist_name=subset_cfg["name"]
            )

    ordered_tracks = _merge_with_priority(
        subsets,
        strategy.get("priority_order", [])
    )

    final_tracks = _apply_global_limit(
        ordered_tracks,
        strategy.get("max_tracks")
    )

    return final_tracks

def _get_album_subset(conn, album_name: str, top_by: str | None = None, limit: int | None = None) -> list[str]:
    """
    Retrieve tracks from album.
    Supports ranking by:
    - recency
    - most_played
    """

    cursor = conn.cursor()

    if top_by == "recency":
        cursor.execute("""
        SELECT
            ph.track_id,
            SUM(
                ph.weight *
                EXP(
                    - (julianday('now') - julianday(ph.played_at)) / 30.0
                )
            ) as score
        FROM play_history ph
        JOIN track_albums ta ON ta.track_id = ph.track_id
        JOIN albums a ON a.album_id = ta.album_id
        WHERE a.name = ?
        GROUP BY ph.track_id
        ORDER BY score DESC
        """, (album_name,))

        rows = cursor.fetchall()
        track_ids = [r[0] for r in rows]

    elif top_by == "most_played":
        cursor.execute("""
        SELECT
            ph.track_id,
            COUNT(*) as play_count
        FROM play_history ph
        JOIN track_albums ta ON ta.track_id = ph.track_id
        JOIN albums a ON a.album_id = ta.album_id
        WHERE a.name = ?
        GROUP BY ph.track_id
        ORDER BY play_count DESC
        """, (album_name,))

        rows = cursor.fetchall()
        track_ids = [r[0] for r in rows]

    else:
        cursor.execute("""
        SELECT t.track_id
        FROM tracks t
        JOIN track_albums ta ON ta.track_id = t.track_id
        JOIN albums a ON a.album_id = ta.album_id
        WHERE a.name = ?
        """, (album_name,))

        rows = cursor.fetchall()
        track_ids = [r[0] for r in rows]

    if limit:
        track_ids = track_ids[:limit]

    return track_ids


def _get_artist_subset(conn, artist_name: str) -> list[str]:
    """
    Retrieve all tracks from a given artist.
    """

    cursor = conn.cursor()

    cursor.execute("""
    SELECT DISTINCT t.track_id
    FROM tracks t
    JOIN track_artists ta ON ta.track_id = t.track_id
    JOIN artists a ON a.artist_id = ta.artist_id
    WHERE a.name = ?
    """, (artist_name,))

    return [r[0] for r in cursor.fetchall()]


def _merge_with_priority(subsets: dict, priority_order: list[str]) -> list[str]:
    """
    Merge subsets following explicit priority order.
    Deduplicate while preserving order.
    """

    merged = []

    for key in priority_order:
        if key in subsets:
            merged.extend(subsets[key])

    return list(dict.fromkeys(merged))


def _apply_global_limit(track_ids: list[str], max_tracks: int | None) -> list[str]:
    """
    Apply global limit to final track list.
    """

    if max_tracks:
        return track_ids[:max_tracks]

    return track_ids