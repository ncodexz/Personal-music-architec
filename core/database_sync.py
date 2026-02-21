def sync_database(sp, conn, include_behavior: bool = False) -> dict:
    """
    Full database synchronization pipeline.

    - Sync saved tracks (tracks, artists, albums, relations)
    - Sync missing audio features
    - Optionally sync recently played behavior

    Returns summary dictionary.
    """

    summary = {
        "new_tracks": 0,
        "audio_features_inserted": 0,
        "play_events_inserted": 0
    }

    summary["new_tracks"] = _sync_saved_tracks(sp, conn)
    summary["audio_features_inserted"] = _sync_missing_audio_features(sp, conn)

    if include_behavior:
        summary["play_events_inserted"] = _sync_behavior(sp, conn)

    return summary


def _sync_saved_tracks(sp, conn) -> int:
    from core.database import get_latest_added_at

    cursor = conn.cursor()
    latest_added_at = get_latest_added_at(conn)

    limit = 50
    offset = 0
    new_tracks_count = 0

    while True:
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        items = results.get("items", [])

        if not items:
            break

        stop_sync = False

        for item in items:
            track = item["track"]
            added_at = item["added_at"]

            if latest_added_at and added_at <= latest_added_at:
                stop_sync = True
                break

            track_id = track["id"]
            name = track["name"]
            duration_ms = track["duration_ms"]
            popularity = track.get("popularity")

            cursor.execute("""
                INSERT OR IGNORE INTO tracks
                (track_id, name, added_at, duration_ms, popularity)
                VALUES (?, ?, ?, ?, ?)
            """, (
                track_id,
                name,
                added_at,
                duration_ms,
                popularity
            ))

            for artist in track["artists"]:
                artist_id = artist["id"]
                artist_name = artist["name"]

                cursor.execute("""
                    INSERT OR IGNORE INTO artists (artist_id, name)
                    VALUES (?, ?)
                """, (
                    artist_id,
                    artist_name
                ))

                cursor.execute("""
                    INSERT OR IGNORE INTO track_artists (track_id, artist_id)
                    VALUES (?, ?)
                """, (
                    track_id,
                    artist_id
                ))

            album = track["album"]
            album_id = album["id"]
            album_name = album["name"]
            release_date = album.get("release_date")
            total_tracks = album.get("total_tracks")
            album_type = album.get("album_type")

            cursor.execute("""
                INSERT OR IGNORE INTO albums
                (album_id, name, release_date, total_tracks, album_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                album_id,
                album_name,
                release_date,
                total_tracks,
                album_type
            ))

            cursor.execute("""
                INSERT OR IGNORE INTO track_albums (track_id, album_id)
                VALUES (?, ?)
            """, (
                track_id,
                album_id
            ))

            new_tracks_count += 1

        if stop_sync:
            break

        offset += limit

    conn.commit()
    return new_tracks_count


def _sync_missing_audio_features(sp, conn, batch_size: int = 50) -> int:
    """
    Sync only missing audio features.
    Uses safe batching and error handling.
    """

    cursor = conn.cursor()

    cursor.execute("""
        SELECT t.track_id
        FROM tracks t
        LEFT JOIN track_audio_features taf
        ON t.track_id = taf.track_id
        WHERE taf.track_id IS NULL
    """)

    rows = cursor.fetchall()
    track_ids = [r[0] for r in rows]

    if not track_ids:
        return 0

    inserted = 0

    for i in range(0, len(track_ids), batch_size):
        batch = track_ids[i:i + batch_size]

        try:
            features_list = sp.audio_features(batch)
        except Exception:
            continue

        for features in features_list:
            if not features:
                continue

            cursor.execute("""
                INSERT INTO track_audio_features (
                    track_id,
                    danceability,
                    energy,
                    valence,
                    tempo,
                    acousticness,
                    instrumentalness,
                    liveness,
                    speechiness
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                features["id"],
                features["danceability"],
                features["energy"],
                features["valence"],
                features["tempo"],
                features["acousticness"],
                features["instrumentalness"],
                features["liveness"],
                features["speechiness"]
            ))

            inserted += 1

    conn.commit()
    return inserted


def _sync_behavior(sp, conn, limit: int = 50) -> int:
    from core.behavior import ingest_recently_played
    return ingest_recently_played(sp, conn, limit=limit)