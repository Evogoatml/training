"""
SelfBuilder — gives GhostGoat the ability to grow its own knowledge.

Two upgrade paths:
  1. ingest_file(path)          — drop any file on the bot and it indexes itself
  2. learn_from_execution(...)  — after every successful task, distil what was
                                  learned and store it as a new training entry

Both ultimately call KnowledgeTank._index_training_entries(), so the new
knowledge is immediately searchable and will be injected into future LLM
reasoning contexts via _fetch_training_context().
"""

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.memory.semantic_tank import (
    AlgorithmScanner,
    KnowledgeTank,
)

# File types that AlgorithmScanner already handles natively
_CODE_SUFFIXES = {
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".cs",
    ".go", ".rs", ".rb", ".php", ".swift", ".kt",
}

_TRAINING_DIR = Path(__file__).resolve().parent / "training"


class SelfBuilder:
    """Wraps KnowledgeTank to provide live self-upgrade capabilities."""

    def __init__(
        self,
        tank: KnowledgeTank,
        llm_call: Optional[Callable[[str], str]] = None,
    ):
        """
        Args:
            tank:     The KnowledgeTank instance to write into.
            llm_call: Optional callable(prompt) -> str used to extract
                      structured knowledge from free-form text/task results.
                      Pass None to use the built-in heuristic extractor.
        """
        self.tank = tank
        self._llm = llm_call

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest_file(self, path: str) -> int:
        """Index any file into GhostGoat's knowledge.

        Routing:
          - Code files (.py, .js, …) → AlgorithmScanner → algorithms table
          - JSON files                → training entries (if list) or wrapped
          - Text / Markdown / other  → heuristic training entry

        Returns:
            Number of entries indexed (0 on failure).
        """
        p = Path(path)
        if not p.exists():
            print(f"[SelfBuilder] File not found: {path}")
            return 0

        suffix = p.suffix.lower()

        if suffix in _CODE_SUFFIXES:
            return self._ingest_code_file(p)
        elif suffix == ".json":
            return self._ingest_json_file(p)
        else:
            return self._ingest_text_file(p)

    def learn_from_execution(
        self,
        query: str,
        understanding: Dict[str, Any],
        results: List[Dict],
        final_result: Dict,
    ) -> bool:
        """Distil a successful execution into a new training entry.

        Only called when at least one task succeeded.  The new entry is
        written both to the DB and appended to a JSON file in training/
        so it survives database resets.

        Returns:
            True if a new entry was indexed, False otherwise.
        """
        if not any(r.get("success") for r in results):
            return False

        entry = self._build_execution_entry(query, understanding, results, final_result)
        if not entry:
            return False

        count = self.tank._index_training_entries([entry], source_file="self_learned")
        if count:
            self._persist_entry(entry)
            print(f"[SelfBuilder] Learned: '{entry['title']}'")
        return count > 0

    # ------------------------------------------------------------------
    # File ingestion helpers
    # ------------------------------------------------------------------

    def _ingest_code_file(self, p: Path) -> int:
        """Use AlgorithmScanner to index a single code file."""
        try:
            scanner = AlgorithmScanner()
            meta = scanner.scan_file(p)
            if meta is None:
                return 0
            indexed = self.tank.index_batch([meta])
            print(f"[SelfBuilder] Indexed code file: {p.name} → {indexed} entries")
            return indexed
        except Exception as exc:
            print(f"[SelfBuilder] Error indexing code file {p.name}: {exc}")
            return 0

    def _ingest_json_file(self, p: Path) -> int:
        """Ingest a JSON file as training entries or wrapped entry."""
        try:
            with open(p) as fh:
                data = json.load(fh)
        except Exception as exc:
            print(f"[SelfBuilder] Cannot parse JSON {p.name}: {exc}")
            return 0

        # If it's already a list of training-format dicts with 'id' fields,
        # load directly
        if isinstance(data, list) and data and isinstance(data[0], dict) and "id" in data[0]:
            count = self.tank._index_training_entries(data, source_file=str(p))
            # Copy into training dir so it's reloaded on next boot
            dest = _TRAINING_DIR / p.name
            if not dest.exists():
                dest.write_text(json.dumps(data, indent=2))
            print(f"[SelfBuilder] Indexed JSON training file: {p.name} → {count} entries")
            return count

        # Otherwise wrap the whole file as a single training entry
        entry = {
            "id": f"json_{_short_hash(str(p))}",
            "title": p.stem.replace("_", " ").title(),
            "category": "ingested",
            "subcategory": "json",
            "description": f"JSON knowledge file: {p.name}",
            "content": json.dumps(data)[:4000],
            "tags": ["ingested", "json", p.stem],
        }
        count = self.tank._index_training_entries([entry], source_file=str(p))
        print(f"[SelfBuilder] Wrapped and indexed JSON: {p.name}")
        return count

    def _ingest_text_file(self, p: Path) -> int:
        """Ingest a text/markdown file as a training entry."""
        try:
            text = p.read_text(errors="ignore")
        except Exception as exc:
            print(f"[SelfBuilder] Cannot read {p.name}: {exc}")
            return 0

        if self._llm:
            entry = self._extract_with_llm(p.stem, text)
        else:
            entry = self._extract_heuristic(p.stem, text)

        count = self.tank._index_training_entries([entry], source_file=str(p))
        print(f"[SelfBuilder] Indexed text file: {p.name}")
        return count

    # ------------------------------------------------------------------
    # Execution-learning helpers
    # ------------------------------------------------------------------

    def _build_execution_entry(
        self,
        query: str,
        understanding: Dict,
        results: List[Dict],
        final_result: Dict,
    ) -> Optional[Dict]:
        """Turn an execution record into a training entry dict."""
        entry_id = f"learned_{_short_hash(query + datetime.now().isoformat())}"
        domain = understanding.get("domain", "general")
        intent = understanding.get("intent", query)
        summary = final_result.get("summary", "")
        findings = final_result.get("key_findings", [])
        recommendations = final_result.get("recommendations", [])

        # Build key_insight from LLM or heuristic
        if self._llm and summary:
            key_insight = self._llm_extract_insight(query, summary, findings)
        else:
            key_insight = summary or (findings[0] if findings else intent)

        if not key_insight:
            return None

        return {
            "id": entry_id,
            "title": _title_from_intent(intent),
            "category": "learned",
            "subcategory": domain,
            "description": query,
            "key_insight": key_insight,
            "use_cases": [query],
            "recommendations": recommendations,
            "tags": ["learned", domain] + _tags_from_text(query),
        }

    def _persist_entry(self, entry: Dict) -> None:
        """Append a learned entry to the self-learned JSON file in training/."""
        dest = _TRAINING_DIR / "self_learned.json"
        existing: List[Dict] = []
        if dest.exists():
            try:
                existing = json.loads(dest.read_text())
            except Exception:
                existing = []
        # Deduplicate by id
        ids = {e["id"] for e in existing}
        if entry["id"] not in ids:
            existing.append(entry)
            dest.write_text(json.dumps(existing, indent=2))

    # ------------------------------------------------------------------
    # Knowledge extraction
    # ------------------------------------------------------------------

    def _extract_heuristic(self, stem: str, text: str) -> Dict:
        """Build a training entry from plain text without an LLM."""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        title = stem.replace("_", " ").replace("-", " ").title()
        description = lines[0] if lines else title
        # Use first 300 chars as key_insight
        key_insight = " ".join(lines[1:5])[:300] if len(lines) > 1 else description
        tags = _tags_from_text(text[:500])
        return {
            "id": f"text_{_short_hash(stem + text[:50])}",
            "title": title,
            "category": "ingested",
            "subcategory": "text",
            "description": description,
            "key_insight": key_insight,
            "use_cases": [],
            "tags": ["ingested"] + tags,
        }

    def _extract_with_llm(self, stem: str, text: str) -> Dict:
        """Use the LLM to extract a structured training entry from text."""
        prompt = f"""Extract structured knowledge from this document and return JSON:

Title hint: {stem.replace('_', ' ')}
Content (first 2000 chars):
{text[:2000]}

Return JSON with these exact keys:
{{
  "title": "Short title",
  "category": "domain category",
  "description": "One sentence summary",
  "key_insight": "The most important thing to know",
  "use_cases": ["when to apply this"],
  "tags": ["tag1", "tag2"]
}}"""
        try:
            raw = self._llm(prompt)
            parsed = json.loads(raw)
            parsed["id"] = f"text_{_short_hash(stem + text[:50])}"
            parsed.setdefault("subcategory", "text")
            return parsed
        except Exception:
            return self._extract_heuristic(stem, text)

    def _llm_extract_insight(self, query: str, summary: str, findings: List) -> str:
        """Use the LLM to distil an insight from task results."""
        prompt = f"""Given this completed task, write one concise sentence capturing the key insight:

Task: {query}
Summary: {summary}
Key findings: {json.dumps(findings[:3])}

Return only the insight sentence, nothing else."""
        try:
            return self._llm(prompt).strip()
        except Exception:
            return summary


# ------------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------------

def _short_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:10]


def _title_from_intent(intent: str) -> str:
    """Turn an intent string into a readable title (max 60 chars)."""
    title = re.sub(r"[^a-zA-Z0-9 ]", " ", intent).strip()
    title = " ".join(title.split())
    return title[:60].title() if title else "Learned Task"


def _tags_from_text(text: str) -> List[str]:
    """Extract simple keyword tags from text."""
    words = re.findall(r"\b[a-z]{4,}\b", text.lower())
    stopwords = {
        "this", "that", "with", "from", "have", "will", "been",
        "they", "when", "what", "which", "there", "their", "about",
    }
    freq: Dict[str, int] = {}
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda x: -x[1])[:5]]
