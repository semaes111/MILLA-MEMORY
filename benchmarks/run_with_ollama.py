#!/usr/bin/env python3
"""
Run MemPalace LongMemEval benchmark with Ollama embedding models.

Plugs a local Ollama embedding model into MemPalace's benchmark harness,
replacing ChromaDB's default all-MiniLM-L6-v2.

Usage:
    python benchmarks/run_with_ollama.py <data_file> [--model nomic-embed-text-v2-moe] [--mode raw]
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import urllib.request
import urllib.error


_DIM = None


def _embed_one(text, model, base_url, max_chars=8000):
    """Embed a single text, truncating if needed."""
    global _DIM
    text = text[:max_chars]
    payload = json.dumps(
        {
            "model": model,
            "input": text,
            "options": {"num_ctx": 8192},
        }
    ).encode()
    req = urllib.request.Request(
        f"{base_url}/api/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    vec = result["embeddings"][0]
    if _DIM is None:
        _DIM = len(vec)
    return vec


def _ollama_embed(texts, model, base_url="http://localhost:11434"):
    """Call Ollama embedding API, one text at a time with truncation fallback."""
    global _DIM
    embeddings = []
    for i, t in enumerate(texts):
        vec = None
        for max_chars in (8000, 4000, 2000, 1000):
            try:
                vec = _embed_one(t, model, base_url, max_chars)
                break
            except Exception:
                continue
        if vec is None:
            # Zero vector fallback
            vec = [0.0] * (_DIM or 768)
        embeddings.append(vec)
    return embeddings


def make_ollama_embed_fn(model_name, base_url="http://localhost:11434"):
    """Create a ChromaDB-compatible embedding function backed by Ollama."""
    from chromadb.api.types import EmbeddingFunction, Documents, Embeddings

    class OllamaEmbedFn(EmbeddingFunction):
        def __init__(self):
            print(f"  Connecting to Ollama at {base_url}...")
            test = _embed_one("test", model_name, base_url)
            print(f"  Ollama model: {model_name} ({len(test)} dimensions)")

        def __call__(self, input: Documents) -> Embeddings:
            return _ollama_embed(input, model_name, base_url)

    return OllamaEmbedFn()


def main():
    parser = argparse.ArgumentParser(description="MemPalace benchmark with Ollama embeddings")
    parser.add_argument("data_file", help="Path to LongMemEval JSON")
    parser.add_argument("--model", default="nomic-embed-text-v2-moe", help="Ollama embedding model")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument(
        "--mode",
        default="raw",
        choices=["raw", "aaak", "rooms", "hybrid", "full"],
        help="MemPalace retrieval mode",
    )
    parser.add_argument("--granularity", default="session", choices=["session", "turn"])
    parser.add_argument("--limit", type=int, default=0, help="Limit number of questions")
    args = parser.parse_args()

    embed_fn = make_ollama_embed_fn(args.model, args.ollama_url)

    sys.path.insert(0, str(Path(__file__).parent.parent))
    import benchmarks.longmemeval_bench as bench

    bench._bench_embed_fn = embed_fn

    model_tag = args.model.replace(":", "_").replace("/", "_")
    out_file = (
        f"benchmarks/results_mempal_{args.mode}_ollama_{model_tag}"
        f"_{args.granularity}_{datetime.now().strftime('%Y%m%d_%H%M')}.jsonl"
    )

    bench.run_benchmark(
        args.data_file,
        granularity=args.granularity,
        limit=args.limit,
        out_file=out_file,
        mode=args.mode,
    )


if __name__ == "__main__":
    main()
