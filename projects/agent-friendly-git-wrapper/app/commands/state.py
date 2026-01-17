"""Handle the router state command."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable, Sequence


def _detect_ops(git_dir: Path) -> list[str]:
    """Detect in-progress git operations based on git-dir markers."""
    ops = []
    if (git_dir / "MERGE_HEAD").exists():
        ops.append("merge")
    if (git_dir / "REBASE_HEAD").exists() or (git_dir / "rebase-apply").exists() or (git_dir / "rebase-merge").exists():
        ops.append("rebase")
    if (git_dir / "CHERRY_PICK_HEAD").exists():
        ops.append("cherry-pick")
    if (git_dir / "BISECT_LOG").exists():
        ops.append("bisect")
    if (git_dir / "sequencer").exists():
        ops.append("sequencer")
    return ops


def dispatch_state(
    args: list[str],
    config: dict,
    git_output: Callable[[Sequence[str]], str],
) -> int:
    """Print a compact snapshot of repo state and worktree status."""
    branch = ""
    base = ""
    idx = 0
    while idx < len(args):
        token = args[idx]
        if token in {"-h", "--help"}:
            sys.stdout.write("usage: router state [--branch NAME] [--base NAME]\n")
            return 0
        if token == "--branch":
            if idx + 1 >= len(args):
                raise RuntimeError("router state: --branch requires a value")
            branch = args[idx + 1]
            idx += 2
            continue
        if token == "--base":
            if idx + 1 >= len(args):
                raise RuntimeError("router state: --base requires a value")
            base = args[idx + 1]
            idx += 2
            continue
        raise RuntimeError(f"router state: unknown argument '{token}'")

    repo_root = git_output(["rev-parse", "--show-toplevel"])
    current_branch = git_output(["rev-parse", "--abbrev-ref", "HEAD"])
    target_branch = branch or current_branch
    head_full = git_output(["rev-parse", target_branch])
    head_short = git_output(["rev-parse", "--short", target_branch])

    worktree_dirty = False
    dirty_count = 0
    status = git_output(["status", "--porcelain"]).splitlines()
    if status:
        worktree_dirty = True
        dirty_count = len(status)

    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    if not base:
        base = str(router_cfg.get("default_base", "")).strip()
    ahead = "?"
    behind = "?"
    base_exists = True
    if base:
        try:
            counts = git_output(["rev-list", "--left-right", "--count", f"{base}...{target_branch}"])
            parts = counts.split()
            if len(parts) >= 2:
                behind = parts[0]
                ahead = parts[1]
        except RuntimeError:
            base_exists = False

    upstream = ""
    try:
        upstream = git_output(["rev-parse", "--abbrev-ref", "--symbolic-full-name", f"{target_branch}@{{u}}"])
    except RuntimeError:
        upstream = ""

    git_dir = Path(git_output(["rev-parse", "--git-dir"]))
    if not git_dir.is_absolute():
        git_dir = Path(repo_root) / git_dir
    ops = _detect_ops(git_dir)

    sys.stdout.write(f"repo: {repo_root}\n")
    sys.stdout.write(f"branch: {target_branch}\n")
    if target_branch != current_branch:
        sys.stdout.write(f"worktree_branch: {current_branch}\n")
    sys.stdout.write(f"head: {head_short}\n")
    sys.stdout.write(f"head_full: {head_full}\n")
    sys.stdout.write(f"worktree: {'dirty' if worktree_dirty else 'clean'}\n")
    sys.stdout.write(f"dirty_count: {dirty_count}\n")
    if base:
        sys.stdout.write(f"base: {base}\n")
        if not base_exists:
            sys.stdout.write("base_exists: no\n")
        sys.stdout.write(f"behind: {behind}\n")
        sys.stdout.write(f"ahead: {ahead}\n")
    if upstream:
        sys.stdout.write(f"upstream: {upstream}\n")
    sys.stdout.write(f"ops: {','.join(ops) if ops else 'none'}\n")
    return 0

