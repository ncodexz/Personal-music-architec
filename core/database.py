import sqlite3


def get_connection(db_path: str = "music_agent.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables(conn):
    cursor = conn.cursor()

    # =========================
    # Core Domain
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tracks (
        track_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        added_at TEXT NOT NULL,
        duration_ms INTEGER,
        popularity INTEGER
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artists (
        artist_id TEXT PRIMARY KEY,
        name TEXT NOT NULL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS albums (
        album_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        release_date TEXT,
        total_tracks INTEGER,
        album_type TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS track_artists (
        track_id TEXT NOT NULL,
        artist_id TEXT NOT NULL,
        PRIMARY KEY (track_id, artist_id),
        FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE,
        FOREIGN KEY (artist_id) REFERENCES artists(artist_id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS track_albums (
        track_id TEXT NOT NULL,
        album_id TEXT NOT NULL,
        PRIMARY KEY (track_id, album_id),
        FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE,
        FOREIGN KEY (album_id) REFERENCES albums(album_id) ON DELETE CASCADE
    );
    """)

    # =========================
    # Playlists Domain
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS playlists (
        playlist_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        owner_id TEXT,
        is_collaborative INTEGER,
        is_public INTEGER,
        total_tracks INTEGER,
        snapshot_id TEXT,
        updated_at TEXT
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS playlist_tracks (
        playlist_id TEXT NOT NULL,
        track_id TEXT NOT NULL,
        added_at TEXT,
        position INTEGER,
        PRIMARY KEY (playlist_id, track_id),
        FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id) ON DELETE CASCADE,
        FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE
    );
    """)

    # =========================
    # Saved Albums
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS saved_albums (
        album_id TEXT PRIMARY KEY,
        added_at TEXT,
        FOREIGN KEY (album_id) REFERENCES albums(album_id) ON DELETE CASCADE
    );
    """)

    # =========================
    # Audio Features
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS track_audio_features (
        track_id TEXT PRIMARY KEY,
        danceability REAL,
        energy REAL,
        valence REAL,
        tempo REAL,
        acousticness REAL,
        instrumentalness REAL,
        liveness REAL,
        speechiness REAL,
        FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE
    );
    """)

    # =========================
    # Metrics Domain
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS track_metrics (
        track_id TEXT PRIMARY KEY,
        playlist_count INTEGER DEFAULT 0,
        added_recency_score REAL DEFAULT 0,
        popularity INTEGER,
        engagement_score REAL DEFAULT 0,
        updated_at TEXT,
        FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS playlist_metrics (
        playlist_id TEXT PRIMARY KEY,
        avg_energy REAL,
        avg_valence REAL,
        dominant_artist TEXT,
        overlap_score REAL,
        total_tracks INTEGER,
        updated_at TEXT,
        FOREIGN KEY (playlist_id) REFERENCES playlists(playlist_id) ON DELETE CASCADE
    );
    """)

    # =========================
    # Behavioral Domain
    # =========================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS play_history (
        track_id TEXT NOT NULL,
        played_at TEXT NOT NULL,
        context_type TEXT,
        context_id TEXT,
        FOREIGN KEY (track_id) REFERENCES tracks(track_id) ON DELETE CASCADE
    );
    """)

    # =========================
    # Indexes (Read Optimization)
    # =========================

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tracks_added_at ON tracks(added_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_track_artists_artist ON track_artists(artist_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_track_albums_album ON track_albums(album_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_playlist_tracks_playlist ON playlist_tracks(playlist_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_playlist_tracks_track ON playlist_tracks(track_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audio_features_energy ON track_audio_features(energy);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audio_features_valence ON track_audio_features(valence);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_track_metrics_engagement ON track_metrics(engagement_score);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_play_history_played_at ON play_history(played_at);")

    conn.commit()


def get_latest_added_at(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(added_at) FROM tracks;")
    result = cursor.fetchone()[0]
    return result
