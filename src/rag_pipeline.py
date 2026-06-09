import faiss
import numpy as np
import pickle
from pathlib import Path
from src.embeddings import embed_texts, embed_query
from src.rule_loader import load_all_rules, load_rules_as_text
from src.utils import Timer

VS_DIR = Path("/workspace/shared/audit_validator/data/vector_store")

def build_faiss_index(rule_texts: list) -> tuple:
    texts = [r["text"] for r in rule_texts]
    with Timer("Embedding rules"):
        embeddings = embed_texts(texts)
    embeddings = np.array(embeddings).astype(np.float32)
    dim   = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    print(f"FAISS index built: {index.ntotal} vectors | dim={dim}")
    return index, rule_texts

def save_index(index, rule_texts: list):
    VS_DIR.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(VS_DIR / "rules.index"))
    with open(VS_DIR / "rule_texts.pkl", "wb") as f:
        pickle.dump(rule_texts, f)
    print(f"Index saved to: {VS_DIR}")

def load_index():
    index      = faiss.read_index(str(VS_DIR / "rules.index"))
    with open(VS_DIR / "rule_texts.pkl", "rb") as f:
        rule_texts = pickle.load(f)
    print(f"Index loaded: {index.ntotal} vectors")
    return index, rule_texts

def retrieve_top_rules(query: str, index, rule_texts: list, top_k: int = 3) -> list:
    query_vec        = embed_query(query).reshape(1, -1).astype(np.float32)
    scores, indices  = index.search(query_vec, top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx != -1:
            r = rule_texts[idx].copy()
            r["similarity_score"] = round(float(score), 4)
            results.append(r)
    return results

def index_exists() -> bool:
    return (VS_DIR / "rules.index").exists() and (VS_DIR / "rule_texts.pkl").exists()