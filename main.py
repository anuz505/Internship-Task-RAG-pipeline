from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ingestion import router as ingestion_router
from app.api.rag import router as rag_router
from app.db.base import init_db
from app.services.chat_history import close_redis_client
from app.config import settings
from app.logger import logger
from app.models.schemas import HealthCheckResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    logger.info(f"Environment: {settings.app_name} v{settings.app_version}")
    logger.info(f"Vector Store: Pinecone")
    logger.info(f"Embedding Provider: {settings.embedding_provider}")
    logger.info(f"LLM Provider: {settings.llm_provider}")

    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    logger.info("Application startup complete")

    yield

    logger.info("Shutting down application...")
    await close_redis_client()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Production-grade RAG backend with document ingestion, "
        "conversational chat, and interview booking support"
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion_router)
app.include_router(rag_router)


@app.get("/", response_model=HealthCheckResponse)
async def root():
    return HealthCheckResponse(
        status="healthy",
        version=settings.app_version,
        services={
            "database": "postgresql",
            "cache": "redis",
            "vector_store": "pinecone",
            "embedding": settings.embedding_provider,
            "llm": settings.llm_provider,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
