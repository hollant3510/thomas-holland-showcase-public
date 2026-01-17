"""Guardrails helpers for git command enforcement."""
from __future__ import annotations

from fnmatch import fnmatch
from typing import Callable


def get_guardrails(config: dict) -> dict:
    """Return guardrails configuration from the router config."""
    guard = config.get("guardrails", {})
    if not isinstance(guard, dict):
        return {}
    return guard


def _current_branch(git_output: Callable[[list[str]], str]) -> str:
    """Return the current git branch name."""
    return git_output(["rev-parse", "--abbrev-ref", "HEAD"])


def _worktree_clean(git_output: Callable[[list[str]], str]) -> bool:
    """Return True when the working tree has no local changes."""
    status = git_output(["status", "--porcelain"])
    return status.strip() == ""


def _is_branch_delete(cmd: str, args: list[str]) -> bool:
    """Return True when the command is deleting a branch."""
    if cmd != "branch":
        return False
    for token in args:
        if token in {"-d", "-D", "--delete"}:
            return True
    return False


def _matches_safe_block(cmd: str, args: list[str], patterns: list[str]) -> bool:
    """Return True when a command matches a safe-mode block pattern."""
    for pattern in patterns:
        parts = [p for p in pattern.split(" ") if p]
        if not parts:
            continue
        if parts[0] != cmd:
            continue
        if len(parts) == 1:
            return True
        if all(part in args for part in parts[1:]):
            return True
    return False


def _branch_matches(name: str, patterns: list[str]) -> bool:
    """Return True when a branch name matches any pattern."""
    return any(fnmatch(name, pattern) for pattern in patterns)


def guardrails_block(
    tool: str,
    args: list[str],
    config: dict,
    git_output: Callable[[list[str]], str],
) -> str | None:
    """Return a guardrail error message when a command should be blocked.

    This evaluates guardrail rules (safe mode, protected branches, clean worktree)
    and returns a user-facing message when the command should not run.
    """
    guard = get_guardrails(config)
    if not guard or not args:
        return None
    if tool != "git":
        return None

    runtime = config.get("_runtime", {}) if isinstance(config.get("_runtime"), dict) else {}
    override = bool(runtime.get("override", False))
    safe_mode = bool(runtime.get("safe_mode", False))
    require_clean_flag = bool(runtime.get("require_clean", False))

    protected_branches = [str(item).strip() for item in guard.get("protected_branches", []) if str(item).strip()]
    protected_patterns = [str(item).strip() for item in guard.get("protected_patterns", []) if str(item).strip()]
    protected_ops = [str(item).strip() for item in guard.get("protected_ops", []) if str(item).strip()]
    require_clean_ops = [str(item).strip() for item in guard.get("require_clean_ops", []) if str(item).strip()]
    safe_block_ops = [str(item).strip() for item in guard.get("safe_block_ops", []) if str(item).strip()]
    enforce_name_ops = [str(item).strip() for item in guard.get("enforce_branch_name_ops", []) if str(item).strip()]
    branch_patterns = [str(item).strip() for item in guard.get("branch_name_patterns", []) if str(item).strip()]
    merge_policies = guard.get("merge_policies", [])

    cmd = args[0]
    cmd_args = args[1:]

    if override:
        return None

    if safe_mode:
        if _matches_safe_block(cmd, cmd_args, safe_block_ops):
            return "router guardrails: blocked by safe mode"

    branch_delete = _is_branch_delete(cmd, cmd_args)
    needs_clean = require_clean_flag or cmd in require_clean_ops
    if cmd == "branch":
        needs_clean = needs_clean and branch_delete
    if needs_clean:
        if not _worktree_clean(git_output):
            return "router guardrails: worktree not clean (use --override to proceed)"

    branch = _current_branch(git_output)
    if branch in protected_branches or _branch_matches(branch, protected_patterns):
        if (cmd in protected_ops and cmd != "branch") or (cmd == "branch" and branch_delete):
            return f"router guardrails: blocked on protected branch '{branch}'"

    if branch_patterns and (cmd in enforce_name_ops):
        if not _branch_matches(branch, branch_patterns):
            return "router guardrails: branch name does not match allowed patterns"

    if cmd == "merge":
        for rule in merge_policies or []:
            if not isinstance(rule, dict):
                continue
            target = str(rule.get("target", "")).strip()
            if target and target == branch:
                allowed = [str(item).strip() for item in rule.get("allowed_sources", []) if str(item).strip()]
                if allowed:
                    source = ""
                    for token in cmd_args:
                        if token.startswith("-"):
                            continue
                        source = token
                    if source and source not in allowed:
                        return f"router guardrails: merge into {branch} allowed only from {', '.join(allowed)}"

    return None
