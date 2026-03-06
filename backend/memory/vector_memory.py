"""
memory/vector_memory.py
=======================
Long-term semantic memory backed by Qdrant.

Memories are embedded with sentence-transformers and stored as
384-dimensional float32 vectors.  At query time the top-k most
similar memories are retrieved and returned as plain strings so
they can be injected into the LLM prompt.
"""

import logging
import os
import uuid

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    PointStruct,
    VectorParams,
)
from sentence_transformers import SentenceTransformer

log = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "agent_memories"
VECTOR_DIM = 384  # all-MiniLM-L6-v2 output dimension

# Module-level singletons – initialised once in lifespan
_encoder: SentenceTransformer | None = None
_qdrant: AsyncQdrantClient | None = None


def _get_encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        log.info("Loading sentence-transformer model …")
        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
    return _encoder


def _get_client() -> AsyncQdrantClient:
    global _qdrant
    if _qdrant is None:
        _qdrant = AsyncQdrantClient(url=QDRANT_URL)
    return _qdrant


async def init_vector_store() -> None:
    """Create the Qdrant collection if it does not already exist."""
    client = _get_client()
    existing = await client.get_collections()
    names = [c.name for c in existing.collections]
    if COLLECTION not in names:
        await client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        log.info("Created Qdrant collection '%s'.", COLLECTION)
    else:
        log.info("Qdrant collection '%s' already exists.", COLLECTION)


async def store_memory(text: str, metadata: dict | None = None) -> str:
    """
    Embed *text* and upsert it into Qdrant.
    Returns the generated point ID.
    """
    encoder = _get_encoder()
    vector = encoder.encode(text).tolist()
    point_id = str(uuid.uuid4())

    payload = {"text": text}
    if metadata:
        payload.update(metadata)

    client = _get_client()
    await client.upsert(
        collection_name=COLLECTION,
        points=[PointStruct(id=point_id, vector=vector, payload=payload)],
    )
    log.debug("Stored memory: '%s…'", text[:60])
    return point_id


async def search_memories(query: str, top_k: int = 5, score_threshold: float = 0.35) -> list[str]:
    """
    Retrieve the *top_k* memories most semantically similar to *query*.
    Only results above *score_threshold* are returned.
    """
    encoder = _get_encoder()
    query_vector = encoder.encode(query).tolist()

    client = _get_client()
    hits = await client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k,
        score_threshold=score_threshold,
    )

    results = [hit.payload.get("text", "") for hit in hits if hit.payload]
    log.debug("Retrieved %d memories for query '%s…'", len(results), query[:40])
    return results
