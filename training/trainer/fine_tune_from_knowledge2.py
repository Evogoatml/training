#!/usr/bin/env python3
"""Fine‑tuning trainer that builds a JSONL dataset directly from the lightweight GraphRAG store.

We avoid importing the top‑level ``brain`` package (which pulls in ``brain.system``
and requires the unavailable ``hermes_tools``).  Instead we load ``GraphRAGStore``
via ``importlib`` from its source file.

The script:
1. Dynamically imports ``GraphRAGStore`` from ``brain/agents/holographic_node_graph_rag.py``.
2. Calls ``store.build_from_path()`` to load all knowledge chunks.
3. Queries the store with an empty string to retrieve *all* chunks.
4. Writes each chunk as a ``{"prompt": ..., "completion": ...}`` pair to
   ``~/telegram-bot/training/knowledge_finetune.jsonl``.

Usage
-----
    python -m brain.trainer.fine_tune_from_knowledge2
"""

import json
import logging
import sys
import importlib.util
from pathlib import Path
from typing import List, Dict

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Resolve the absolute path to the GraphRAG implementation.
# ``__file__`` is ``brain/trainer/fine_tune_from_knowledge2.py``; the GraphRAG
# source lives two directories up (repo root) plus ``brain/agents``.
# ---------------------------------------------------------------------------
GRAPH_RAG_PATH = Path(__file__).resolve().parents[3] / "memory" / "rag" / "holographic_node_graph_rag.py"

spec = importlib.util.spec_from_file_location("graph_rag_module", GRAPH_RAG_PATH)
graph_mod = importlib.util.module_from_spec(spec)  # type: ignore
if spec and spec.loader:
    spec.loader.exec_module(graph_mod)  # type: ignore
else:
    raise ImportError(f"Cannot load GraphRAG module from {GRAPH_RAG_PATH}")

# Grab the class directly.
GraphRAGStore = getattr(graph_mod, "GraphRAGStore")


def _load_store() -> GraphRAGStore:
    """Create a GraphRAGStore pointing at the actual knowledge directory.

    The legacy knowledge files live under ``GhostGoat/brain/agent_byte-master/knowledge``
    relative to the repository root. ``GraphRAGStore`` defaults to ``./brain/agent_byte-master/knowledge``
    which resolves to the current working directory (the ``brain/trainer`` folder) and therefore
    fails to find any files. We compute the absolute path two levels up from this script
    (repo root) and pass it to the store constructor.
    """
    knowledge_path = Path(__file__).resolve().parents[3] / "knowledge"
    store = GraphRAGStore(root_path=str(knowledge_path))
    store.build_from_path()  # now loads from the correct directory
    return store


def _collect_chunks(store: GraphRAGStore, top_k: int = 10000) -> List[str]:
    """Return all loaded chunks (up to top_k). The lightweight GraphRAG store scores
    relevance, but with an empty query every chunk scores 0 and would be filtered out.
    For fine‑tuning we want the full dataset, so we bypass the scoring and just
    return the stored chunks.
    """
    # store._chunks is a list of raw paragraph strings.
    return store._chunks[:top_k]



def _make_qa_pair(chunk: str, idx: int) -> Dict[str, str]:
    cleaned = " ".join(chunk.split())
    prompt = f"Explain the following knowledge item #{idx}:"
    return {"prompt": prompt, "completion": cleaned}


def build_dataset(output_path: Path, top_k: int = 10000) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    store = _load_store()
    chunks = _collect_chunks(store, top_k=top_k)
    with output_path.open("w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks, start=1):
            pair = _make_qa_pair(chunk, i)
            json.dump(pair, f)
            f.write("\n")
    return len(chunks)


def main() -> None:
    data_dir = Path(__file__).resolve().parents[2] / "GhostGoat" / "training"
    data_dir.mkdir(parents=True, exist_ok=True)
    output_file = data_dir / "knowledge_finetune.jsonl"
    log.info("Generating fine‑tuning dataset from GraphRAG store …")
    count = build_dataset(output_file)
    size_mb = output_file.stat().st_size / 1024 / 1024
    print(f"✅ Finished – {count:,} records written to {output_file} ({size_mb:.1f} MiB)")
    print("\nYou can now feed this file to your fine‑tuning tool, e.g.:")
    print("  ollama create my‑knowledge‑model")
    print(f"  <run your fine‑tune command pointing at {output_file}>")

if __name__ == "__main__":
    main()
