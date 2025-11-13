from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional
from pydantic import Field


class Settings(BaseSettings):
    # Application settings
    app_name: str = "RAG Hiring Bot with Doc ingestion and Chat API"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )
    simple_chunk_size: int = Field(
        default=500, description="Simple chunking character size"
    )
    simple_chunk_overlap: int = Field(default=50, description="Simple chunking overlap")

    embedding_provider: Literal["cohere"] = Field(
        default="cohere", description="embedding provider"
    )
    embedding_dim: int = Field(default=1024, description="Embedding Vector Dimension")
    vector_store_type: Literal["pinecone"] = Field(
        default="pinecone", description="pinecone for database"
    )
    pinecone_api = Optional[str] = Field(
        default=None, description="api key for pinecone"
    )
    pinecone_environment: Optional[str] = Field(
        default=None, description="Pinecone environment"
    )
    pinecone_index_name: str = Field(
        default="rag-documents", description="Pinecone index name"
    )

    cohere_api_key: str = Field(default=None, description="Cohere API key")

    groq_api_key: str = Field(default=None, description="Groq api key ")

    groq_chat_model: str = Field(
        default="llama-3.3-70b-versatile", description="Groq chat model"
    )
    llm_temperature: float = Field(default=0.7, description="LLM temperature")
    llm_max_tokens: int = Field(default=1000, description="LLM max tokens")
    llm_provider: Literal["groq"] = Field(
        default="groq", description="LLM provider for RAG"
    )

    chat_memory_ttl: int = Field(default=3600, description="chat memory TTL in seconds")

    max_messages_per_session: int = Field(
        default=20, description="Max messages to keep in memory"
    )

    # DB settings
    postgres_user: str = Field(default="postgres", description="PostgreSQL username")
    postgres_password: str = Field(
        default="postgres", description="PostgreSQL password"
    )
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_db: str = Field(default="rag_db", description="PostgreSQL database name")

    @property
    def database_url(self) -> str:
        """Construct async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

        # Redis settings

    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")

    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = Settings()
