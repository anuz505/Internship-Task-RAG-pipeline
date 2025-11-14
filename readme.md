# RAG Hiring Bot

A FastAPI-based system that lets you chat with your documents and automatically handles interview bookings through natural conversation.

## Overview

I built this to solve a simple problem: sifting through hiring documents and manually scheduling interviews gets tedious. This bot ingests your PDFs and text files, lets you ask questions about them, and can automatically extract and book interview details when you mention them in conversation.

The whole thing uses RAG (Retrieval-Augmented Generation) - basically it chunks your documents, converts them to vector embeddings, and retrieves relevant pieces when you ask questions. Then it feeds that context to an LLM to generate responses.

## What It Does

**Document Processing**

- Upload PDFs or text files
- Choose how to chunk them (fixed-size or semantic - semantic tries to respect sentence/paragraph boundaries)
- Everything gets embedded using Cohere and stored in Pinecone

**Conversational Search**

- Ask questions about your documents in plain English
- The system finds relevant chunks and uses them to generate answers
- Chat history is saved in Redis so it remembers your conversation

**Auto Interview Booking**

- Just mention booking details in chat like "Book an interview for John at john@email.com on Dec 15 at 2pm"
- It extracts the name, email, date, and time automatically
- Saves everything to PostgreSQL

**Stack**

- FastAPI for the API
- PostgreSQL for storing document metadata and bookings
- Redis for caching chat sessions
- Pinecone for vector search
- Cohere for embeddings
- Groq for the LLM (using Llama 3.3)
- Docker Compose to run everything

## Getting Started

**What you'll need:**

- Python 3.11 or higher (or just use Docker)
- API keys from Groq, Cohere, and Pinecone
- PostgreSQL and Redis if running locally

**Quick setup with Docker:**

```bash
cd "Internship task"

# Create app/.env with your config (see below)

docker-compose up --build

# API docs at http://localhost:8000/docs
```

**Running locally:**

```bash
# Virtual environment
python -m venv myvenv
.\myvenv\Scripts\Activate.ps1  # Windows
# source myvenv/bin/activate    # Linux/Mac

pip install -r requirements.txt

# Set up app/.env with your keys

# Start PostgreSQL and Redis

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Setup

Create `app/.env`:

```env
# Application Settings
APP_NAME=RAG Hiring Bot
DEBUG=True
LOG_LEVEL=INFO

# API Keys (Get these from respective providers)
GROQ_API_KEY=your_groq_api_key_here
COHERE_API_KEY=your_cohere_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-east-1-aws  # or your region
PINECONE_INDEX_NAME=rag-documents

# Database (adjust if not using Docker)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=rag_db

# Redis (adjust if not using Docker)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# LLM Configuration
GROQ_CHAT_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000

# Embedding Configuration
EMBEDDING_PROVIDER=cohere
EMBEDDING_DIM=1024

# Vector Store
VECTOR_STORE_TYPE=pinecone

# File Upload Settings
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=[".pdf", ".txt"]
UPLOAD_DIRECTORY=./uploads
```

## API Endpoints

### Health Check

```http
GET /
```

### Upload Documents

```http
POST /api/ingest
Content-Type: multipart/form-data

Parameters:
- file: PDF or TXT file
- chunking_type: "simple" or "semantic"
- chunk_size: 500 (for simple chunking)
- chunk_overlap: 50 (for simple chunking)
- split_by: "sentence" or "paragraph" (for semantic)
- max_chunk_size: 1000 (for semantic)

Response:
{
  "document_id": "uuid",
  "filename": "document.pdf",
  "total_chunks": 42,
  "chunking_strategy": "simple",
  "vector_store": "pinecone",
  "created_at": "2025-11-14T...",
  "message": "Document ingested successfully"
}
```

### Chat

```http
POST /api/chat
Content-Type: application/json

{
  "query": "What are the company benefits?",
  "session_id": "optional-session-id",
  "top_k": 5
}

Response:
{
  "session_id": "abc-123",
  "query": "What are the company benefits?",
  "answer": "Based on the documents...",
  "retrieved_contexts": [...],
  "booking_detected": false,
  "booking_id": null
}
```

To book an interview, just mention it:

```json
{
  "query": "Book an interview for Jane Doe at jane@example.com on December 20th at 3 PM"
}
```

### Bookings

```http
GET /api/bookings

Response:
{
  "bookings": [
    {
      "booking_id": "uuid",
      "name": "Jane Doe",
      "email": "jane@example.com",
      "date": "2025-12-20",
      "time": "15:00:00",
      "status": "pending",
      ...
    }
  ],
  "total": 1
}
```

```http
GET /api/bookings/{booking_id}
```

## Architecture

The flow is pretty straightforward:

1. **Document Upload** → Chunks text → Generates embeddings → Stores in Pinecone
2. **Chat Query** → Embeds query → Searches Pinecone for similar chunks → Feeds to LLM → Returns answer
3. **Session History** → Stored in Redis for context
4. **Bookings** → Extracted by LLM, saved to PostgreSQL

Built with FastAPI, PostgreSQL, Redis, Pinecone, Cohere, and Groq. Everything runs in Docker containers for easy deployment.

## Project Structure

```
.
├── app/
│   ├── api/
│   │   ├── ingestion.py    # Document upload & processing
│   │   └── rag.py          # Chat & booking endpoints
│   ├── db/
│   │   ├── base.py         # Database initialization
│   │   └── session.py      # DB session management
│   ├── models/
│   │   ├── db_models.py    # SQLAlchemy models
│   │   └── schemas.py      # Pydantic schemas
│   ├── services/           # Business logic
│   ├── config.py           # Configuration management
│   └── logger.py           # Logging setup
├── uploads/                # Uploaded files storage
├── main.py                 # Application entry point
├── docker-compose.yml      # Multi-container setup
├── Dockerfile              # Container definition
└── requirements.txt        # Python dependencies
```

## Examples

**Upload a document:**

```bash
curl -X POST "http://localhost:8000/api/ingest" \
  -F "file=@resume.pdf" \
  -F "chunking_type=semantic" \
  -F "split_by=sentence"
```

**Ask questions:**

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What experience does this candidate have?",
    "session_id": "user-123",
    "top_k": 5
  }'
```

**Book an interview:**

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Schedule an interview with Sarah Johnson at sarah.j@email.com for January 5th at 10:30 AM"
  }'
```

## Configuration

Settings in `app/config.py` can be overridden with environment variables:

- Chunking: `simple_chunk_size`, `simple_chunk_overlap`
- Similarity threshold: `similarity_threshold` (default: 0.7)
- Chat memory: `chat_memory_ttl`, `max_messages_per_session`
- File uploads: `max_upload_size`, `allowed_extensions`

## Possible Improvements

Some things I'd add if I had more time:

- A proper frontend instead of just API docs
- Email notifications when interviews are booked
- User authentication
- Support for more file types (DOCX, HTML, etc.)
- Better error handling and logging
- Tests

## License

MIT - use it however you want.
