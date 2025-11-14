from typing import List, Dict, Any, Tuple
from pinecone import Pinecone, ServerlessSpec
from app.services.vectore_store_adapters.base import (
    Base_Vector_Store,
    Vector_Search_Result,
)
from app.logger import logger


class Pinecone_Adapter(Base_Vector_Store):
    def __init__(self, api_key: str, environment: str, index_name: str, dimension: int):
        self.api_key = api_key
        self.environment = environment
        self.index_name = index_name
        self.dimension = dimension
        self.pc = Pinecone(api_key=api_key)
        self.index = None

    async def initialize(self) -> None:
        try:
            existing_indexes = self.pc.list_indexes().names()

            if self.index_name not in existing_indexes:
                logger.info(f"Creating Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )
                logger.info(f"Pinecone index {self.index_name} created")
            else:
                logger.info(f"Pinecone index {self.index_name} already exists")

            # Connect to index
            self.index = self.pc.Index(self.index_name)

        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            raise

    async def upsert(
        self, vectors: List[Tuple[str, List[float], Dict[str, Any]]]
    ) -> None:
        if not self.index:
            await self.initialize()

        try:
            # Pinecone expects format: [(id, values, metadata), ...]
            upsert_data = [
                (vec_id, values, metadata) for vec_id, values, metadata in vectors
            ]

            batch_size = 100
            for i in range(0, len(upsert_data), batch_size):
                batch = upsert_data[i : i + batch_size]
                self.index.upsert(vectors=batch)

            logger.info(f"Upserted {len(vectors)} vectors to Pinecone")

        except Exception as e:
            logger.error(f"Failed to upsert to Pinecone: {e}")
            raise

    async def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filter_dict: Dict[str, Any] = None,
    ) -> List[Vector_Search_Result]:
        if not self.index:
            await self.initialize()

        try:
            query_params = {
                "vector": query_vector,
                "top_k": top_k,
                "include_metadata": True,
            }

            if filter_dict:
                query_params["filter"] = filter_dict

            response = self.index.query(**query_params)

            results = [
                Vector_Search_Result(
                    id=match.id, score=match.score, metadata=match.metadata or {}
                )
                for match in response.matches
            ]

            logger.info(f"Pinecone search returned {len(results)} results")
            return results

        except Exception as e:
            logger.error(f"Failed to search Pinecone: {e}")
            raise

    async def delete(self, ids: List[str]) -> None:
        if not self.index:
            await self.initialize()

        try:
            self.index.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} vectors from Pinecone")

        except Exception as e:
            logger.error(f"Failed to delete from Pinecone: {e}")
            raise
