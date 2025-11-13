"""Models package initialization."""

from app.models.db_models import (
    Base,
    Document,
    DocumentChunk,
    ChatSession,
    ChatMessage,
    InterviewBooking,
)

from app.models.schemas import (
    ChunkingStrategy,
    Fixed_length_Chunk_Config,
    Semantic_Chunk_Config,
    ChatMessage as ChatMessageSchema,
    Booking_Info,
)

__all__ = [
    # DB Models
    "Base",
    "Document",
    "DocumentChunk",
    "ChatSession",
    "ChatMessage",
    "InterviewBooking",
    # Schemas
    "ChunkingStrategy",
    "Fixed_length_Chunk_Config",
    "Semantic_Chunk_Config",
    "ChatMessageSchema",
    "Booking_Info",
]
