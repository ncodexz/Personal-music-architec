from typing import List
from core.repository import Repository
from core.semantic.embeddings import EmbeddingService
from core.semantic.pinecone_indexer import PineconeIndexer


class SemanticService:
    """
    Orchestrates semantic indexing logic.
    Knows about Repository, EmbeddingService, and PineconeIndexer.
    Does not know about Graph or Session.
    """

    def __init__(
        self,
        repo: Repository,
        embedding_service: EmbeddingService,
        pinecone_indexer: PineconeIndexer
    ):
        self.repo = repo
        self.embedding_service = embedding_service
        self.pinecone_indexer = pinecone_indexer

    def _build_track_text(self, name: str, artists: List[str]) -> str:
        artist_str = ", ".join(artists)
        return f"{name} - {artist_str}"

    def index_all_tracks(self, batch_size: int = 100) -> int:

        tracks = self.repo.get_all_tracks_with_artists()

        if not tracks:
            return 0

        total_indexed = 0

        for i in range(0, len(tracks), batch_size):
            batch = tracks[i:i + batch_size]

            texts = []
            vector_payload = []

            for track in batch:
                text = self._build_track_text(
                    track["name"],
                    track["artists"]
                )
                texts.append(text)

            embeddings = self.embedding_service.embed_batch(texts)

            for track, vector in zip(batch, embeddings):
                vector_payload.append({
                    "id": f"track_{track['track_id']}",
                    "values": vector,
                    "metadata": {
                        "type": "track",
                        "track_id": track["track_id"],
                        "name": track["name"],
                        "artists": track["artists"]
                    }
                })

            self.pinecone_indexer.upsert_batch(vector_payload)
            total_indexed += len(batch)

        return total_indexed

    def index_tracks(self, track_ids: List[str], batch_size: int = 100) -> int:

        if not track_ids:
            return 0

        tracks = self.repo.get_tracks_with_artists(track_ids)

        if not tracks:
            return 0

        total_indexed = 0

        for i in range(0, len(tracks), batch_size):
            batch = tracks[i:i + batch_size]

            texts = []
            vector_payload = []

            for track in batch:
                text = self._build_track_text(
                    track["name"],
                    track["artists"]
                )
                texts.append(text)

            embeddings = self.embedding_service.embed_batch(texts)

            for track, vector in zip(batch, embeddings):

                vector_payload.append({
                    "id": f"track_{track['track_id']}",
                    "values": vector,
                    "metadata": {
                        "type": "track",
                        "track_id": track["track_id"],
                        "name": track["name"],
                        "artists": track["artists"]
                    }
                })

            self.pinecone_indexer.upsert_batch(vector_payload)
            total_indexed += len(batch)

        return total_indexed

    def recalculate_anchor(self, anchor_id: str) -> bool:

        track_ids = self.repo.get_anchor_tracks(anchor_id)

        if not track_ids:
            return False

        pinecone_ids = [f"track_{tid}" for tid in track_ids]

        response = self.pinecone_indexer.fetch_by_ids(pinecone_ids)
        vectors_data = response.get("vectors", {})

        if not vectors_data:
            return False

        vectors = []
        for vid in pinecone_ids:
            if vid in vectors_data:
                vectors.append(vectors_data[vid]["values"])

        if not vectors:
            return False

        dimension = len(vectors[0])
        centroid = [0.0] * dimension

        for vector in vectors:
            for i in range(dimension):
                centroid[i] += vector[i]

        count = len(vectors)
        centroid = [value / count for value in centroid]

        anchor_name = self.repo.get_anchor_name(anchor_id)

        if not anchor_name:
            return False

        self.pinecone_indexer.upsert_vector(
            vector_id=f"anchor_{anchor_id}",
            values=centroid,
            metadata={
                "type": "anchor",
                "anchor_id": anchor_id,
                "name": anchor_name
            }
        )

        return True
    
    def search_similar_to_anchor(self, anchor_id: str, top_k: int = 50):

        response = self.pinecone_indexer.fetch_by_ids(
            [f"anchor_{anchor_id}"]
        )

        vectors = response.get("vectors", {})
        anchor_vector = vectors.get(f"anchor_{anchor_id}")

        if not anchor_vector:
            return []

        query = self.pinecone_indexer.query_similar(
            values=anchor_vector["values"],
            top_k=top_k,
            filter={"type": "track"}
        )

        matches = query.get("matches", [])

        return [
            match["metadata"]
            for match in matches
            if match.get("metadata")
        ]
    
    def search_by_text(self, text: str, top_k: int = 50):

        vector = self.embedding_service.embed_text(text)

        results = self.pinecone_indexer.query_similar(
            values=vector,
            top_k=top_k,
            filter={"type": "track"}
        )

        matches = results.get("matches", [])

        return [
            {
                "track_id": m["metadata"]["track_id"],
                "score": m["score"]
            }
            for m in matches
        ]