#!/usr/bin/env python3
"""Fine‑tuning trainer that builds a synthetic dataset from the existing knowledge store.

This script walks the legacy knowledge directory (or the lightweight GraphRAG store) and
produces a JSON‑Lines (JSONL) file suitable for fine‑tuning an LLM (Ollama, LLaMA‑fine, etc.).
Each line contains a ``{"prompt": ..., "completion": ...}`` pair.
The prompt is a simple question derived from a knowledge chunk; the completion is the chunk text.

Usage
-----
    python -m brain.trainer.fine_tune_from_knowledge

The generated file is written to ``~/telegram-bot/training/knowledge_finetune.jsonl``.
You can then feed it to your favourite fine‑tuning tool (``ollama``, ``llamafine``, etc.).
"""

import json
import logging
import importlib.util
from pathlib import Path
from typing import List, Dict

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dynamically load the knowledge accessor without importing the top‑level ``brain``
# package (which pulls in ``brain.system`` and the unavailable ``hermes_tools``).
# We load the file ``brain/agents/knowledge.py`` directly.
# ---------------------------------------------------------------------------
_KNOWLEDGE_MODULE_PATH = Path(__file__).resolve().parents[1] / "agents" / "knowledge.py"

spec = importlib.util.spec_from_file_location("knowledge_module", _KNOWLEDGE_MODULE_PATH)
knowledge_mod = importlib.util.module_from_spec(spec)  # type: ignore
if spec and spec.loader:
    spec.loader.exec_module(knowledge_mod)  # type: ignore
else:
    raise ImportError(f"Cannot load knowledge module from {_KNOWLEDGE_MODULE_PATH}")

# Grab the public ``query`` function.
rag_query = getattr(knowledge_mod, "query")


def _collect_chunks(top_k: int = 1000) -> List[str]:
    """Retrieve the most relevant knowledge chunks.

    ``rag_query`` returns a list of ``(chunk_text, score)`` tuples (or a list of
    dicts with a ``"text"`` key).  We request a fairly large ``top_k`` to capture
    most of the store.  If the underlying store cannot rank, it simply returns the
    first ``top_k`` chunks.
    """
    results = rag_query(query="", top_k=top_k)  # empty query → all chunks
    chunks: List[str] = []
    for item in results:
        if isinstance(item, (list, tuple)) and len(item) >= 1:
            chunks.append(str(item[0]))
        elif isinstance(item, dict) and "text" in item:
            chunks.append(str(item["text"]))
        else:
            chunks.append(str(item))
    return chunks


def _make_qa_pair(chunk: str, idx: int) -> Dict[str, str]:
    """Create a synthetic Q&A pair from a knowledge chunk.

    The prompt is phrased as a request for explanation.  The completion returns the
    raw (cleaned) chunk text.  ``idx`` ensures each prompt is unique.
    """
    cleaned = " ".join(chunk.split())
    prompt = f"Explain the following knowledge item #{idx}:"
    return {"prompt": prompt, "completion": cleaned}


def build_dataset(output_path: Path, top_k: int = 1000) -> int:
    """Generate the JSONL dataset and write it to *output_path*.
    Returns the number of records written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    chunks = _collect_chunks(top_k=top_k)
    with output_path.open("w", encoding="utf-8") as f:
        for i, chunk in enumerate(chunks, start=1):
            pair = _make_qa_pair(chunk, i)
            json.dump(pair, f)
            f.write("\n")
    return len(chunks)


def main() -> None:
    data_dir = Path("~/telegram-bot/training").expanduser()
    data_dir.mkdir(parents=True, exist_ok=True)
    output_file = data_dir / "knowledge_finetune.jsonl"

    log.info("Building fine‑tuning dataset from knowledge store …")
    record_count = build_dataset(output_file)
    size_mb = output_file.stat().st_size / 1024 / 1024
    print(f"✅ Finished – {record_count:,} records written to {output_file} ({size_mb:.1f} MiB)")
    print("\nYou can now feed this file to your fine‑tuning tool, e.g.:")
    print("  ollama create my‑knowledge‑model")
    print(f"  <run your fine‑tune command pointing at {output_file}>")

if __name__ == "__main__":
    main()
