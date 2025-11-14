from app.services.vectore_store_adapters.base import (
    Base_Vector_Store,
    Vector_Search_Result,
)
from app.services.vectore_store_adapters.pinecone_adapter import Pinecone_Adapter
from app.config import settings
from app.logger import logger


def get_vector_store() -> Base_Vector_Store:
    if not settings.pinecone_api_key:
        raise ValueError("Pinecone API key is required")
    if not settings.pinecone_environment:
        raise ValueError("Pinecone environment is required")
    logger.info(f"Initializing pinecone vector store: {settings.pinecone_index_name}")

    return Pinecone_Adapter(
        api_key=settings.pinecone_api_key,
        environment=settings.pinecone_environment,
        index_name=settings.pinecone_index_name,
        dimension=settings.embedding_dim,
    )


__all__ = [
    "Base_Vector_Store",
    "Vector_Search_Result",
    "Pinecone_Adapter",
    "get_vector_store",
]
