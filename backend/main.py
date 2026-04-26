import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rag.vector_store import initialize_vector_store
from routes.chat import router as chat_router
from routes.recommend import router as recommend_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Movie Recommender API...")
    logger.info("📦 Initializing vector store (may take a few minutes on first run)...")
    initialize_vector_store()
    logger.info("✅ Vector store ready!")
    yield
    logger.info("🛑 Shutting down...")


app = FastAPI(
    title="🎬 Movie Recommender Chatbot API",
    description="AI-powered conversational movie recommendation system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/chat", tags=["Chat Flow"])
app.include_router(recommend_router, tags=["Recommendations"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "message": "Movie Recommender API is running!"}
