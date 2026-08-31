"""Retrieval metrics.

A retrieved chunk is *relevant* to an eval item when it comes from the correct
document and its character range overlaps the item's evidence span. From that
single notion of relevance we derive:

* hit@k        — did any of the top-k retrieved chunks contain the evidence?
* recall@k     — same as hit@k here (one evidence span per question)
* reciprocal rank — 1 / rank of the first relevant chunk (0 if none in top-k)

Aggregated across the dataset these give hit-rate@k and MRR.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from evaluation.dataset import EvalItem
from rag.vector_store import Retrieved


def is_relevant(retrieved: Retrieved, item: EvalItem) -> bool:
    c = retrieved.chunk
    return c.doc_id == item.doc_id and c.overlaps(item.ev_start, item.ev_end)


def first_relevant_rank(retrieved: List[Retrieved], item: EvalItem) -> int | None:
    """1-based rank of the first relevant chunk, or None."""
    for i, r in enumerate(retrieved, 1):
        if is_relevant(r, item):
            return i
    return None


def hit_at_k(retrieved: List[Retrieved], item: EvalItem, k: int) -> bool:
    rank = first_relevant_rank(retrieved[:k], item)
    return rank is not None


def reciprocal_rank(retrieved: List[Retrieved], item: EvalItem,
                    k: int | None = None) -> float:
    subset = retrieved if k is None else retrieved[:k]
    rank = first_relevant_rank(subset, item)
    return 1.0 / rank if rank else 0.0


@dataclass
class AggregateMetrics:
    n: int
    hit_rates: dict            # {k: hit_rate}
    mrr: float                 # mean reciprocal rank over the full retrieved list
    misses: List[str]          # ids with no relevant chunk in the top result set

    def as_row(self, ks: List[int]) -> dict:
        row = {f"hit@{k}": self.hit_rates[k] for k in ks}
        row["mrr"] = self.mrr
        return row


def evaluate_retrieval(
    per_question_retrieved: List[tuple[EvalItem, List[Retrieved]]],
    ks: List[int],
) -> AggregateMetrics:
    n = len(per_question_retrieved)
    hit_counts = {k: 0 for k in ks}
    rr_sum = 0.0
    misses: List[str] = []
    max_k = max(ks)
    for item, retrieved in per_question_retrieved:
        for k in ks:
            if hit_at_k(retrieved, item, k):
                hit_counts[k] += 1
        rr = reciprocal_rank(retrieved, item, k=max_k)
        rr_sum += rr
        if rr == 0.0:
            misses.append(item.id)
    hit_rates = {k: (hit_counts[k] / n if n else 0.0) for k in ks}
    return AggregateMetrics(
        n=n, hit_rates=hit_rates, mrr=(rr_sum / n if n else 0.0), misses=misses
    )
