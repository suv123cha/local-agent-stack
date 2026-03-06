"""
AI Agent System – FastAPI Entry Point
======================================
Bootstraps the application, registers routes, and ensures
all memory backends are initialised before accepting traffic.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.chat import router as chat_router
from memory.vector_memory import init_vector_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hooks."""
    log.info("Initialising vector store …")
    await init_vector_store()
    log.info("System ready ✓")
    yield
    log.info("Shutting down …")


app = FastAPI(
    title="AI Agent System",
    version="1.0.0",
    description="Multi-agent orchestrator with memory, tools, planning and reflection.",
    lifespan=lifespan,
)

# Allow the Vite dev server and any local origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
