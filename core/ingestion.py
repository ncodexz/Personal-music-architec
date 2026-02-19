def fetch_all_saved_tracks(sp):
    """
    Fetch all saved tracks from Spotify using pagination.
    """
    all_tracks = []
    limit = 50
    offset = 0

    while True:
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        items = results["items"]

        if not items:
            break

        all_tracks.extend(items)
        offset += limit

    return all_tracks


def sync_new_tracks(sp, conn, get_latest_added_at_func):
    """
    Synchronize new tracks from Spotify into the local database.
    Only inserts tracks added after the latest stored added_at.
    """
    latest_added_at = get_latest_added_at_func(conn)

    cursor = conn.cursor()

    limit = 50
    offset = 0
    new_tracks_count = 0

    while True:
        results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        items = results["items"]

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

            # Insert Track
          
            cursor.execute("""
            INSERT OR IGNORE INTO tracks (track_id, name, added_at, duration_ms, popularity)
            VALUES (?, ?, ?, ?, ?);
            """, (
                track_id,
                name,
                added_at,
                duration_ms,
                popularity
            ))

           
            # Insert Artists + Relation
           
            for artist in track["artists"]:
                artist_id = artist["id"]
                artist_name = artist["name"]

                cursor.execute("""
                INSERT OR IGNORE INTO artists (artist_id, name)
                VALUES (?, ?);
                """, (
                    artist_id,
                    artist_name
                ))

                cursor.execute("""
                INSERT OR IGNORE INTO track_artists (track_id, artist_id)
                VALUES (?, ?);
                """, (
                    track_id,
                    artist_id
                ))

        
            # Insert Album + Relation 
            
            album = track["album"]
            album_id = album["id"]
            album_name = album["name"]
            release_date = album.get("release_date")
            total_tracks = album.get("total_tracks")
            album_type = album.get("album_type")

            cursor.execute("""
            INSERT OR IGNORE INTO albums (album_id, name, release_date, total_tracks, album_type)
            VALUES (?, ?, ?, ?, ?);
            """, (
                album_id,
                album_name,
                release_date,
                total_tracks,
                album_type
            ))

            cursor.execute("""
            INSERT OR IGNORE INTO track_albums (track_id, album_id)
            VALUES (?, ?);
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
