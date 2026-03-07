# core/repository.py

from datetime import datetime


class Repository:
    def __init__(self, db_session):
        self.conn = db_session.conn
        self._session = db_session

    def commit(self):
        self._session.commit()
    
    def commit_batch(self):
        self.commit()

    # =====================================================
    # TRACKS
    # =====================================================

    def get_tracks_by_artist(self, artist_name: str) -> list[str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT t.track_id
            FROM tracks t
            JOIN track_artists ta ON t.track_id = ta.track_id
            JOIN artists a ON ta.artist_id = a.artist_id
            WHERE LOWER(a.name) = LOWER(?)
            ORDER BY t.added_at DESC
        """, (artist_name,))
        return [r[0] for r in cursor.fetchall()]

    def get_tracks_by_album(self, album_name: str) -> list[str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT t.track_id
            FROM tracks t
            JOIN track_albums ta ON ta.track_id = t.track_id
            JOIN albums a ON ta.album_id = a.album_id
            WHERE LOWER(a.name) = LOWER(?)
            ORDER BY t.added_at DESC
        """, (album_name,))
        return [r[0] for r in cursor.fetchall()]

    def get_recent_tracks(self, limit: int = 20) -> list[str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT track_id
            FROM tracks
            ORDER BY added_at DESC
            LIMIT ?
        """, (limit,))
        return [r[0] for r in cursor.fetchall()]
    
    def get_album_tracks_raw(self, album_name: str) -> list[str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT t.track_id
            FROM tracks t
            JOIN track_albums ta ON ta.track_id = t.track_id
            JOIN albums a ON a.album_id = ta.album_id
            WHERE a.name = ?
        """, (album_name,))
        return [r[0] for r in cursor.fetchall()]
    
    def get_artist_tracks_raw(self, artist_name: str) -> list[str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT t.track_id
            FROM tracks t
            JOIN track_artists ta ON ta.track_id = t.track_id
            JOIN artists a ON a.artist_id = ta.artist_id
            WHERE a.name = ?
        """, (artist_name,))
        return [r[0] for r in cursor.fetchall()]

    def track_exists(self, track_id: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT 1 FROM tracks WHERE track_id = ?;",
            (track_id,)
        )
        return cursor.fetchone() is not None

    def count_tracks_by_artist(self, artist_name: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM tracks t
            JOIN track_artists ta ON t.track_id = ta.track_id
            JOIN artists a ON ta.artist_id = a.artist_id
            WHERE LOWER(a.name) = LOWER(?)
        """, (artist_name,))
        return cursor.fetchone()[0]
    
    def count_tracks(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM tracks
        """)
        return cursor.fetchone()[0]
    
    def get_track_name(self, track_id: str) -> str | None:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name
            FROM tracks
            WHERE track_id = ?
        """, (track_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    def get_all_tracks_with_artists(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                t.track_id,
                t.name,
                a.name
            FROM tracks t
            JOIN track_artists ta ON t.track_id = ta.track_id
            JOIN artists a ON ta.artist_id = a.artist_id
            ORDER BY t.track_id;
        """)

        rows = cursor.fetchall()

        tracks = {}

        for track_id, track_name, artist_name in rows:
            if track_id not in tracks:
                tracks[track_id] = {
                    "track_id": track_id,
                    "name": track_name,
                    "artists": []
                }

            tracks[track_id]["artists"].append(artist_name)

        return list(tracks.values())
    
    def get_tracks_with_artists(self, track_ids: list[str]):

        if not track_ids:
            return []

        placeholders = ",".join(["?"] * len(track_ids))

        cursor = self.conn.cursor()

        query = f"""
            SELECT
                t.track_id,
                t.name,
                a.name
            FROM tracks t
            JOIN track_artists ta ON t.track_id = ta.track_id
            JOIN artists a ON ta.artist_id = a.artist_id
            WHERE t.track_id IN ({placeholders})
            ORDER BY t.track_id;
        """

        cursor.execute(query, track_ids)

        rows = cursor.fetchall()

        tracks = {}

        for track_id, track_name, artist_name in rows:

            if track_id not in tracks:
                tracks[track_id] = {
                    "track_id": track_id,
                    "name": track_name,
                    "artists": []
                }

            tracks[track_id]["artists"].append(artist_name)

        return list(tracks.values())
    
    # =====================================================
    # BEHAVIOR (Play History)
    # =====================================================

    def insert_play_event(
        self,
        track_id: str,
        played_at: str,
        context_type: str | None,
        context_id: str | None,
        source: str,
        weight: float = 1.0
    ):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO play_history (
                track_id,
                played_at,
                context_type,
                context_id,
                source,
                weight
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            track_id,
            played_at,
            context_type,
            context_id,
            source,
            weight
        ))
        self.commit()

    def get_recency_scores(self, limit: int, decay_days: float):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT
                ph.track_id,
                SUM(
                    ph.weight *
                    EXP(
                        - (julianday('now') - julianday(ph.played_at)) / {decay_days}
                    )
                ) as score
            FROM play_history ph
            GROUP BY ph.track_id
            ORDER BY score DESC
            LIMIT ?;
        """, (limit,))
        return cursor.fetchall()

    def get_album_recency_scores(self, album_name: str, limit: int, decay_days: float):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT
                ph.track_id,
                SUM(
                    ph.weight *
                    EXP(
                        - (julianday('now') - julianday(ph.played_at)) / {decay_days}
                    )
                ) as score
            FROM play_history ph
            JOIN track_albums ta ON ta.track_id = ph.track_id
            JOIN albums a ON a.album_id = ta.album_id
            WHERE a.name = ?
            GROUP BY ph.track_id
            ORDER BY score DESC
            LIMIT ?;
        """, (album_name, limit))
        return cursor.fetchall()

    def get_artist_recency_scores(self, limit: int, decay_days: float):
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT
                a.artist_id,
                SUM(
                    ph.weight *
                    EXP(
                        - (julianday('now') - julianday(ph.played_at)) / {decay_days}
                    )
                ) as score
            FROM play_history ph
            JOIN track_artists ta ON ta.track_id = ph.track_id
            JOIN artists a ON a.artist_id = ta.artist_id
            GROUP BY a.artist_id
            ORDER BY score DESC
            LIMIT ?;
        """, (limit,))
        return cursor.fetchall()
    
    def get_album_most_played(self, album_name: str) -> list[str]:
        cursor = self.conn.cursor()
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
        return [r[0] for r in cursor.fetchall()]

    def get_play_history_aggregated(self, decay_days: float):
        cursor = self.conn.cursor()
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
        return cursor.fetchall()

    def get_track_popularity(self, track_id: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT popularity
            FROM tracks
            WHERE track_id = ?
        """, (track_id,))
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0
    
    def get_most_played_track(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT ph.track_id, COUNT(*) as play_count
            FROM play_history ph
            GROUP BY ph.track_id
            ORDER BY play_count DESC
            LIMIT 1
        """)
        return cursor.fetchone()
    
    def get_recently_played_track_names(self, limit: int = 5):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT t.name
            FROM play_history ph
            JOIN tracks t ON ph.track_id = t.track_id
            ORDER BY ph.played_at DESC
            LIMIT ?
        """, (limit,))
        return [r[0] for r in cursor.fetchall()]
    
    # =====================================================
    # METRICS
    # =====================================================

    def get_engagement_score(self, track_id: str) -> float:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT engagement_score
            FROM track_metrics
            WHERE track_id = ?
        """, (track_id,))
        row = cursor.fetchone()
        return row[0] if row else 0.0

    def get_engagement_scores_for_tracks(self, track_ids: list[str]):
        if not track_ids:
            return []

        cursor = self.conn.cursor()
        placeholders = ",".join(["?"] * len(track_ids))

        query = f"""
            SELECT track_id, engagement_score
            FROM track_metrics
            WHERE track_id IN ({placeholders})
            ORDER BY engagement_score DESC;
        """

        cursor.execute(query, track_ids)
        return cursor.fetchall()

    def upsert_track_metrics(
        self,
        track_id: str,
        recency_score: float,
        popularity: int,
        engagement_score: float
    ):
        cursor = self.conn.cursor()
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

    # =====================================================
    # PLAYLISTS
    # =====================================================

    def get_playlist_tracks(self, playlist_id: str) -> list[str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT track_id
            FROM playlist_tracks
            WHERE playlist_id = ?
            ORDER BY position ASC
        """, (playlist_id,))
        return [r[0] for r in cursor.fetchall()]

    def add_track_to_playlist(
        self,
        playlist_id: str,
        track_id: str,
        position: int
    ):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO playlist_tracks (playlist_id, track_id, position)
            VALUES (?, ?, ?)
        """, (playlist_id, track_id, position))
        self.commit()

    def get_all_playlists(self) -> list[str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name
            FROM playlists
            ORDER BY name ASC
        """)
        return [r[0] for r in cursor.fetchall()]

    def get_all_playlist_ids(self) -> list[str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT playlist_id
            FROM playlists
        """)
        return [r[0] for r in cursor.fetchall()]
    
    def count_playlists(self) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM playlists
        """)
        return cursor.fetchone()[0]

    def count_artist_tracks_in_playlists(self, artist_name: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(DISTINCT pt.track_id)
            FROM playlist_tracks pt
            JOIN track_artists ta ON pt.track_id = ta.track_id
            JOIN artists a ON ta.artist_id = a.artist_id
            WHERE LOWER(a.name) = LOWER(?)
        """, (artist_name,))
        return cursor.fetchone()[0]
    
    def delete_playlist(self, playlist_id: str):
        cursor = self.conn.cursor()

        # Remove tracks linked to playlist
        cursor.execute(
            "DELETE FROM playlist_tracks WHERE playlist_id = ?",
            (playlist_id,)
        )

        # Remove playlist itself
        cursor.execute(
            "DELETE FROM playlists WHERE playlist_id = ?",
            (playlist_id,)
        )

        self.commit()
        
    # =====================================================
    # SEMANTIC (Emotional Anchors)
    # =====================================================

    def get_anchor_by_name(self, name: str):

        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT anchor_id, name, created_at, updated_at
            FROM emotional_anchors
        """)

        rows = cursor.fetchall()

        for row in rows:
            if row[1].lower() == name.lower():
                return {
                    "anchor_id": row[0],
                    "name": row[1],
                    "created_at": row[2],
                    "updated_at": row[3]
                }

        return None

    def create_anchor(self, anchor_id: str, name: str, created_at: str, updated_at: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO emotional_anchors (anchor_id, name, created_at, updated_at)
            VALUES (?, ?, ?, ?);
        """, (anchor_id, name, created_at, updated_at))
        self.commit()

    def delete_anchor(self, anchor_id: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM emotional_anchors
            WHERE anchor_id = ?;
        """, (anchor_id,))
        self.commit()

    def add_track_to_anchor(self, anchor_id: str, track_id: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO emotional_anchor_tracks (anchor_id, track_id)
            VALUES (?, ?);
        """, (anchor_id, track_id))
        self.commit()

    def get_anchor_tracks(self, anchor_id: str) -> list[str]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT track_id
            FROM emotional_anchor_tracks
            WHERE anchor_id = ?;
        """, (anchor_id,))
        return [r[0] for r in cursor.fetchall()]

    def get_anchor_name(self, anchor_id: str) -> str | None:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name
            FROM emotional_anchors
            WHERE anchor_id = ?;
        """, (anchor_id,))
        row = cursor.fetchone()
        return row[0] if row else None
    
    def get_all_anchors(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT anchor_id, name
            FROM emotional_anchors;
        """)
        rows = cursor.fetchall()
        
        return [
            {
                "anchor_id": row[0],
                "name": row[1]
            }
            for row in rows
        ]
    
# =====================================================
# SYSTEM STATE
# =====================================================

    def get_last_sync(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT last_sync_at
            FROM system_state
            WHERE id = 1;
        """)
        row = cursor.fetchone()
        return row[0] if row else None


    def set_last_sync(self, timestamp: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO system_state (id, last_sync_at)
            VALUES (1, ?)
            ON CONFLICT(id) DO UPDATE SET
                last_sync_at = excluded.last_sync_at;
        """, (timestamp,))
        self.commit()