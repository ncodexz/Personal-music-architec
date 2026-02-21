from datetime import datetime


def update_track_metrics(conn, decay_days: float = 30.0) -> int:
    """
    Recalculate engagement metrics for all tracks based on:

    - Recency-weighted play score
    - Total play count
    - Popularity (normalized)

    Stores results in track_metrics table.

    Returns number of updated rows.
    """

    cursor = conn.cursor()

    # Get recency weighted scores
    cursor.execute(f"""
        SELECT
            ph.track_id,
            SUM(
                ph.weight *
                EXP(
                    - (julianday('now') - julianday(ph.played_at)) / {decay_days}
                )
            ) as recency_score,
            COUNT(*) as total_plays
        FROM play_history ph
        GROUP BY ph.track_id
    """)

    play_data = cursor.fetchall()

    if not play_data:
        return 0

    # Get max values for normalization
    max_recency = max(row[1] for row in play_data)
    max_plays = max(row[2] for row in play_data)

    updated = 0

    for track_id, recency_score, total_plays in play_data:

        recency_norm = recency_score / max_recency if max_recency else 0
        plays_norm = total_plays / max_plays if max_plays else 0

        cursor.execute("""
            SELECT popularity
            FROM tracks
            WHERE track_id = ?
        """, (track_id,))

        row = cursor.fetchone()
        popularity = row[0] if row and row[0] is not None else 0
        popularity_norm = popularity / 100.0

        engagement_score = (
            recency_norm * 0.6 +
            plays_norm * 0.3 +
            popularity_norm * 0.1
        )

        cursor.execute("""
            INSERT INTO track_metrics (
                track_id,
                playlist_count,
                added_recency_score,
                popularity,
                engagement_score,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(track_id) DO UPDATE SET
                added_recency_score = excluded.added_recency_score,
                popularity = excluded.popularity,
                engagement_score = excluded.engagement_score,
                updated_at = excluded.updated_at
        """, (
            track_id,
            0,
            recency_score,
            popularity,
            engagement_score,
            datetime.utcnow().isoformat()
        ))

        updated += 1

    conn.commit()

    return updated