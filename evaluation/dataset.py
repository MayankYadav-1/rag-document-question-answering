"""Load the QA dataset and resolve each evidence span to character offsets.

The offsets are computed against the *normalized* Document.text (see
rag.documents), which is the same coordinate system chunk offsets live in. This
is what makes retrieval scoring strategy-independent.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from rag.documents import Document


@dataclass
class EvalItem:
    id: str
    question: str
    answer: str
    doc_id: str
    evidence: str
    ev_start: int      # char offset of evidence in the doc's normalized text
    ev_end: int


def _find_span(haystack: str, needle: str) -> tuple[int, int] | None:
    """Case-insensitive, whitespace-tolerant search returning (start, end)."""
    idx = haystack.lower().find(needle.lower())
    if idx != -1:
        return idx, idx + len(needle)
    # fall back to a whitespace-flexible regex (handles stray spacing)
    pattern = re.escape(needle.strip())
    pattern = re.sub(r"\\\s+|\s+", r"\\s+", pattern)
    m = re.search(pattern, haystack, re.IGNORECASE)
    return (m.start(), m.end()) if m else None


def load_dataset(path: str | Path, docs_by_id: Dict[str, Document]) -> List[EvalItem]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    items: List[EvalItem] = []
    problems: List[str] = []
    for q in data["questions"]:
        doc = docs_by_id.get(q["doc"])
        if doc is None:
            problems.append(f"{q['id']}: unknown doc '{q['doc']}'")
            continue
        span = _find_span(doc.text, q["evidence"])
        if span is None:
            problems.append(
                f"{q['id']}: evidence not found in '{q['doc']}': "
                f"{q['evidence'][:60]!r}"
            )
            continue
        items.append(EvalItem(
            id=q["id"], question=q["question"], answer=q["answer"],
            doc_id=q["doc"], evidence=q["evidence"],
            ev_start=span[0], ev_end=span[1],
        ))
    if problems:
        raise ValueError(
            "Dataset validation failed for these items:\n  " +
            "\n  ".join(problems)
        )
    return items
