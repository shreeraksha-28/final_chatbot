import os
import logging

import chromadb
from langchain_chroma import Chroma

from rag.embeddings import get_embeddings
from rag.data_loader import load_and_preprocess, get_movie_metadata

logger = logging.getLogger(__name__)

CHROMA_DB_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
)
COLLECTION_NAME = "tmdb_movies"
BATCH_SIZE = 500

_vector_store: Chroma | None = None


def get_vector_store() -> Chroma:
    if _vector_store is None:
        raise RuntimeError("Vector store not initialized. Call initialize_vector_store() first.")
    return _vector_store


def initialize_vector_store() -> None:
    """Build or load the ChromaDB vector store from the TMDB dataset."""
    global _vector_store

    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    embeddings = get_embeddings()

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    existing = [c.name for c in client.list_collections()]

    if COLLECTION_NAME in existing:
        col = client.get_collection(COLLECTION_NAME)
        if col.count() > 100:
            logger.info(f"✅ Loaded existing ChromaDB collection ({col.count()} docs)")
            _vector_store = Chroma(
                client=client,
                collection_name=COLLECTION_NAME,
                embedding_function=embeddings,
            )
            return

    logger.info("🏗️  Building ChromaDB index — this is a one-time process (~2-5 min)...")
    df = load_and_preprocess()

    texts = df["combined_text"].tolist()
    metadatas = [get_movie_metadata(row) for _, row in df.iterrows()]
    ids = [f"movie_{i}" for i in range(len(texts))]

    _vector_store = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )

    total = len(texts)
    for start in range(0, total, BATCH_SIZE):
        end = min(start + BATCH_SIZE, total)
        _vector_store.add_texts(
            texts=texts[start:end],
            metadatas=metadatas[start:end],
            ids=ids[start:end],
        )
        logger.info(f"  Indexed {end}/{total} movies...")

    logger.info("✅ ChromaDB index built and persisted!")


def query_movies(query: str, n_results: int = 10) -> list[dict]:
    """Return the top-n most similar movies to the query string."""
    vs = get_vector_store()
    results = vs.similarity_search_with_score(query, k=n_results)
    return [
        {
            "title": doc.metadata.get("title", "Unknown"),
            "overview": doc.metadata.get("overview", ""),
            "genres": doc.metadata.get("genres", ""),
            "vote_average": doc.metadata.get("vote_average", 0),
            "popularity": doc.metadata.get("popularity", 0),
            "cast": doc.metadata.get("cast", ""),
            "director": doc.metadata.get("director", ""),
            "similarity_score": float(score),
        }
        for doc, score in results
    ]
