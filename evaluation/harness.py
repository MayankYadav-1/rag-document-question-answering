"""The evaluation harness — the heart of this project.

It holds the embedder fixed and sweeps:

    chunking strategy  ×  {no re-ranker, re-ranker}

For every combination it builds an index, retrieves for all eval questions, and
reports hit-rate@k and MRR. This is how you *measure* whether a change (semantic
chunking, adding a re-ranker) actually helped instead of guessing.

Run:  python -m evaluation.harness            # auto-detect real vs offline
      python -m evaluation.harness --embedder hash --reranker lexical
"""

from __future__ import annotations

import argparse
import csv
import warnings
from pathlib import Path
from typing import List, Optional

from rag.chunking import (FixedSizeChunker, ParagraphChunker, SemanticChunker)
from rag.documents import load_corpus
from rag.embeddings import get_embedder
from rag.pipeline import RAGConfig, RAGPipeline
from rag.reranker import get_reranker

from evaluation.dataset import load_dataset
from evaluation.metrics import evaluate_retrieval

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "data" / "corpus"
DATASET_PATH = ROOT / "eval_data" / "questions.json"
RESULTS_DIR = ROOT / "results"
KS = [1, 3, 5]
MAX_K = 10


def _resolve_embedder(kind: str):
    """kind: 'st' | 'hash' | 'auto'. Falls back to hash if st is unavailable."""
    if kind == "hash":
        return get_embedder("hash")
    try:
        return get_embedder("st")
    except Exception as e:  # ImportError or model download failure
        if kind == "st":
            raise
        warnings.warn(f"Falling back to offline HashEmbedder ({e}).")
        return get_embedder("hash")


def _resolve_reranker(kind: str):
    """kind: 'cross-encoder' | 'lexical' | 'auto' | 'none'."""
    if kind == "none":
        return None
    if kind == "lexical":
        return get_reranker("lexical")
    try:
        return get_reranker("cross-encoder")
    except Exception as e:
        if kind == "cross-encoder":
            raise
        warnings.warn(f"Falling back to offline LexicalReranker ({e}).")
        return get_reranker("lexical")


def run(embedder_kind: str = "auto", reranker_kind: str = "auto") -> List[dict]:
    docs = load_corpus(CORPUS_DIR)
    docs_by_id = {d.doc_id: d for d in docs}
    dataset = load_dataset(DATASET_PATH, docs_by_id)

    embedder = _resolve_embedder(embedder_kind)
    reranker = _resolve_reranker(reranker_kind)

    print(f"Corpus: {len(docs)} documents | Eval questions: {len(dataset)}")
    print(f"Embedder: {embedder.name} | "
          f"Re-ranker: {reranker.name if reranker else 'none'}\n")

    def chunkers():
        return [
            FixedSizeChunker(chunk_size=600, overlap=100),
            ParagraphChunker(max_size=700),
            SemanticChunker(embedder, breakpoint_percentile=80),
        ]

    rows: List[dict] = []
    for chunker in chunkers():
        for use_rerank in (False, True):
            rr = reranker if use_rerank else None
            if use_rerank and rr is None:
                continue
            pipe = RAGPipeline(
                embedder=embedder, chunker=chunker, reranker=rr,
                config=RAGConfig(top_k=MAX_K, fetch_k=20),
            )
            n_chunks = pipe.ingest(docs)
            per_q = [(item, pipe.retrieve(item.question, k=MAX_K))
                     for item in dataset]
            agg = evaluate_retrieval(per_q, KS)
            row = {
                "chunker": chunker.name,
                "rerank": rr.name if rr else "none",
                "chunks": n_chunks,
                **{f"hit@{k}": round(agg.hit_rates[k], 3) for k in KS},
                "mrr": round(agg.mrr, 3),
                "misses": ",".join(agg.misses),
            }
            rows.append(row)
    return rows


def print_table(rows: List[dict]) -> None:
    headers = ["chunker", "rerank", "chunks"] + [f"hit@{k}" for k in KS] + ["mrr"]
    widths = {h: len(h) for h in headers}
    for r in rows:
        for h in headers:
            widths[h] = max(widths[h], len(str(r[h])))
    line = "  ".join(h.ljust(widths[h]) for h in headers)
    print(line)
    print("-" * len(line))
    for r in rows:
        print("  ".join(str(r[h]).ljust(widths[h]) for h in headers))
    print()

    best = max(rows, key=lambda r: (r["mrr"], r[f"hit@{KS[0]}"]))
    print(f"Best config by MRR: chunker={best['chunker']}, "
          f"rerank={best['rerank']} (mrr={best['mrr']}, "
          f"hit@1={best['hit@1']}, hit@{KS[-1]}={best[f'hit@{KS[-1]}']})")
    if best["misses"]:
        print(f"  Remaining misses: {best['misses']}")


def save_csv(rows: List[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["chunker", "rerank", "chunks"] + [f"hit@{k}" for k in KS] + \
             ["mrr", "misses"]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fields})


def main() -> None:
    ap = argparse.ArgumentParser(description="RAG retrieval evaluation harness")
    ap.add_argument("--embedder", choices=["auto", "st", "hash"], default="auto")
    ap.add_argument("--reranker", choices=["auto", "cross-encoder", "lexical",
                                           "none"], default="auto")
    ap.add_argument("--csv", default=str(RESULTS_DIR / "retrieval_results.csv"))
    args = ap.parse_args()

    rows = run(args.embedder, args.reranker)
    print_table(rows)
    save_csv(rows, Path(args.csv))
    print(f"Saved results to {args.csv}")


if __name__ == "__main__":
    main()
