# scripts/semantic-search.py
from sentence_transformers import SentenceTransformer
import numpy as np
import json
from pathlib import Path

model = SentenceTransformer('all-MiniLM-L6-v2')

def build_index():
    """Build embeddings for all documentation."""
    docs = []
    for md_file in Path("docs").rglob("*.md"):
        with open(md_file) as f:
            content = f.read()
        docs.append({
            "path": str(md_file),
            "content": content,
            "embedding": model.encode(content).tolist()
        })

    with open("docs/_search_index.json", "w") as f:
        json.dump(docs, f)

def search(query, top_k=5):
    """Search documentation semantically."""
    with open("docs/_search_index.json") as f:
        docs = json.load(f)

    query_embedding = model.encode(query)

    scores = []
    for doc in docs:
        score = np.dot(query_embedding, doc["embedding"])
        scores.append((score, doc["path"]))

    scores.sort(reverse=True)
    return scores[:top_k]