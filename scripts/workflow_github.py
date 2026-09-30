#!/usr/bin/env python3
"""Guarded GitHub delivery for the FleetWise demo, invoked by Spec Kit workflows."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import uuid

REPO = "hkaanturgut/spec-kit-fleetwise"
ACCOUNT = "hkaanturgut"
TRAILER = "Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
TASK = re.compile(r"^\s*[-*] \[([ xX])\] (T\d{3,})\s+(.+)$", re.MULTILINE)


def run(*args: str, input_text: str | None = None) -> str:
    result = subprocess.run(args, input=input_text, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(f"{' '.join(args)} failed:\n{result.stderr or result.stdout}")
    return result.stdout.rstrip("\n")


def api(path: str, payload: dict | None = None) -> object:
    args = ["gh", "api", f"repos/{REPO}/{path}"]
    if payload is not None:
        args += ["--input", "-"]
    return json.loads(run(*args, input_text=json.dumps(payload) if payload is not None else None))


def pages(path: str) -> list[dict]:
    result = json.loads(run("gh", "api", "--paginate", "--slurp", f"repos/{REPO}/{path}"))
    return [item for page in result for item in page]


def authenticate() -> None:
    allowed = {f"https://github.com/{REPO}", f"https://github.com/{REPO}.git",
               f"git@github.com:{REPO}.git", f"ssh://git@github.com/{REPO}.git"}
    for mode in ([], ["--push"]):
        urls = run("git", "remote", "get-url", *mode, "--all", "origin").splitlines()
        if len(urls) != 1 or urls[0] not in allowed:
            raise RuntimeError(f"origin must point only to {REPO}, including its push URL")
    run("gh", "auth", "switch", "--hostname", "github.com", "--user", ACCOUNT)
    if run("gh", "api", "user", "-q", ".login") != ACCOUNT:
        raise RuntimeError(f"GitHub account must be {ACCOUNT}")


def state_path() -> Path:
    return Path(run("git", "rev-parse", "--git-path", "fleetwise-delivery.json"))


def save(state: dict) -> None:
    state_path().write_text(json.dumps(state, indent=2) + "\n")


def state() -> dict:
    value = json.loads(state_path().read_text())
    if run("git", "branch", "--show-current") != value["branch"] or value["branch"] == "main":
        raise RuntimeError("The delivery branch changed. Return to the recorded feature branch.")
    run("git", "merge-base", "--is-ancestor", value["base"], "HEAD")
    return value


def changed_files() -> list[str]:
    output = run("git", "-c", "core.quotepath=false", "ls-files", "-z", "--modified",
                 "--others", "--exclude-standard")
    staged = run("git", "diff", "--cached", "--name-only", "-z")
    return sorted(set(filter(None, (output + "\0" + staged).split("\0"))))


def setup_file(path: str) -> bool:
    return path.startswith((".specify/", ".github/skills/")) or path == ".github/copilot-instructions.md"


def prepare() -> None:
    authenticate()
    if state_path().exists():
        print(f"Reusing delivery branch: {state()['branch']}")
        return
    unexpected = [p for p in changed_files() if not setup_file(p)]
    if unexpected:
        raise RuntimeError(f"Start in a dedicated clean worktree; unrelated changes: {unexpected}")
    if not Path(".specify/memory/constitution.md").is_file():
        raise RuntimeError("Initialize Spec Kit and ratify a constitution first.")
    run("git", "fetch", "origin", "main")
    if run("git", "rev-parse", "HEAD") != run("git", "rev-parse", "origin/main"):
        raise RuntimeError("Start at current origin/main, not a historical checkpoint or an existing feature.")
    branch = f"demo/delivery-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:8]}"
    run("git", "switch", "-c", branch)
    save({"branch": branch, "base": run("git", "rev-parse", "HEAD")})
    print(f"Created feature branch: {branch}")


def feature(value: dict) -> tuple[Path, list[tuple[str, str, str]]]:
    pointer = json.loads(Path(".specify/feature.json").read_text())["feature_directory"]
    root = Path.cwd().resolve()
    directory = (root / pointer).resolve()
    relative = directory.relative_to(root).as_posix()
    if directory.parent != root / "specs":
        raise RuntimeError("Active feature must be a direct child of this checkout's specs/.")
    if "feature" in value and value["feature"] != relative:
        raise RuntimeError("Active feature changed during delivery.")
    tasks = TASK.findall((directory / "tasks.md").read_text())
    ids = [task[1] for task in tasks]
    if not ids or len(ids) != len(set(ids)):
        raise RuntimeError("tasks.md must contain unique checkbox task IDs (T001, T002, ...).")
    value["feature"] = relative
    return directory, tasks


def marker(value: dict, task_id: str) -> str:
    scope = hashlib.sha256(f"{value['branch']}:{value['feature']}".encode()).hexdigest()[:24]
    return f"<!-- fleetwise-task:{scope}:{task_id} -->"


def issue_map(value: dict, tasks: list[tuple[str, str, str]]) -> dict[str, dict]:
    existing = [issue for issue in pages("issues?state=all&per_page=100") if "pull_request" not in issue]
    mapping = {}
    for _, task_id, _ in tasks:
        matches = [issue for issue in existing if marker(value, task_id) in (issue.get("body") or "")]
        if len(matches) > 1:
            raise RuntimeError(f"Multiple GitHub issues match {task_id}; resolve duplicates before resuming.")
        if matches:
            mapping[task_id] = matches[0]
    return mapping


def issues(create: bool) -> dict:
    authenticate()
    value = state()
    directory, tasks = feature(value)
    save(value)
    mapping = issue_map(value, tasks)
    if create:
        labels = pages("labels?per_page=100")
        if not any(label["name"] == "demo" for label in labels):
            api("labels", {"name": "demo", "color": "0366d6", "description": "FleetWise rehearsal"})
        for _, task_id, description in tasks:
            if task_id not in mapping:
                mapping[task_id] = api("issues", {
                    "title": f"{task_id}: {description}"[:256],
                    "body": f"{marker(value, task_id)}\n\nFeature: `{value['feature']}`\n"
                            f"Branch: `{value['branch']}`\n\n{description}\n\n"
                            "Tracked by the delivery workflow. Close through the reviewed PR, not generation.",
                    "labels": ["demo"],
                })
    missing = [task_id for _, task_id, _ in tasks if task_id not in mapping]
    if missing:
        raise RuntimeError(f"Missing GitHub issues for {missing}; resume the taskstoissues stage.")
    links = {task_id: {"number": issue["number"], "url": issue["html_url"]}
             for task_id, issue in mapping.items()}
    (directory / "issue-links.json").write_text(json.dumps(links, indent=2) + "\n")
    print(json.dumps(links, indent=2))
    return links


def review() -> tuple[dict, list[str]]:
    value = state()
    _, tasks = feature(value)
    if any(checked == " " for checked, _, _ in tasks):
        raise RuntimeError("Unchecked tasks remain. Finish or explicitly rescope and review before publishing.")
    # Older demo baselines track this per-machine pointer; never publish its edits.
    if ".specify/feature.json" in run("git", "diff", "--cached", "--name-only", "-z").split("\0"):
        raise RuntimeError("Unstage the machine-local feature pointer before publication.")
    files = [path for path in changed_files() if path != ".specify/feature.json"]
    committed = run("git", "diff", "--name-only", "-z", value["base"], "HEAD").split("\0")
    if ".specify/feature.json" in committed:
        raise RuntimeError("A machine-local feature pointer was committed; review that commit before publishing.")
    for path in sorted(set(files + list(filter(None, committed)))):
        if not (setup_file(path) or path.startswith(("src/", "tests/", value["feature"] + "/"))
                or path == "AGENTS.md"):
            raise RuntimeError(f"Unexpected changed file: {path}. Review it outside automated publication.")
        if any(part in ("bin", "obj", "__pycache__") for part in Path(path).parts) or path.endswith((".db", ".pem", ".key")) or Path(path).name.startswith(".env"):
            raise RuntimeError(f"Refusing generated output or sensitive file: {path}")
    print(run("git", "--no-pager", "diff", value["base"], "--"))
    print("Files to include (inspect untracked files too):\n" + "\n".join(files))
    return value, files


def content_scan() -> None:
    # Keep the prohibited vocabulary out of repository source as well as output.
    pattern = "|".join(("aus" + "tin", "accel" + "erator", "vol" + "aris"))
    result = subprocess.run(["grep", "-rniE", pattern, ".", "--exclude-dir=.git"],
                            text=True, capture_output=True)
    if result.returncode != 1:
        raise RuntimeError("Pre-push content scan failed:\n" + result.stdout + result.stderr)


def publish() -> None:
    authenticate()
    links = issues(create=False)
    value, files = review()
    print(run("dotnet", "test", "--nologo"))
    content_scan()
    prs = json.loads(run("gh", "pr", "list", "--repo", REPO, "--head", value["branch"],
                         "--base", "main", "--state", "all", "--json", "number,url,state"))
    if any(pr["state"] != "OPEN" for pr in prs):
        raise RuntimeError("This branch already has a closed or merged PR. Start a fresh delivery.")
    if files:
        run("git", "add", "--", *files)
    if run("git", "diff", "--cached", "--name-only"):
        run("git", "diff", "--cached", "--check")
        run("git", "commit", "-m", f"feat: implement {Path(value['feature']).name}", "-m", TRAILER)
    if run("git", "rev-parse", "HEAD") == value["base"]:
        raise RuntimeError("No feature commit to publish.")
    authenticate()
    content_scan()
    run("git", "push", "--set-upstream", "origin", f"HEAD:refs/heads/{value['branch']}")
    body = (f"## Feature\n\n`{value['feature']}`\n\n"
            "Generated with Spec Kit; reviewed at intent, design, issue creation, and publication gates.\n\n"
            "## Verification\n\n`dotnet test --nologo` passed before publication.\n\n"
            "## Tracked tasks\n\n" +
            "\n".join(f"Closes #{item['number']}" for item in links.values()) +
            "\n\nHuman code review and CI are required before marking ready or merging.\n")
    if prs:
        run("gh", "pr", "edit", str(prs[0]["number"]), "--repo", REPO, "--body", body, "--add-label", "demo")
        print(prs[0]["url"])
    else:
        print(run("gh", "pr", "create", "--repo", REPO, "--base", "main", "--head", value["branch"],
                  "--draft", "--label", "demo", "--title", f"feat: {Path(value['feature']).name}",
                  "--body", body))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["prepare", "issues", "verify-issues", "review", "publish"])
    action = parser.parse_args().action
    try:
        if Path(run("git", "rev-parse", "--show-toplevel")).resolve() != Path.cwd().resolve():
            raise RuntimeError("Run from the root of the delivery worktree.")
        if action == "prepare":
            prepare()
        elif action in ("issues", "verify-issues"):
            issues(create=action == "issues")
        elif action == "review":
            review()
        else:
            publish()
    except (RuntimeError, OSError, ValueError, KeyError) as exc:
        print(f"Delivery stopped: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
