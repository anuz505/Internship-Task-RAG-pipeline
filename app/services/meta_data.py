from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db_models import Document, DocumentChunk, InterviewBooking, ChatSession
from app.logger import logger


class Meta_Data_Store:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document(
        self,
        filename: str,
        file_path: Optional[str],
        file_size: Optional[int],
        file_type: str,
        total_chunks: int,
        chunking_strategy: str,
        chunking_config: dict,
        vector_store_type: str,
        embedding_model: str,
    ) -> Document:
        document = Document(
            filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            total_chunks=total_chunks,
            chunking_strategy=chunking_strategy,
            chunking_config=chunking_config,
            vector_store_type=vector_store_type,
            embedding_model=embedding_model,
        )
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def create_chunk(
        self,
        chunk_id: str,
        document_id: UUID,
        chunk_index: int,
        chunk_text: str,
        vector_id: str,
        metadata: Optional[dict] = None,
    ) -> DocumentChunk:
        chunk = DocumentChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            chunk_index=chunk_index,
            chunk_text=chunk_text,
            vector_id=vector_id,
            chunk_metadata=metadata,
        )

        self.db.add(chunk)
        await self.db.flush()
        return chunk

    async def get_document_by_id(self, document_id: UUID) -> Optional[Document]:
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def get_chunks_by_document_id(self, document_id: UUID) -> List[DocumentChunk]:
        result = await self.db.execute(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def get_chunk_by_vector_id(self, vector_id: str) -> Optional[DocumentChunk]:

        result = await self.db.execute(
            select(DocumentChunk).where(DocumentChunk.vector_id == vector_id)
        )
        return result.scalar_one_or_none()

    async def delete_document(self, document_id: UUID) -> bool:

        result = await self.db.execute(
            delete(Document).where(Document.id == document_id)
        )

        deleted = result.rowcount > 0
        if deleted:
            logger.info(f"Deleted document: {document_id}")

        return deleted

    async def get_or_create_chat_session(self, session_id: UUID) -> ChatSession:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            session = ChatSession(session_id=session_id)
            self.db.add(session)
            await self.db.flush()
            await self.db.refresh(session)
            logger.info(f"Created chat session: {session_id}")

        return session

    async def create_booking(
        self,
        name: str,
        email: str,
        date: str,
        time: str,
        session_id: Optional[UUID] = None,
        additional_notes: Optional[str] = None,
    ) -> InterviewBooking:
        # Ensure chat session exists if session_id is provided
        if session_id:
            await self.get_or_create_chat_session(session_id)

        booking = InterviewBooking(
            name=name,
            email=email,
            date=date,
            time=time,
            session_id=session_id,
            additional_notes=additional_notes,
            status="pending",
        )

        self.db.add(booking)
        await self.db.flush()
        await self.db.refresh(booking)

        logger.info(f"Created booking: {booking.id} for {name}")
        return booking

    async def get_booking_by_id(self, booking_id: UUID) -> Optional[InterviewBooking]:
        result = await self.db.execute(
            select(InterviewBooking).where(InterviewBooking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def get_all_bookings(self) -> List[InterviewBooking]:
        result = await self.db.execute(
            select(InterviewBooking).order_by(InterviewBooking.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_booking_status(
        self, booking_id: UUID, status: str
    ) -> Optional[InterviewBooking]:
        booking = await self.get_booking_by_id(booking_id)
        if booking:
            booking.status = status
            await self.db.flush()
            await self.db.refresh(booking)
            logger.info(f"Updated booking {booking_id} status to {status}")

        return booking
