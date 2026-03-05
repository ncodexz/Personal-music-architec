from typing import List, Dict, Any
from pinecone import Pinecone


class PineconeIndexer:
    """
    Responsible only for interacting with Pinecone.
    Does not know about tracks, anchors, SQLite, or Graph.
    """

    def __init__(
        self,
        api_key: str,
        index_name: str,
        dimension: int = 1536,
    ):
        if not api_key:
            raise ValueError("Pinecone API key must be provided.")

        self.dimension = dimension
        self.index_name = index_name

        self.pc = Pinecone(api_key=api_key)
        self.index = self.pc.Index(index_name)

    def upsert_vector(
        self,
        vector_id: str,
        values: List[float],
        metadata: Dict[str, Any]
    ) -> None:

        if len(values) != self.dimension:
            raise ValueError(
                f"Vector dimension mismatch. "
                f"Expected {self.dimension}, got {len(values)}."
            )

        self.index.upsert(
            vectors=[
                {
                    "id": vector_id,
                    "values": values,
                    "metadata": metadata
                }
            ]
        )

    def upsert_batch(
        self,
        vectors: List[Dict[str, Any]]
    ) -> None:

        for vector in vectors:
            if len(vector["values"]) != self.dimension:
                raise ValueError(
                    f"Vector dimension mismatch for id {vector['id']}."
                )

        self.index.upsert(vectors=vectors)

    def query_similar(
        self,
        values: List[float],
        top_k: int = 10,
        filter: Dict[str, Any] | None = None
    ):

        if len(values) != self.dimension:
            raise ValueError(
                f"Query vector dimension mismatch. "
                f"Expected {self.dimension}, got {len(values)}."
            )

        return self.index.query(
            vector=values,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )

    def fetch_by_ids(self, ids: List[str]) -> Dict[str, Any]:

        if not ids:
            return {}

        return self.index.fetch(ids=ids)