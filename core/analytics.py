


def get_top_tracks_by_recency(repo, limit: int = 10, decay_days: float = 30.0):
    return repo.get_recency_scores(limit, decay_days)


def get_top_tracks_from_album_by_recency(repo, album_name: str, limit: int = 10, decay_days: float = 30.0):
    return repo.get_album_recency_scores(album_name, limit, decay_days)


def get_top_artists_by_recency(repo, limit: int = 10, decay_days: float = 30.0):
    return repo.get_artist_recency_scores(limit, decay_days)


def get_track_engagement_score(repo, track_id: str) -> float:
    rows = repo.get_engagement_scores_for_tracks([track_id])
    return rows[0][1] if rows else 0.0


def rank_tracks_by_engagement(repo, track_ids: list[str]):
    return repo.get_engagement_scores_for_tracks(track_ids)