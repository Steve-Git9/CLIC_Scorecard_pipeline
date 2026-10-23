"""Core SDG semantic-similarity classifier, shared by sdg_api.py (Flask) and app/viewer.py.

Classifies a document's text against the 17 UN Sustainable Development Goals
by cosine similarity between sentence-transformer embeddings, chunk by chunk.
The embedding model runs locally; no document content leaves the machine.
"""

from __future__ import annotations

import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
SDGS_PATH = Path(__file__).with_name("sdgs.json")

CHUNK_SIZE = 500
TOP_N_SDGS = 5
MATCH_THRESHOLD = 0.35


def load_sdgs(path: Path = SDGS_PATH) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_model(model_name: str = MODEL_NAME) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def embed_sdgs(model: SentenceTransformer, sdgs: list[dict]):
    texts = [f"\n{s['name']}\n{s['description']}\n{s['semantic_profile']}\n" for s in sdgs]
    return model.encode(texts, convert_to_numpy=True)


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]


def classify_document(text: str, model: SentenceTransformer, sdgs: list[dict], sdg_embeddings) -> dict:
    """Score `text` against every SDG. Returns {"sdgs": [top TOP_N_SDGS, best first]}."""
    chunks = chunk_text(text)
    sdg_stats = {s["number"]: {"max_score": 0.0, "matching_chunks": 0} for s in sdgs}

    for chunk in chunks:
        chunk_embedding = model.encode([chunk], convert_to_numpy=True)
        similarities = cosine_similarity(chunk_embedding, sdg_embeddings)[0]

        for idx, score in enumerate(similarities):
            number = sdgs[idx]["number"]
            stats = sdg_stats[number]
            if score > stats["max_score"]:
                stats["max_score"] = float(score)
            if score > MATCH_THRESHOLD:
                stats["matching_chunks"] += 1

    results = []
    for sdg in sdgs:
        number = sdg["number"]
        max_score = sdg_stats[number]["max_score"]
        matching_chunks = sdg_stats[number]["matching_chunks"]
        final_score = 0.8 * max_score + 0.2 * min(matching_chunks / 5, 1)
        results.append({
            "number": number,
            "name": sdg["name"],
            "score": round(final_score, 3),
            "max_score": round(max_score, 3),
            "matching_chunks": matching_chunks,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return {"sdgs": results[:TOP_N_SDGS]}
