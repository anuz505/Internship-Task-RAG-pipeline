from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
import io
import PyPDF2
from pathlib import Path
from app.models.schemas import Document_INGESTION_RESPONSE
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.logger import logger
from app.config import settings
from app.models.schemas import Fixed_length_Chunk_Config, Semantic_Chunk_Config
from app.services.chunking import get_chunker
from app.services.embed import get_embedding_client
from app.services.vectore_store_adapters import get_vector_store
from uuid import uuid4
from app.services.meta_data import Meta_Data_Store


router = APIRouter(prefix="/api", tags=["ingestion"])


def extract_text_from_pdf(file_content: bytes) -> str:
    pdf_file = io.BytesIO(file_content)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()


def extract_text_from_text(file_content: bytes) -> str:
    return file_content.decode("utf-8")


@router.post("/ingest", response_model=Document_INGESTION_RESPONSE)
async def ingest_document(
    file: UploadFile = File(..., description="PDF or TXT file to ingest"),
    chunking_type: str = Form(
        "simple", description="Chunking strategy: 'simple' or 'semantic'"
    ),
    chunk_size: int = Form(500, description="Chunk size for simple chunking"),
    chunk_overlap: int = Form(50, description="Chunk overlap for simple chunking"),
    split_by: str = Form(
        "sentence",
        description="Split by 'sentence' or 'paragraph' for semantic chunking",
    ),
    max_chunk_size: int = Form(
        1000, description="Max chunk size for semantic chunking"
    ),
    db: AsyncSession = Depends(get_db),
):
    try:
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_extension} not allowed. Allowed types: {settings.allowed_extensions}",
            )
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > settings.max_upload_size:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum allowed size of {settings.max_upload_size} bytes",
            )
        logger.info(f"Processing file: {file.filename} ({file_size} bytes)")
        # Extract text based on file type
        if file_extension == ".pdf":
            text = extract_text_from_pdf(file_content)
        elif file_extension == ".txt":
            text = extract_text_from_text(file_content)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        if not text or not text.strip():
            raise HTTPException(
                status_code=400, detail="No text could be extracted from the file"
            )

        logger.info(f"Extracted {len(text)} characters from {file.filename}")

        if chunking_type == "fixed_len":
            chunking_config = Fixed_length_Chunk_Config(
                chunk_size=chunk_size, chunk_overlap=chunk_overlap
            )
        else:
            chunking_config = Semantic_Chunk_Config(
                split_by=split_by, max_chunk_size=max_chunk_size
            )
        chunker = get_chunker(chunking_config)
        chunks = chunker.chunk(text)
        if not chunks:
            raise HTTPException(
                status_code=400, detail="No chunks were created from the text"
            )
        logger.info(f"Created {len(chunks)} chunks")

        embedding_client = get_embedding_client()
        vector_store = get_vector_store()
        metadata_store = Meta_Data_Store(db)

        await vector_store.initialize()

        upload_dir = Path(settings.upload_directory)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_id = uuid4()
        file_path = upload_dir / f"{file_id}{file_extension}"

        with open(file_path, "wb") as f:
            f.write(file_content)

        if settings.embedding_provider == "cohere":
            embedding_model = "cohere-embed"
        else:
            embedding_model = f"{settings.embedding_provider}-embed"

        document = await metadata_store.create_document(
            filename=file.filename,
            file_path=str(file_path),
            file_size=file_size,
            file_type=file_extension.lstrip("."),
            total_chunks=len(chunks),
            chunking_strategy=chunking_type,
            chunking_config=chunking_config.model_dump(),
            vector_store_type=settings.vector_store_type,
            embedding_model=embedding_model,
        )
        logger.info("Generating embeddings...")
        embeddings = await embedding_client.embed_list_of_text(
            chunks, input_type="search_document"
        )
        vectors = []
        for idx, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{document.id}_{idx}"
            vector_id = f"vec_{chunk_id}"

            await metadata_store.create_chunk(
                chunk_id=chunk_id,
                document_id=document.id,
                chunk_index=idx,
                chunk_text=chunk_text,
                vector_id=vector_id,
                metadata={
                    "filename": file.filename,
                    "document_id": str(document.id),
                },
            )
            vectors.append(
                (
                    vector_id,
                    embedding,
                    {
                        "chunk_id": chunk_id,
                        "chunk_text": chunk_text,
                        "filename": file.filename,
                        "chunk_index": idx,
                        "document_id": str(document.id),
                    },
                )
            )
            logger.info("Storing vectors in Pinecone...")
        await vector_store.upsert(vectors)

        logger.info(f"Successfully ingested document {document.id}")

        return Document_INGESTION_RESPONSE(
            document_id=document.id,
            filename=file.filename,
            total_chunks=len(chunks),
            chunking_strategy=chunking_type,
            vector_store="pinecone",
            created_at=document.created_at,
            message="Document ingested successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ingesting document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to ingest document: {str(e)}"
        )
