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

def sync_playlists(sp, conn):
    """
    Synchronize playlists owned by the current user into the local database.
    Uses the official /items endpoint (Spotify current contract).
    Only tracks that exist in the local library are inserted.
    """

    from core.playlists import get_playlist_items

    cursor = conn.cursor()

    current_user_id = sp.current_user()["id"]

    limit = 50
    offset = 0

    total_playlists_synced = 0
    total_playlist_tracks_synced = 0

    while True:
        playlists = sp.current_user_playlists(limit=limit, offset=offset)
        items = playlists.get("items", [])

        if not items:
            break

        for playlist in items:

            # Only sync playlists owned by the current user
            if playlist["owner"]["id"] != current_user_id:
                continue

            playlist_id = playlist["id"]
            name = playlist.get("name")
            description = playlist.get("description")
            owner_id = playlist["owner"]["id"]
            is_collaborative = int(playlist.get("collaborative", False))
            is_public = int(playlist.get("public", False))
            total_tracks = playlist.get("tracks", {}).get("total")
            snapshot_id = playlist.get("snapshot_id")

            # Insert or replace playlist metadata
            cursor.execute("""
                INSERT OR REPLACE INTO playlists (
                    playlist_id,
                    name,
                    description,
                    owner_id,
                    is_collaborative,
                    is_public,
                    total_tracks,
                    snapshot_id,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'));
            """, (
                playlist_id,
                name,
                description,
                owner_id,
                is_collaborative,
                is_public,
                total_tracks,
                snapshot_id
            ))

            total_playlists_synced += 1

            # Clean previous snapshot
            cursor.execute("""
                DELETE FROM playlist_tracks
                WHERE playlist_id = ?;
            """, (playlist_id,))

            # Fetch playlist items
            track_offset = 0
            track_limit = 100
            position = 0

            while True:
                result = get_playlist_items(
                    sp,
                    playlist_id,
                    limit=track_limit,
                    offset=track_offset
                )

                tracks_batch = result.get("items", [])

                if not tracks_batch:
                    break

                for entry in tracks_batch:

                    content = entry.get("item")

                    if not content:
                        continue

                    if content.get("type") != "track":
                        continue

                    track_id = content.get("id")
                    added_at = entry.get("added_at")

                    if not track_id:
                        continue

                    #  IMPORTANT: Only include tracks that exist in library
                    cursor.execute(
                        "SELECT 1 FROM tracks WHERE track_id = ?;",
                        (track_id,)
                    )
                    if not cursor.fetchone():
                        continue

                    cursor.execute("""
                        INSERT OR IGNORE INTO playlist_tracks (
                            playlist_id,
                            track_id,
                            added_at,
                            position
                        )
                        VALUES (?, ?, ?, ?);
                    """, (
                        playlist_id,
                        track_id,
                        added_at,
                        position
                    ))

                    position += 1
                    total_playlist_tracks_synced += 1

                track_offset += track_limit

        offset += limit

    conn.commit()

    return {
        "playlists_synced": total_playlists_synced,
        "playlist_tracks_synced": total_playlist_tracks_synced
    }