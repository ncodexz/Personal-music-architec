# core/ingestion.py

from core.semantic.anchors import convert_playlist_to_anchor
from core.database import get_latest_added_at


# =====================================================
# TRACK SYNC
# =====================================================

def sync_new_tracks(sp, repo):
    """
    Synchronize new saved tracks from Spotify into SQLite.
    Only inserts tracks added after latest stored added_at.
    """

    latest_added_at = get_latest_added_at(repo.conn)
    cursor = repo.conn.cursor()

    limit = 50
    offset = 0
    new_tracks_count = 0
    new_tracks_ids = []

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
            new_tracks_ids.append(track_id)

            cursor.execute("""
                INSERT OR IGNORE INTO tracks
                (track_id, name, added_at, duration_ms, popularity)
                VALUES (?, ?, ?, ?, ?);
            """, (
                track_id,
                track["name"],
                added_at,
                track["duration_ms"],
                track.get("popularity")
            ))

            # Artists
            for artist in track["artists"]:
                cursor.execute("""
                    INSERT OR IGNORE INTO artists (artist_id, name)
                    VALUES (?, ?);
                """, (
                    artist["id"],
                    artist["name"]
                ))

                cursor.execute("""
                    INSERT OR IGNORE INTO track_artists (track_id, artist_id)
                    VALUES (?, ?);
                """, (
                    track_id,
                    artist["id"]
                ))

            # Album
            album = track["album"]

            cursor.execute("""
                INSERT OR IGNORE INTO albums
                (album_id, name, release_date, total_tracks, album_type)
                VALUES (?, ?, ?, ?, ?);
            """, (
                album["id"],
                album["name"],
                album.get("release_date"),
                album.get("total_tracks"),
                album.get("album_type")
            ))

            cursor.execute("""
                INSERT OR IGNORE INTO track_albums (track_id, album_id)
                VALUES (?, ?);
            """, (
                track_id,
                album["id"]
            ))

            new_tracks_count += 1

        if stop_sync:
            break

        offset += limit

    repo.commit()

    return {
        "new_tracks_count": new_tracks_count,
        "new_tracks_ids": new_tracks_ids
    }


# =====================================================
# PLAYLIST SYNC
# =====================================================

def sync_playlists(sp, repo):
    """
    Synchronize user-owned playlists.
    Only tracks existing in library are inserted.
    Handles ANCHOR_ playlists.
    """

    from core.playlists import get_playlist_items

    cursor = repo.conn.cursor()
    current_user_id = sp.current_user()["id"]

    limit = 50
    offset = 0

    total_playlists_synced = 0
    total_playlist_tracks_synced = 0
    anchors_updated = []

    while True:
        playlists = sp.current_user_playlists(limit=limit, offset=offset)
        items = playlists.get("items", [])

        if not items:
            break

        for playlist in items:

            if playlist["owner"]["id"] != current_user_id:
                continue

            playlist_id = playlist["id"]
            name = playlist.get("name")

            # ==========================
            # ANCHOR DETECTION
            # ==========================

            if name and name.startswith("ANCHOR_"):

                anchor_id = convert_playlist_to_anchor(
                    repo,
                    playlist_id,
                    name
                )

                if anchor_id:

                    anchors_updated.append(anchor_id)

                    sp.current_user_unfollow_playlist(playlist_id)

                    cursor.execute(
                        "DELETE FROM playlists WHERE playlist_id = ?;",
                        (playlist_id,)
                    )

                    repo.commit()

                continue

            # ==========================
            # NORMAL PLAYLIST SYNC
            # ==========================

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
                playlist.get("description"),
                playlist["owner"]["id"],
                int(playlist.get("collaborative", False)),
                int(playlist.get("public", False)),
                playlist.get("tracks", {}).get("total"),
                playlist.get("snapshot_id")
            ))

            total_playlists_synced += 1

            cursor.execute(
                "DELETE FROM playlist_tracks WHERE playlist_id = ?;",
                (playlist_id,)
            )

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

                batch = result.get("items", [])

                if not batch:
                    break

                for entry in batch:

                    content = entry.get("item")

                    if not content:
                        continue

                    if content.get("type") != "track":
                        continue

                    track_id = content.get("id")

                    if not track_id:
                        continue

                    # Only include tracks already in library
                    cursor.execute(
                        "SELECT 1 FROM tracks WHERE track_id = ?;",
                        (track_id,)
                    )

                    if not cursor.fetchone():
                        continue

                    cursor.execute("""
                        INSERT OR IGNORE INTO playlist_tracks
                        (playlist_id, track_id, added_at, position)
                        VALUES (?, ?, ?, ?);
                    """, (
                        playlist_id,
                        track_id,
                        entry.get("added_at"),
                        position
                    ))

                    position += 1
                    total_playlist_tracks_synced += 1

                track_offset += track_limit

        offset += limit

    repo.commit()

    return {
        "playlists_synced": total_playlists_synced,
        "playlist_tracks_synced": total_playlist_tracks_synced,
        "anchors_updated": anchors_updated
    }