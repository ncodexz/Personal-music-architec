from datetime import datetime


def ingest_recently_played(sp, conn, limit: int = 50) -> int:
    """
    Ingest recently played tracks from Spotify into play_history.
    Only inserts events for tracks that already exist in tracks table.
    Returns number of inserted rows.
    """

    results = sp.current_user_recently_played(limit=limit)

    cursor = conn.cursor()
    inserted = 0

    for item in results.get("items", []):
        track = item.get("track")
        if not track:
            continue

        track_id = track.get("id")
        played_at = item.get("played_at")

        if not track_id or not played_at:
            continue

        # Ensure track exists in tracks table to satisfy FK constraint
        cursor.execute(
            "SELECT 1 FROM tracks WHERE track_id = ?;",
            (track_id,)
        )
        exists = cursor.fetchone()

        if not exists:
            continue

        context = item.get("context")
        context_type = None
        context_id = None

        if context:
            context_type = context.get("type")
            context_uri = context.get("uri")

            if context_uri and ":" in context_uri:
                context_id = context_uri.split(":")[-1]

        # Append-only insert
        cursor.execute("""
        INSERT INTO play_history (
            track_id,
            played_at,
            context_type,
            context_id,
            source,
            weight
        )
        VALUES (?, ?, ?, ?, ?, ?);
        """, (
            track_id,
            played_at,
            context_type,
            context_id,
            "spotify_recent",
            1.0
        ))

        inserted += 1

    conn.commit()

    return inserted


def simulate_play_event(conn, track_id: str, played_at: str | None = None, weight: float = 1.0) -> None:
    """
    Manually insert a simulated play event.
    Used for artificial behavioral data growth.
    """

    if not played_at:
        played_at = datetime.utcnow().isoformat()

    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM tracks WHERE track_id = ?;",
        (track_id,)
    )
    exists = cursor.fetchone()

    if not exists:
        return

    cursor.execute("""
    INSERT INTO play_history (
        track_id,
        played_at,
        context_type,
        context_id,
        source,
        weight
    )
    VALUES (?, ?, ?, ?, ?, ?);
    """, (
        track_id,
        played_at,
        None,
        None,
        "simulated",
        weight
    ))

    conn.commit()


def simulate_bulk_behavior(conn, track_ids: list[str], plays_per_track: int = 5) -> int:
    """
    Simulate multiple play events per track.
    Useful for demonstrating ranking behavior.
    """

    inserted = 0

    for track_id in track_ids:
        for _ in range(plays_per_track):
            simulate_play_event(conn, track_id)
            inserted += 1

    return inserted