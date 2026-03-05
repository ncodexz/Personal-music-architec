from typing import List
from openai import OpenAI


class EmbeddingService:
    """
    Responsible only for generating embeddings.
    Does not know about Pinecone, SQLite, or Graph.
    """

    DEFAULT_MODEL = "text-embedding-3-small"
    DEFAULT_DIMENSION = 1536

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        """
        Initialize the embedding service.

        Args:
            api_key: OpenAI API key.
            model: Embedding model to use.
        """
        if not api_key:
            raise ValueError("OpenAI API key must be provided.")

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding vector for a single text input.
        """
        if not text or not text.strip():
            raise ValueError("Input text must be a non-empty string.")

        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )

        vector = response.data[0].embedding

        if len(vector) != self.DEFAULT_DIMENSION:
            raise ValueError(
                f"Embedding dimension mismatch. "
                f"Expected {self.DEFAULT_DIMENSION}, got {len(vector)}."
            )

        return vector

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embedding vectors for multiple text inputs in a single call.
        """
        if not texts:
            return []

        cleaned_texts = []

        for text in texts:
            if not text or not text.strip():
                raise ValueError("All texts must be non-empty strings.")
            cleaned_texts.append(text.strip())

        response = self.client.embeddings.create(
            model=self.model,
            input=cleaned_texts
        )

        vectors = [item.embedding for item in response.data]

        for vector in vectors:
            if len(vector) != self.DEFAULT_DIMENSION:
                raise ValueError(
                    f"Embedding dimension mismatch. "
                    f"Expected {self.DEFAULT_DIMENSION}, got {len(vector)}."
                )

        return vectors