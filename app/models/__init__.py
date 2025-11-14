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
    DocumentUploadRequest,
    Document_INGESTION_RESPONSE,
    ChatRequest,
    ChatResponse,
    RetrievedContext,
    Booking_Info,
    BookingRequest,
    BookingResponse,
    BookingListResponse,
    HealthCheckResponse,
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
    "DocumentUploadRequest",
    "Document_INGESTION_RESPONSE",
    "ChatRequest",
    "ChatResponse",
    "ChatMessageSchema",
    "RetrievedContext",
    "Booking_Info",
    "BookingRequest",
    "Booking_Info",
    "BookingResponse",
    "BookingListResponse",
    "HealthCheckResponse",
]
