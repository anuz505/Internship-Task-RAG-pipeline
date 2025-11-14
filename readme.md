# 🤖 RAG Hiring Bot - Your AI-Powered Interview Assistant

> Because manually scheduling interviews is _so_ last decade! 📅✨

Welcome to the RAG (Retrieval-Augmented Generation) Hiring Bot - a production-grade FastAPI backend that doesn't just chat, it _understands_ your documents and can even book interviews for you. Yes, really!

## 🎯 What Does This Thing Do?

Ever wished you had an assistant that could:

- 📄 **Read your documents** (PDFs and text files) like a speed-reading champion
- 🧠 **Remember everything** using vector embeddings (fancy AI memory)
- 💬 **Chat intelligently** about the content with context awareness
- 📆 **Automatically detect and book interviews** from natural conversation
- 🔍 **Find relevant information** faster than you can say "Ctrl+F"

Well, that's exactly what this does! It's like having a super-smart hiring assistant who never sleeps, never forgets, and runs entirely on your machine.

## ✨ Key Features

### 📚 Document Ingestion

- **Upload & Process**: Drag and drop PDFs or text files
- **Smart Chunking**: Choose between:
  - 🔪 **Simple chunking** - Fixed-size pieces (great for consistency)
  - 🧩 **Semantic chunking** - Context-aware splitting (respects sentence/paragraph boundaries)
- **Vector Storage**: Documents get embedded and stored in Pinecone for lightning-fast retrieval

### 💬 Conversational AI

- **Context-Aware Chat**: Ask questions about your documents naturally
- **Memory**: Redis-powered chat history keeps conversations flowing
- **Smart Retrieval**: Only shows you the most relevant content (no filler!)

### 🎯 Interview Booking Magic

- **Natural Language Understanding**: Just say "Book an interview for John at john@email.com on Dec 15 at 2pm"
- **Automatic Extraction**: The bot detects names, emails, dates, and times
- **Database Storage**: All bookings saved in PostgreSQL

### 🏗️ Production-Ready Architecture

- **FastAPI**: Blazing fast async API framework
- **PostgreSQL**: Reliable metadata and booking storage
- **Redis**: Chat history caching for speed
- **Pinecone**: Vector database for semantic search
- **Docker**: One command to rule them all

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (or just use Docker 🐳)
- PostgreSQL (or use Docker Compose)
- Redis (or... you guessed it... Docker Compose)
- API Keys for:
  - [Groq](https://console.groq.com/) - For LLM responses
  - [Cohere](https://cohere.com/) - For embeddings
  - [Pinecone](https://www.pinecone.io/) - For vector storage

### 🐳 The Easy Way (Docker)

```bash
# 1. Clone and navigate to the project
cd "Internship task"

# 2. Create your .env file in the app/ directory
# (See "Environment Setup" section below)

# 3. Fire up everything
docker-compose up --build

# 4. Visit http://localhost:8000/docs
# 🎉 You're live!
```

### 🛠️ The Manual Way (Local Development)

```bash
# 1. Create a virtual environment
python -m venv myvenv
.\myvenv\Scripts\Activate.ps1  # Windows PowerShell
# or: source myvenv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
# Create app/.env with your API keys (see below)

# 4. Start PostgreSQL and Redis
# (Use Docker or install locally)

# 5. Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. Open http://localhost:8000/docs
```

## 🔐 Environment Setup

Create a file `app/.env` with these variables:

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

## 📡 API Endpoints

### 🏠 Health Check

```http
GET /
```

Returns system status and configured services.

### 📥 Document Ingestion

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

### 💬 Chat with Documents

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

**Pro Tip**: To book an interview, just ask naturally:

```json
{
  "query": "Book an interview for Jane Doe at jane@example.com on December 20th at 3 PM"
}
```

### 📅 View Bookings

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

### 🔍 Get Specific Booking

```http
GET /api/bookings/{booking_id}
```

## 🏗️ Architecture

```
┌─────────────┐
│   FastAPI   │ ← Your API Gateway
└──────┬──────┘
       │
   ┌───┴────┬─────────┬──────────┐
   │        │         │          │
┌──▼───┐ ┌─▼────┐ ┌──▼─────┐ ┌──▼────────┐
│ PDFs │ │Redis │ │Postgres│ │ Pinecone  │
│ TXTs │ │Cache │ │   DB   │ │  Vectors  │
└──────┘ └──────┘ └────────┘ └───────────┘
```

**Tech Stack:**

- **FastAPI**: Lightning-fast async Python framework
- **SQLAlchemy**: ORM for PostgreSQL interactions
- **Pinecone**: Vector database for semantic search
- **Cohere**: Embedding generation
- **Groq**: LLM inference (crazy fast!)
- **Redis**: Session & chat history caching
- **Docker**: Containerization for easy deployment

## 📁 Project Structure

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

## 🎮 Usage Examples

### Upload a Document

```bash
curl -X POST "http://localhost:8000/api/ingest" \
  -F "file=@resume.pdf" \
  -F "chunking_type=semantic" \
  -F "split_by=sentence"
```

### Chat About It

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What experience does this candidate have?",
    "session_id": "user-123",
    "top_k": 5
  }'
```

### Book an Interview (Naturally!)

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Schedule an interview with Sarah Johnson at sarah.j@email.com for January 5th at 10:30 AM"
  }'
```

## 🔧 Configuration

All settings are in `app/config.py` and can be overridden via environment variables. Key configurations:

- **Chunking**: Adjust `simple_chunk_size`, `simple_chunk_overlap`
- **Similarity Threshold**: `similarity_threshold` (default: 0.7)
- **Chat Memory**: `chat_memory_ttl`, `max_messages_per_session`
- **Upload Limits**: `max_upload_size`, `allowed_extensions`

## 🐛 Troubleshooting

**Database connection errors?**

- Check your PostgreSQL is running: `docker ps`
- Verify `POSTGRES_HOST` in your .env

**Redis connection issues?**

- Ensure Redis container is up
- Check `REDIS_HOST` and `REDIS_PORT`

**Pinecone errors?**

- Verify your API key is correct
- Ensure the index name matches in Pinecone console
- Check your Pinecone environment region

**LLM not responding?**

- Validate your Groq API key
- Check rate limits on your Groq account

## 🚀 What's Next?

Want to extend this? Here are some ideas:

- 🎨 Add a frontend UI (React, Vue, or Svelte)
- 📧 Send email confirmations for bookings
- 🔒 Add authentication & authorization
- 📊 Build an analytics dashboard
- 🌐 Support more file types (DOCX, HTML, etc.)
- 🧪 Add comprehensive test coverage

## 📝 License

This is an internship task project. Feel free to learn from it, extend it, and make it your own!

## 🙌 Credits

Built with ❤️ using:

- [FastAPI](https://fastapi.tiangolo.com/)
- [Pinecone](https://www.pinecone.io/)
- [Cohere](https://cohere.com/)
- [Groq](https://groq.com/)
- And a lot of coffee ☕

---

**Happy Coding!** 🎉 If you found this useful, star it, share it, or just smile knowing that somewhere, someone automated their interview scheduling. 😊
