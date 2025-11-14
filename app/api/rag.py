from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    RetrievedContext,
    BookingResponse,
    BookingListResponse,
)
from app.services.embed import get_embedding_client
from app.services.vectore_store_adapters import get_vector_store
from app.services.chat_history import get_chat_memory, ChatMemoryService
from app.services.LLM import get_llm_client
from app.services.meta_data import Meta_Data_Store
from app.db.session import get_db
from app.config import settings
from app.logger import logger


router = APIRouter(prefix="/api", tags=["rag"])


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    chat_memory: ChatMemoryService = Depends(get_chat_memory),
):
    try:
        logger.info(f"Processing chat request for session {request.session_id}")

        embedding_client = get_embedding_client()
        vector_store = get_vector_store()
        llm_client = get_llm_client()
        metadata_store = Meta_Data_Store(db)

        await vector_store.initialize()

        chat_history = await chat_memory.get_recent_messages(
            session_id=request.session_id, count=10
        )

        await chat_memory.add_message(
            session_id=request.session_id, role="user", content=request.query
        )

        logger.info("Generating query embedding...")
        query_embedding = await embedding_client.embed_text(
            request.query, input_type="search_query"
        )

        logger.info(f"Searching for top {request.top_k} similar vectors...")
        search_results = await vector_store.search(
            query_vector=query_embedding, top_k=request.top_k
        )

        filtered_results = [
            result
            for result in search_results
            if result.score >= settings.similarity_threshold
        ]

        logger.info(
            f"Found {len(filtered_results)} results above threshold {settings.similarity_threshold}"
        )

        retrieved_contexts = []
        context_text = ""

        for result in filtered_results:
            retrieved_contexts.append(
                RetrievedContext(
                    chunk_id=result.metadata.get("chunk_id", ""),
                    chunk_text=result.metadata.get("chunk_text", ""),
                    filename=result.metadata.get("filename", ""),
                    similarity_score=result.score,
                    metadata=result.metadata,
                )
            )
            context_text += f"\n\n{result.metadata.get('chunk_text', '')}"

        if not context_text.strip():
            context_text = "No relevant context found in the document database."

        logger.info("Generating LLM response...")
        answer = await llm_client.generate_response(
            query=request.query, context=context_text, chat_history=chat_history
        )

        await chat_memory.add_message(
            session_id=request.session_id, role="assistant", content=answer
        )

        booking_detected = False
        booking_id = None

        booking_info = await llm_client.extract_booking_info(request.query)

        if booking_info and any(
            [
                booking_info.name,
                booking_info.email,
                booking_info.date,
                booking_info.time,
            ]
        ):
            if (
                booking_info.name
                and booking_info.email
                and booking_info.date
                and booking_info.time
            ):
                logger.info(f"Booking detected for {booking_info.name}")
                booking_detected = True

                booking = await metadata_store.create_booking(
                    name=booking_info.name,
                    email=booking_info.email,
                    date=booking_info.date,
                    time=booking_info.time,
                    session_id=request.session_id,
                    additional_notes=booking_info.additional_notes,
                )
                booking_id = booking.id

                answer += (
                    f"\n\n✅ Interview booking created successfully!\n"
                    f"- Name: {booking_info.name}\n"
                    f"- Email: {booking_info.email}\n"
                    f"- Date: {booking_info.date}\n"
                    f"- Time: {booking_info.time}\n"
                    f"- Booking ID: {booking_id}"
                )

        return ChatResponse(
            session_id=request.session_id,
            query=request.query,
            answer=answer,
            retrieved_contexts=retrieved_contexts,
            booking_detected=booking_detected,
            booking_id=booking_id,
        )

    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to process chat request: {str(e)}"
        )


@router.get("/bookings", response_model=BookingListResponse)
async def get_bookings(db: AsyncSession = Depends(get_db)):
    try:
        metadata_store = Meta_Data_Store(db)
        bookings = await metadata_store.get_all_bookings()

        booking_responses = [
            BookingResponse(
                booking_id=booking.id,
                name=booking.name,
                email=booking.email,
                date=booking.date,
                time=booking.time,
                session_id=booking.session_id,
                additional_notes=booking.additional_notes,
                status=booking.status,
                created_at=booking.created_at,
                updated_at=booking.updated_at,
            )
            for booking in bookings
        ]

        return BookingListResponse(
            bookings=booking_responses, total=len(booking_responses)
        )

    except Exception as e:
        logger.error(f"Error fetching bookings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch bookings: {str(e)}"
        )


@router.get("/bookings/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        metadata_store = Meta_Data_Store(db)
        booking = await metadata_store.get_booking_by_id(booking_id)

        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        return BookingResponse(
            booking_id=booking.id,
            name=booking.name,
            email=booking.email,
            date=booking.date,
            time=booking.time,
            session_id=booking.session_id,
            additional_notes=booking.additional_notes,
            status=booking.status,
            created_at=booking.created_at,
            updated_at=booking.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching booking: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch booking: {str(e)}"
        )
