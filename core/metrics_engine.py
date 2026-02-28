# core/metrics_engine.py


def update_track_metrics(repo, decay_days: float = 30.0) -> int:

    play_data = repo.get_play_history_aggregated(decay_days)

    if not play_data:
        return 0

    max_recency = max(row[1] for row in play_data)
    max_plays = max(row[2] for row in play_data)

    updated = 0

    for track_id, recency_score, total_plays in play_data:

        recency_norm = recency_score / max_recency if max_recency else 0
        plays_norm = total_plays / max_plays if max_plays else 0

        popularity = repo.get_track_popularity(track_id)
        popularity_norm = popularity / 100.0

        engagement_score = (
            recency_norm * 0.6 +
            plays_norm * 0.3 +
            popularity_norm * 0.1
        )

        repo.upsert_track_metrics(
            track_id=track_id,
            recency_score=recency_score,
            popularity=popularity,
            engagement_score=engagement_score
        )

        updated += 1

    repo.commit_batch()

    return updated