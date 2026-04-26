import logging

logger = logging.getLogger(__name__)

_model = None


def get_embeddings():
    """Singleton HuggingFace embedding model (all-MiniLM-L6-v2)."""
    global _model
    if _model is None:
        logger.info("Loading HuggingFace embedding model (first load may take ~30s)...")
        try:
            # Prefer the non-deprecated langchain-huggingface package
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            # Fallback to langchain-community if not installed yet
            from langchain_community.embeddings import HuggingFaceEmbeddings

        _model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("✅ Embedding model loaded!")
    return _model
