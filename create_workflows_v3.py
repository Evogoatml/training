#!/usr/bin/env python3
"""Read ALL file contents and build proper workflow JSONs."""

import json
import os
import re
import uuid
import shutil
import base64
from pathlib import Path

BASE_DIR = Path("/media/popic/New Volume/training/datasets")
WORKFLOW_DIR = BASE_DIR / "workflow"
PROJECTS_DIR = WORKFLOW_DIR / "projects"

# Exclude dirs
EXCLUDE_DIRS = {".git", "venv", "__pycache__", ".idea", ".vscode",
                "node_modules", ".backend", "workflow"}
SKIP_FILES = {".gitignore", ".travis.yml"}

TEXT_EXTS = {".py", ".md", ".txt", ".csv", ".json", ".yml", ".yaml", ".ipynb",
             ".html", ".css", ".js", ".xml", ".cfg", ".ini", ".toml", ".sh", ".bat"}

def is_excluded(p):
    return any(part in EXCLUDE_DIRS for part in p.parts)

def read_file_content(fp):
    """Read file content. Text as string, binary as base64."""
    ext = fp.suffix.lower()
    if ext in TEXT_EXTS or fp.name == "AGENT.md":
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                return {"type": "text", "content": f.read()}
        except Exception:
            pass
    # Binary fallback
    try:
        with open(fp, "rb") as f:
            raw = f.read()
        return {"type": "binary", "size": len(raw), "base64": base64.b64encode(raw).decode("ascii")}
    except Exception as e:
        return {"type": "error", "error": str(e)}

def has_agent_md(d):
    return (d / "AGENT.md").is_file()

def read_agent_md(path):
    agent_md = path / "AGENT.md"
    if not agent_md.exists():
        return None
    try:
        text = agent_md.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    data = {"raw": text}
    m = re.search(r"\*\*Agent ID\*\*\s*\|\s*`?([^`\|]+)`?", text)
    if m:
        data["agent_id"] = m.group(1).strip()
    m = re.search(r"\*\*Folder\*\*\s*\|\s*`?([^`\|]+)`?", text)
    if m:
        data["folder"] = m.group(1).strip()
    return data

# ------------------------------------------------------------------
# 1. Discover every directory
# ------------------------------------------------------------------
all_dirs = []
for root, dirs, _ in os.walk(BASE_DIR):
    dirs[:] = [d for d in dirs if not is_excluded(Path(root) / d)]
    all_dirs.append(Path(root))

# 2. Agent roots
agent_dirs = [d for d in all_dirs if has_agent_md(d)]

# 3. Candidate roots (directories with code files directly in them)
candidate_dirs = []
for d in all_dirs:
    if d == BASE_DIR:
        continue
    if any(d.is_relative_to(a) and d != a for a in agent_dirs):
        continue
    try:
        has_files = any(f.is_file() for f in d.iterdir())
        if has_files:
            candidate_dirs.append(d)
    except OSError:
        pass

# 4. Build master list - deepest wins
all_project_dirs = sorted(set(agent_dirs + candidate_dirs),
                          key=lambda p: len(p.parts), reverse=True)

project_roots = []
for d in all_project_dirs:
    has_child = any(c.is_relative_to(d) and c != d and c in project_roots
                    for c in all_project_dirs)
    if not has_child:
        project_roots.append(d)

project_roots.sort(key=lambda p: len(p.parts), reverse=True)

# ------------------------------------------------------------------
# 5. Assign every file to deepest project root
# ------------------------------------------------------------------
file_to_project = {}
orphan_files = []

for root, dirs, files in os.walk(BASE_DIR):
    dirs[:] = [d for d in dirs if not is_excluded(Path(root) / d)]
    for fn in files:
        if fn.startswith(".") or fn in SKIP_FILES:
            continue
        fp = Path(root) / fn
        if is_excluded(fp):
            continue
        covering = None
        for pr in project_roots:
            if str(fp).startswith(str(pr) + os.sep) or fp == pr:
                if covering is None or len(pr.parts) > len(covering.parts):
                    covering = pr
        if covering:
            file_to_project.setdefault(covering, []).append(fp)
        else:
            orphan_files.append(fp)

# Orphans -> synthetic roots
synthetic_projects = {}
for fp in orphan_files:
    parent = fp.parent
    if parent == BASE_DIR:
        continue
    synthetic_projects.setdefault(parent, []).append(fp)

# ------------------------------------------------------------------
# 6. Build JSONs WITH CONTENT
# ------------------------------------------------------------------
def safe_name(rel):
    s = str(rel.as_posix()).replace("/", "__").replace(" ", "_")
    s = re.sub(r"[^a-zA-Z0-9_\-.]", "_", s)[:120]
    return s

def build_workflow(project_dir, files, agent=None, is_synthetic=False):
    nodes = []
    for fp in sorted(files):
        rel = fp.relative_to(BASE_DIR).as_posix()
        ext = fp.suffix.lower()
        role = "module"
        if fp.name == "AGENT.md":
            role = "agent_manifest"
        elif fp.name in {"main.py", "app.py", "__init__.py", "train.py"}:
            role = "entrypoint"
        elif ext == ".ipynb":
            role = "notebook"

        content_data = read_file_content(fp)

        node = {
            "node_id": f"node_{str(uuid.uuid4())[:8]}",
            "type": "agent_manifest" if role == "agent_manifest" else "file",
            "label": fp.name,
            "file_path": rel,
            "absolute_path": str(fp),
            "metadata": {
                "size_bytes": fp.stat().st_size if fp.exists() else 0,
                "extension": ext,
                "role": role,
            },
            "content": content_data
        }
        nodes.append(node)

    edges = []
    agent_nodes = [n for n in nodes if n["type"] == "agent_manifest"]
    ep_nodes   = [n for n in nodes if n["metadata"]["role"] == "entrypoint"]
    mod_nodes  = [n for n in nodes if n["metadata"]["role"] == "module"]
    for a in agent_nodes:
        for e in ep_nodes:
            edges.append({"from": a["node_id"], "to": e["node_id"], "type": "manifest_points_to"})
    for e in ep_nodes:
        for m in mod_nodes:
            edges.append({"from": e["node_id"], "to": m["node_id"], "type": "imports_or_uses"})

    name = project_dir.name
    if is_synthetic:
        name = f"{project_dir.name}__root"

    py_count = sum(1 for n in nodes if n["metadata"]["extension"] == ".py")
    nb_count = sum(1 for n in nodes if n["metadata"]["extension"] == ".ipynb")
    if nb_count > 0 and py_count == 0:
        ptype = "notebook"
    elif py_count > 0:
        ptype = "python_tool"
    else:
        ptype = "mixed"

    return {
        "workflow_id": f"wf_{safe_name(project_dir.relative_to(BASE_DIR))[:60]}_{str(uuid.uuid4())[:6]}",
        "project_name": name,
        "source_path": str(project_dir.relative_to(BASE_DIR).as_posix()),
        "absolute_path": str(project_dir),
        "agent": agent,
        "project_type": ptype,
        "nodes": nodes,
        "edges": edges,
        "generated_at": "2026-05-13",
        "schema_version": "2.0"
    }

# Clean + recreate
if WORKFLOW_DIR.exists():
    shutil.rmtree(WORKFLOW_DIR)
WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)

master = {
    "workflow_registry_id": f"registry_{str(uuid.uuid4())[:8]}",
    "base_path": str(BASE_DIR),
    "total_projects": 0,
    "projects": [],
    "generated_at": "2026-05-13",
    "schema_version": "2.0"
}

# Agent & candidate roots
for pr in project_roots:
    agent = read_agent_md(pr) if has_agent_md(pr) else None
    files = file_to_project.get(pr, [])
    if not files:
        continue
    wf = build_workflow(pr, files, agent=agent)
    rel = pr.relative_to(BASE_DIR)
    out_file = PROJECTS_DIR / f"{safe_name(rel)}.workflow.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    master["projects"].append({
        "project_name": wf["project_name"],
        "workflow_id": wf["workflow_id"],
        "project_type": wf["project_type"],
        "source_path": wf["source_path"],
        "workflow_file": str(out_file.relative_to(BASE_DIR).as_posix()),
        "node_count": len(wf["nodes"]),
        "agent_id": wf["agent"]["agent_id"] if wf["agent"] else None
    })
    master["total_projects"] += 1
    print(f"Wrote {out_file.name} ({len(wf['nodes'])} nodes)")

# Synthetic container roots
for parent_dir, files in synthetic_projects.items():
    if not files or parent_dir == BASE_DIR or parent_dir in project_roots:
        continue
    wf = build_workflow(parent_dir, files, is_synthetic=True)
    rel = parent_dir.relative_to(BASE_DIR)
    out_file = PROJECTS_DIR / f"{safe_name(rel)}__root.workflow.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(wf, f, indent=2, ensure_ascii=False)
    master["projects"].append({
        "project_name": wf["project_name"],
        "workflow_id": wf["workflow_id"],
        "project_type": wf["project_type"],
        "source_path": wf["source_path"],
        "workflow_file": str(out_file.relative_to(BASE_DIR).as_posix()),
        "node_count": len(wf["nodes"]),
        "agent_id": None
    })
    master["total_projects"] += 1
    print(f"Wrote {out_file.name} ({len(wf['nodes'])} nodes) [synthetic]")

master_file = WORKFLOW_DIR / "master_workflow_registry.json"
with open(master_file, "w", encoding="utf-8") as f:
    json.dump(master, f, indent=2, ensure_ascii=False)
print(f"\nMaster registry: {master_file}")
print(f"Total projects: {master['total_projects']}")
