#!/usr/bin/env python3
import json, shutil
from pathlib import Path

BASE = Path("/media/popic/New Volume/training/datasets/workflow")
PROJECTS = BASE / "projects"
NOISE = BASE / "noise"
NOISE.mkdir(exist_ok=True)

kept = []
moved = 0

for wf in sorted(PROJECTS.glob("*.workflow.json")):
    with open(wf, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    nodes = data.get("nodes", [])
    has_agent = bool(data.get("agent"))
    has_code = any(n["metadata"]["extension"] in {".py", ".ipynb", ".m"} for n in nodes)
    is_synthetic = data["project_name"].endswith("__root")
    
    # Keep if: has agent, or has code files, or has 3+ nodes and isn't a boring synthetic
    keep = has_agent or has_code or (len(nodes) >= 3 and not is_synthetic)
    
    if keep:
        kept.append({
            "project_name": data["project_name"],
            "workflow_id": data["workflow_id"],
            "project_type": data["project_type"],
            "source_path": data["source_path"],
            "workflow_file": str(Path("workflow/projects") / wf.name),
            "node_count": len(nodes),
            "agent_id": data["agent"]["agent_id"] if data.get("agent") else None
        })
    else:
        shutil.move(str(wf), str(NOISE / wf.name))
        moved += 1

# Write clean master registry
master = {
    "workflow_registry_id": f"registry_clean_{str(__import__('uuid').uuid4())[:8]}",
    "base_path": str(BASE.parent),
    "total_projects": len(kept),
    "projects": kept,
    "generated_at": "2026-05-13",
    "schema_version": "2.1_clean"
}

with open(BASE / "master_workflow_registry.json", "w", encoding="utf-8") as f:
    json.dump(master, f, indent=2, ensure_ascii=False)

print(f"Kept: {len(kept)}  Moved to noise: {moved}")
