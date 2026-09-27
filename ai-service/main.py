"""
Main FastAPI Application for BoardRoom AI RAG & Question Generation Subsystem.
"""

import sys
from pathlib import Path

# Add ai-service to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.routes import router as api_router, _retriever
from api.evaluation_routes import router as evaluation_router

app = FastAPI(
    title="BoardRoom AI — RAG & Question Generation Service",
    description="Intelligent RAG pipeline, structured interview question generator, and explainable relevance evaluator.",
    version="1.0.0"
)

# CORS setup for seamless Node backend & React frontend integration
# Explicit origins configured via settings.allowed_origins_list so allow_credentials=True is compliant with browser specs
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(evaluation_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Returns service health, loaded chunks count, retrieval mode, and LLM configuration."""
    return {
        "status": "healthy",
        "service": "BoardRoom AI - RAG & Question Generation Subsystem",
        "chunks_indexed": len(_retriever.chunks),
        "retrieval_mode": _retriever.retrieval_mode,
        "dense_embeddings_active": _retriever.dense_embeddings_active,
        "llm_configured": bool(settings.GEMINI_API_KEY),
        "llm_model": settings.DEFAULT_LLM_MODEL
    }



if __name__ == "__main__":
    import uvicorn
    print(f"Starting BoardRoom AI RAG Service on {settings.HOST}:{settings.PORT}")
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
