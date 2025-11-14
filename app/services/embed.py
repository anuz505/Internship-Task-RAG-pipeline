from typing import List, Protocol
from abc import ABC, abstractmethod
import httpx

from app.config import settings
from app.logger import logger


class Embedding_Protocal(Protocol):
    async def embed_text(self, text: str) -> List[float]: ...
    async def embed_list_of_text(self, text: List[str]) -> List[List[float]]: ...


class Base_Embedding(ABC):
    @abstractmethod
    async def embed_text(self, text: str, input_type: str) -> List[float]:
        pass

    async def embed_list_of_text(
        self, texts: List[str], input_type: str
    ) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embeddig = await self.embed_text(text, input_type=input_type)
            embeddings.append(embeddig)
        return embeddings


# TODO we could add more embedding model from other providers like OpenAI since its not free so I chose this free one.
class Cohere_Embedding(Base_Embedding):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.cohere.ai/v1/embed"
        self.model = "embed-english-v3.0"

    async def embed_text(
        self, text: str, input_type: str = "search_query"
    ) -> List[float]:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "texts": [text],
                    "model": self.model,
                    "input_type": input_type,
                    "embedding_types": ["float"],
                },
                timeout=30.0,
            )
            res.raise_for_status()
            data = res.json()
            embedding = data["embeddings"]["float"][0]
            logger.debug(f"Generated Cohere embeddings of dim {len(embedding)}")
            return embedding

    async def embed_list_of_text(
        self, texts: List[str], input_type: str = "search_document"
    ) -> List[List[float]]:
        if not texts:
            return []

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "texts": texts,
                    "model": self.model,
                    "input_type": input_type,
                    "embedding_types": ["float"],
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            embeddings = data["embeddings"]["float"]
            logger.info(f"Generated {len(embeddings)} Cohere embeddings")
            return embeddings


def get_embedding_client() -> Base_Embedding:
    provider = settings.embedding_provider

    if provider == "cohere":
        if not settings.cohere_api_key:
            raise ValueError("Cohere API key required.")
        return Cohere_Embedding(api_key=settings.cohere_api_key)
