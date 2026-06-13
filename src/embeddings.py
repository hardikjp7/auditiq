import torch
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-small-en-v1.5"
_model = None

def get_embedding_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading embedding model on: {device}")
        _model = SentenceTransformer(MODEL_NAME, device=device)
        print(f"Embedding model loaded: {MODEL_NAME}")
    return _model

def embed_texts(texts: list, batch_size: int = 32, show_progress: bool = True):
    model = get_embedding_model()
    return model.encode(
        texts, batch_size=batch_size,
        show_progress_bar=show_progress,
        normalize_embeddings=True
    )

def embed_query(query: str):
    model = get_embedding_model()
    return model.encode(
        [f"Represent this sentence for searching relevant passages: {query}"],
        normalize_embeddings=True
    )[0]
