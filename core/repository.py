"""
Data access layer for SQLite.
All functions in this file are responsible for querying the local database.
No Spotify logic should exist here.
"""


def get_tracks_by_artist(conn, artist_name: str):
    """
    Retrieve all track_ids for a given artist.
    Ordered by most recently added.
    """
    query = """
    SELECT t.track_id
    FROM tracks t
    JOIN track_artists ta ON t.track_id = ta.track_id
    JOIN artists a ON ta.artist_id = a.artist_id
    WHERE LOWER(a.name) = LOWER(?)
    ORDER BY t.added_at DESC
    """

    cursor = conn.cursor()
    cursor.execute(query, (artist_name,))
    results = cursor.fetchall()

    return [r[0] for r in results]


def get_recent_tracks(conn, limit: int = 20):
    """
    Retrieve the most recently added track_ids.
    Limit defines how many tracks to return.
    """
    query = """
    SELECT track_id
    FROM tracks
    ORDER BY added_at DESC
    LIMIT ?
    """

    cursor = conn.cursor()
    cursor.execute(query, (limit,))
    results = cursor.fetchall()

    return [r[0] for r in results]


def get_tracks_by_album(conn, album_name: str):
    """
    Retrieve all track_ids for a given album.
    Ordered by most recently added.
    """
    query = """
    SELECT t.track_id
    FROM tracks t
    JOIN track_albums ta ON t.track_id = ta.track_id
    JOIN albums al ON ta.album_id = al.album_id
    WHERE LOWER(al.name) = LOWER(?)
    ORDER BY t.added_at DESC
    """

    cursor = conn.cursor()
    cursor.execute(query, (album_name,))
    results = cursor.fetchall()

    return [r[0] for r in results]


def get_tracks_by_artist_and_recent(conn, artist_name: str, limit: int = 20):
    """
    Retrieve the most recently added track_ids for a given artist.
    """
    query = """
    SELECT t.track_id
    FROM tracks t
    JOIN track_artists ta ON t.track_id = ta.track_id
    JOIN artists a ON ta.artist_id = a.artist_id
    WHERE LOWER(a.name) = LOWER(?)
    ORDER BY t.added_at DESC
    LIMIT ?
    """

    cursor = conn.cursor()
    cursor.execute(query, (artist_name, limit))
    results = cursor.fetchall()

    return [r[0] for r in results]


def get_tracks_by_artist_and_album(conn, artist_name: str, album_name: str):
    """
    Retrieve track_ids filtered by both artist and album.
    """
    query = """
    SELECT t.track_id
    FROM tracks t
    JOIN track_artists ta ON t.track_id = ta.track_id
    JOIN artists a ON ta.artist_id = a.artist_id
    JOIN track_albums tal ON t.track_id = tal.track_id
    JOIN albums al ON tal.album_id = al.album_id
    WHERE LOWER(a.name) = LOWER(?)
      AND LOWER(al.name) = LOWER(?)
    ORDER BY t.added_at DESC
    """

    cursor = conn.cursor()
    cursor.execute(query, (artist_name, album_name))
    results = cursor.fetchall()

    return [r[0] for r in results]
