#!/usr/bin/env python3
"""Inspect Spec Kit artifacts and report which SDD steps are missing or stale.

Used by the `sdd-autopilot` Spec Kit workflow (workflows/sdd-autopilot/workflow.yml)
and by humans on stage.

Usage:
  python3 scripts/speckit_state.py state      # JSON: decisions for the workflow
  python3 scripts/speckit_state.py remaining  # JSON: open tasks left in tasks.md
  python3 scripts/speckit_state.py explain    # human-readable summary

Every flag is phrased positively ("plan_stale": true means "run plan"), so workflow
conditions can use plain truthy paths. The script always exits 0 on success, because a
non-zero exit fails a Spec Kit workflow run.

  python3 scripts/speckit_state.py stamp plan   # record the spec.md hash plan.md was built from
  python3 scripts/speckit_state.py stamp tasks  # record the plan.md hash tasks.md was built from

Staleness uses content fingerprints first: after the workflow runs plan or tasks it stamps a
SHA-256 of the input file into <feature>/.sdd-stamps.json. "plan is stale" then means "spec.md no
longer matches the hash the plan was built from". This stays correct even when a regenerated plan
comes out byte-identical.

Without a stamp (for example a plan created by hand in Copilot Chat) it falls back to time:
  - uncommitted or untracked file -> its filesystem modification time
  - committed and clean file      -> time of the last commit that touched it
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = re.compile(r"\[[A-Z][A-Z0-9_]{2,}\]")
UNCHECKED_TASK = re.compile(r"^\s*[-*] \[ \]", re.MULTILINE)
CLARIFY_MARKER = "[NEEDS CLARIFICATION"


def git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
        ).stdout.strip()
    except FileNotFoundError:
        return ""


def last_change(path: Path) -> float:
    rel = str(path.relative_to(ROOT))
    if git("status", "--porcelain", "--", rel):
        return path.stat().st_mtime
    committed = git("log", "-1", "--format=%ct", "--", rel)
    return float(committed) if committed else path.stat().st_mtime


def feature_dir() -> Path | None:
    env = os.environ.get("SPECIFY_FEATURE_DIRECTORY")
    if env:
        candidate = Path(env)
        return candidate if candidate.is_absolute() else ROOT / candidate

    feature_json = ROOT / ".specify" / "feature.json"
    if feature_json.exists():
        try:
            value = json.loads(feature_json.read_text()).get("feature_directory")
        except (json.JSONDecodeError, OSError):
            value = None
        if value:
            candidate = Path(value)
            return candidate if candidate.is_absolute() else ROOT / candidate

    specs = ROOT / "specs"
    if specs.is_dir():
        folders = sorted(p for p in specs.iterdir() if p.is_dir())
        if folders:
            return folders[-1]
    return None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_stamps(fdir: Path) -> dict:
    stamps = fdir / ".sdd-stamps.json"
    if not stamps.exists():
        return {}
    try:
        return json.loads(stamps.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def changed_since(source: Path, target: Path, stamp_key: str) -> bool:
    """True when `target` was built from an older version of `source`."""
    stamp = read_stamps(target.parent).get(stamp_key)
    if stamp:
        return stamp != sha256(source)
    return last_change(source) > last_change(target)


def stamp(kind: str) -> dict:
    fdir = feature_dir()
    if fdir is None:
        raise SystemExit("No active feature to stamp.")
    source = {"plan": fdir / "spec.md", "tasks": fdir / "plan.md"}[kind]
    stamps = read_stamps(fdir)
    stamps[kind] = sha256(source)
    (fdir / ".sdd-stamps.json").write_text(json.dumps(stamps, indent=2) + "\n")
    return {"stamped": kind, "source": source.name}


def compute_state() -> dict:
    reasons: list[str] = []
    constitution = ROOT / ".specify" / "memory" / "constitution.md"
    constitution_missing = (not constitution.exists()) or bool(
        PLACEHOLDER.search(constitution.read_text(encoding="utf-8"))
    )
    if constitution_missing:
        reasons.append("constitution: missing or still the template, write it with the team")
    else:
        reasons.append("constitution: ratified")

    fdir = feature_dir()
    spec = fdir / "spec.md" if fdir else None
    plan = fdir / "plan.md" if fdir else None
    tasks = fdir / "tasks.md" if fdir else None

    needs_spec = spec is None or not spec.exists()
    reasons.append("spec: missing, run specify" if needs_spec else "spec: present, skip specify")

    open_questions = (not needs_spec) and CLARIFY_MARKER in spec.read_text(encoding="utf-8")
    if not needs_spec:
        reasons.append(
            "spec: has [NEEDS CLARIFICATION], human gate for clarify"
            if open_questions
            else "spec: no open questions, skip clarify"
        )

    if needs_spec:
        plan_stale = True
        reasons.append("plan: will be created after the spec")
    elif not plan.exists():
        plan_stale = True
        reasons.append("plan: missing, run plan")
    elif changed_since(spec, plan, "plan"):
        plan_stale = True
        reasons.append("plan: spec.md changed after plan.md, run plan")
    else:
        plan_stale = False
        reasons.append("plan: up to date, skip plan")

    if plan_stale:
        tasks_stale = True
        reasons.append("tasks: plan will change, run tasks")
    elif not tasks.exists():
        tasks_stale = True
        reasons.append("tasks: missing, run tasks")
    elif changed_since(plan, tasks, "tasks"):
        tasks_stale = True
        reasons.append("tasks: plan.md changed after tasks.md, run tasks")
    else:
        tasks_stale = False
        reasons.append("tasks: up to date, skip tasks")

    open_tasks = bool(tasks and tasks.exists() and UNCHECKED_TASK.search(tasks.read_text(encoding="utf-8")))

    return {
        "feature_dir": str(fdir.relative_to(ROOT)) if fdir and fdir.is_relative_to(ROOT) else (str(fdir) if fdir else ""),
        "constitution_missing": constitution_missing,
        "needs_spec": needs_spec,
        "open_questions": open_questions,
        "plan_stale": plan_stale,
        "tasks_stale": tasks_stale,
        "open_tasks": open_tasks,
        "reasons": reasons,
    }


def compute_remaining() -> dict:
    fdir = feature_dir()
    tasks = fdir / "tasks.md" if fdir else None
    count = 0
    if tasks and tasks.exists():
        count = len(UNCHECKED_TASK.findall(tasks.read_text(encoding="utf-8")))
    return {"open_tasks": count > 0, "count": count}


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "explain"
    if command == "state":
        print(json.dumps(compute_state()))
    elif command == "remaining":
        print(json.dumps(compute_remaining()))
    elif command == "stamp" and len(argv) > 2 and argv[2] in ("plan", "tasks"):
        print(json.dumps(stamp(argv[2])))
    elif command == "explain":
        state = compute_state()
        print(f"Feature: {state['feature_dir'] or '(none yet)'}")
        for reason in state["reasons"]:
            print(f"  - {reason}")
    else:
        print(__doc__, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
