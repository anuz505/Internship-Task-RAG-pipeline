# here is al the pydantic models for validation
import datetime
from pydantic import BaseModel, Field, EmailStr
from typing import Literal, Optional
from uuid import UUID, uuid4


# chunks
class ChunkingStrategy(BaseModel):
    type: Literal["fixed_len", "semantic"] = Field(description="type of chunk strategy")


class Fixed_length_Chunk_Config(ChunkingStrategy):
    type: Literal["fixed_len"] = "fixed_len"
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)


class Semantic_Chunk_Config(ChunkingStrategy):
    type: Literal["semantic"] = "semantic"
    split_by: Literal["sentence", "paragraph"] = Field(default="sentence")
    max_chunk_size: Optional[int] = Field(default=1000, ge=200)


# llm or Rag schemas


class ChatMessage(BaseModel):
    role: Literal["user", "system", "assistant"] = Field(description="Message role")
    content: str = Field(description="message content or text to llm")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Booking Schema
class Booking_Info(BaseModel):
    name: Optional[str] = Field(default=None, description="Candidate name")
    email: Optional[EmailStr] = Field(default=None, description="Candidate email")
    date: Optional[str] = Field(default=None, description="Interview date (YYYY-MM-DD)")
    time: Optional[str] = Field(default=None, description="Interview time (HH:MM)")
    additional_notes: Optional[str] = Field(
        default=None, description="Additional notes"
    )


class BookingRequest(BaseModel):
    """Request to create a booking."""

    name: str = Field(description="Candidate name", min_length=1)
    email: EmailStr = Field(description="Candidate email")
    date: str = Field(description="Interview date (YYYY-MM-DD)")
    time: str = Field(description="Interview time (HH:MM)")
    session_id: Optional[UUID] = Field(
        default=None, description="Associated chat session"
    )
    additional_notes: Optional[str] = Field(default=None)


class BookingResponse(BaseModel):
    """Response for booking creation/retrieval."""

    booking_id: UUID = Field(description="Booking UUID")
    name: str
    email: str
    date: str
    time: str
    session_id: Optional[UUID] = None
    additional_notes: Optional[str] = None
    status: Literal["pending", "confirmed", "cancelled"] = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class BookingListResponse(BaseModel):
    """Response for listing bookings."""

    bookings: list[BookingResponse]
    total: int = Field(description="Total number of bookings")


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(description="API version")
    services: dict[str, str] = Field(
        default_factory=dict, description="Service status checks"
    )
