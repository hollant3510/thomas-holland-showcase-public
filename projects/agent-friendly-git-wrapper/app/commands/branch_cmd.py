"""Handle the router branch command."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from fnmatch import fnmatch
from typing import Callable


def _get_branch_config(config: dict) -> dict:
    """Return branch hygiene configuration from the router config."""
    branch_cfg = config.get("branch_hygiene", {})
    if not isinstance(branch_cfg, dict):
        return {}
    return branch_cfg


def _match_any(name: str, patterns: list[str]) -> bool:
    """Return True when a name matches any glob pattern."""
    for pattern in patterns:
        if fnmatch(name, pattern):
            return True
    return False


def _ref_exists(ref: str, run_git: Callable[..., object]) -> bool:
    """Return True when a ref exists in git."""
    proc = run_git(["show-ref", "--verify", "--quiet", ref], check=False)
    return proc.returncode == 0


def _load_branches(remote: str, include_remotes: bool, run_git: Callable[..., object]) -> list[dict]:
    """Load branch metadata for local (and optionally remote) refs."""
    entries: list[dict] = []
    fmt = "%(refname:short)|%(objectname)|%(committerdate:iso8601-strict)|%(authorname)|%(upstream:short)"
    proc = run_git(
        ["for-each-ref", f"--format={fmt}", "refs/heads"],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    for line in proc.stdout.splitlines():
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        name, sha, date_str, author, upstream = parts
        entries.append(
            {
                "name": name,
                "ref": f"refs/heads/{name}",
                "sha": sha,
                "date": date_str,
                "author": author,
                "upstream": upstream,
                "location": "local",
            }
        )
    if include_remotes:
        proc = run_git(
            ["for-each-ref", f"--format={fmt}", f"refs/remotes/{remote}"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for line in proc.stdout.splitlines():
            parts = line.split("|", 4)
            if len(parts) < 5:
                continue
            name, sha, date_str, author, upstream = parts
            if name.endswith("/HEAD"):
                continue
            entries.append(
                {
                    "name": name,
                    "ref": f"refs/remotes/{name}",
                    "sha": sha,
                    "date": date_str,
                    "author": author,
                    "upstream": upstream,
                    "location": "remote",
                }
            )
    return entries


def _parse_iso_date(date_str: str) -> datetime | None:
    """Parse an ISO8601 timestamp into a datetime."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return None


def _age_days(date_str: str) -> int:
    """Return the age of a commit date in whole days."""
    dt = _parse_iso_date(date_str)
    if not dt:
        return -1
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    return int(delta.total_seconds() // 86400)


def _merge_policy_status(base: str, branch: str, policies: list[dict]) -> str:
    """Return merge-policy status for a branch relative to a base."""
    for rule in policies:
        if not isinstance(rule, dict):
            continue
        target = str(rule.get("target", "")).strip()
        if not target or target != base:
            continue
        allowed = rule.get("allowed_sources", [])
        allowed_list = [str(item).strip() for item in allowed if str(item).strip()]
        if allowed_list and branch not in allowed_list:
            return "blocked"
    return "ok"


def dispatch_branch(
    args: list[str],
    config: dict,
    git_output: Callable[[list[str]], str],
    run_git: Callable[..., object],
) -> int:
    """Dispatch branch hygiene subcommands."""
    if not args:
        raise RuntimeError("router branch: subcommand required")

    sub = args[0]
    rest = args[1:]
    branch_cfg = _get_branch_config(config)
    base_default = str(branch_cfg.get("default_base", "")).strip()
    if not base_default:
        router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
        base_default = str(router_cfg.get("default_base", "")).strip()
    remote_default = str(branch_cfg.get("default_remote", "origin")).strip() or "origin"
    include_remotes = bool(branch_cfg.get("include_remotes", True))
    fetch_before = bool(branch_cfg.get("fetch_before", True))
    protected_branches = [str(item).strip() for item in branch_cfg.get("protected_branches", []) if str(item).strip()]
    protected_patterns = [str(item).strip() for item in branch_cfg.get("protected_patterns", []) if str(item).strip()]
    ignore_patterns = [str(item).strip() for item in branch_cfg.get("ignore_patterns", []) if str(item).strip()]
    merge_policies = branch_cfg.get("merge_policies", [])
    cleanup_cfg = branch_cfg.get("cleanup", {}) if isinstance(branch_cfg.get("cleanup"), dict) else {}
    prune_cfg = branch_cfg.get("prune", {}) if isinstance(branch_cfg.get("prune"), dict) else {}

    if sub in {"-h", "--help"}:
        sys.stdout.write(
            "usage: router branch <report-merged|cleanup-merged|audit-unmerged|prune-local|sync-report> [...]\n"
        )
        return 0

    def is_protected(name: str) -> bool:
        """Return True when the branch is protected by name or pattern."""
        if name in protected_branches:
            return True
        if _match_any(name, protected_patterns):
            return True
        return False

    def is_ignored(name: str) -> bool:
        """Return True when a branch matches ignore patterns."""
        return _match_any(name, ignore_patterns)

    runtime = config.get("_runtime", {}) if isinstance(config.get("_runtime"), dict) else {}
    safe_mode = bool(runtime.get("safe_mode", False))
    override = bool(runtime.get("override", False))

    if sub == "report-merged":
        base = base_default
        remote = remote_default
        include = include_remotes
        idx = 0
        while idx < len(rest):
            token = rest[idx]
            if token in {"-h", "--help"}:
                sys.stdout.write("usage: router branch report-merged [--base BRANCH] [--remote NAME]\n")
                return 0
            if token == "--base":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router branch report-merged: --base requires a value")
                base = rest[idx + 1].strip()
                idx += 2
                continue
            if token == "--remote":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router branch report-merged: --remote requires a value")
                remote = rest[idx + 1].strip()
                idx += 2
                continue
            if token == "--local-only":
                include = False
                idx += 1
                continue
            raise RuntimeError(f"router branch report-merged: unknown argument '{token}'")
        if not base:
            raise RuntimeError("router branch report-merged: base branch required")
        if fetch_before:
            run_git(["fetch", remote, base], check=False, capture_output=True)
        branches = _load_branches(remote, include, run_git)
        sys.stdout.write("merged_branches:\n")
        for info in branches:
            name = info["name"]
            if name == base or is_ignored(name):
                continue
            base_ref = base
            if info["location"] == "remote":
                remote_base = f"{remote}/{base}"
                if _ref_exists(f"refs/remotes/{remote}/{base}", run_git):
                    base_ref = remote_base
            if run_git(["merge-base", "--is-ancestor", info["ref"], base_ref], check=False).returncode != 0:
                continue
            policy = _merge_policy_status(base, name, merge_policies)
            age = _age_days(info["date"])
            upstream = info["upstream"] or "-"
            sys.stdout.write(
                f"  merged: {name} location={info['location']} age_days={age} author={info['author']} "
                f"upstream={upstream} policy={policy}\n"
            )
        return 0

    if sub == "cleanup-merged":
        base = base_default
        remote = remote_default
        apply = bool(cleanup_cfg.get("default_apply", False))
        enforce_policy = bool(cleanup_cfg.get("enforce_merge_policy", False))
        idx = 0
        while idx < len(rest):
            token = rest[idx]
            if token in {"-h", "--help"}:
                sys.stdout.write(
                    "usage: router branch cleanup-merged [--base BRANCH] [--remote NAME] [--dry-run|--apply]\n"
                )
                return 0
            if token == "--base":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router branch cleanup-merged: --base requires a value")
                base = rest[idx + 1].strip()
                idx += 2
                continue
            if token == "--remote":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router branch cleanup-merged: --remote requires a value")
                remote = rest[idx + 1].strip()
                idx += 2
                continue
            if token == "--dry-run":
                apply = False
                idx += 1
                continue
            if token in {"--apply", "--no-dry-run"}:
                apply = True
                idx += 1
                continue
            raise RuntimeError(f"router branch cleanup-merged: unknown argument '{token}'")
        if not base:
            raise RuntimeError("router branch cleanup-merged: base branch required")
        if fetch_before:
            run_git(["fetch", remote, base], check=False, capture_output=True)
        current = git_output(["rev-parse", "--abbrev-ref", "HEAD"])
        branches = _load_branches(remote, False, run_git)
        sys.stdout.write("cleanup_merged:\n")
        if safe_mode and not override:
            raise RuntimeError("router branch cleanup-merged blocked by safe mode (use --override to proceed)")
        for info in branches:
            name = info["name"]
            if name == base or is_ignored(name):
                continue
            if run_git(["merge-base", "--is-ancestor", info["ref"], base], check=False).returncode != 0:
                continue
            if is_protected(name):
                sys.stdout.write(f"  cleanup: skip-protected {name}\n")
                continue
            if name == current:
                sys.stdout.write(f"  cleanup: skip-current {name}\n")
                continue
            policy = _merge_policy_status(base, name, merge_policies)
            if enforce_policy and policy == "blocked":
                sys.stdout.write(f"  cleanup: policy-blocked {name}\n")
                continue
            if not apply:
                sys.stdout.write(f"  cleanup: dry-run {name}\n")
                continue
            proc = run_git(["branch", "-d", name], check=False, capture_output=True, text=True)
            if proc.returncode == 0:
                sys.stdout.write(f"  cleanup: deleted {name}\n")
            else:
                sys.stdout.write(f"  cleanup: failed {name}\n")
        return 0

    if sub == "audit-unmerged":
        base = base_default
        remote = remote_default
        include = include_remotes
        idx = 0
        while idx < len(rest):
            token = rest[idx]
            if token in {"-h", "--help"}:
                sys.stdout.write("usage: router branch audit-unmerged [--base BRANCH] [--remote NAME]\n")
                return 0
            if token == "--base":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router branch audit-unmerged: --base requires a value")
                base = rest[idx + 1].strip()
                idx += 2
                continue
            if token == "--remote":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router branch audit-unmerged: --remote requires a value")
                remote = rest[idx + 1].strip()
                idx += 2
                continue
            if token == "--local-only":
                include = False
                idx += 1
                continue
            raise RuntimeError(f"router branch audit-unmerged: unknown argument '{token}'")
        if not base:
            raise RuntimeError("router branch audit-unmerged: base branch required")
        if fetch_before:
            run_git(["fetch", remote, base], check=False, capture_output=True)
        branches = _load_branches(remote, include, run_git)
        sys.stdout.write("unmerged_branches:\n")
        for info in branches:
            name = info["name"]
            if name == base or is_ignored(name):
                continue
            base_ref = base
            if info["location"] == "remote":
                remote_base = f"{remote}/{base}"
                if _ref_exists(f"refs/remotes/{remote}/{base}", run_git):
                    base_ref = remote_base
            if run_git(["merge-base", "--is-ancestor", info["ref"], base_ref], check=False).returncode == 0:
                continue
            counts = git_output(["rev-list", "--left-right", "--count", f"{base_ref}...{info['ref']}"])
            behind, ahead = counts.split()
            policy = _merge_policy_status(base, name, merge_policies)
            age = _age_days(info["date"])
            upstream = info["upstream"] or "-"
            sys.stdout.write(
                f"  unmerged: {name} location={info['location']} age_days={age} author={info['author']} "
                f"upstream={upstream} ahead={ahead} behind={behind} policy={policy}\n"
            )
        return 0

    if sub == "prune-local":
        remote = remote_default
        apply = bool(prune_cfg.get("default_apply", False))
        pattern = str(prune_cfg.get("pattern", "")).strip()
        idx = 0
        while idx < len(rest):
            token = rest[idx]
            if token in {"-h", "--help"}:
                sys.stdout.write(
                    "usage: router branch prune-local [--remote NAME] [--pattern GLOB] [--dry-run|--apply]\n"
                )
                return 0
            if token == "--remote":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router branch prune-local: --remote requires a value")
                remote = rest[idx + 1].strip()
                idx += 2
                continue
            if token == "--pattern":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router branch prune-local: --pattern requires a value")
                pattern = rest[idx + 1].strip()
                idx += 2
                continue
            if token == "--dry-run":
                apply = False
                idx += 1
                continue
            if token in {"--apply", "--no-dry-run"}:
                apply = True
                idx += 1
                continue
            raise RuntimeError(f"router branch prune-local: unknown argument '{token}'")
        if safe_mode and not override:
            raise RuntimeError("router branch prune-local blocked by safe mode (use --override to proceed)")
        if fetch_before:
            run_git(["fetch", remote, "--prune"], check=False, capture_output=True)
        current = git_output(["rev-parse", "--abbrev-ref", "HEAD"])
        proc = run_git(
            ["for-each-ref", "--format=%(refname:short)|%(upstream:short)", "refs/heads"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        sys.stdout.write("prune_local:\n")
        for line in proc.stdout.splitlines():
            parts = line.split("|", 1)
            if len(parts) < 2:
                continue
            name, upstream = parts
            if not upstream:
                continue
            if pattern and not fnmatch(name, pattern):
                continue
            if is_protected(name):
                sys.stdout.write(f"  prune: skip-protected {name}\n")
                continue
            if name == current:
                sys.stdout.write(f"  prune: skip-current {name}\n")
                continue
            if not apply:
                sys.stdout.write(f"  prune: dry-run {name}\n")
                continue
            proc = run_git(["branch", "-D", name], check=False, capture_output=True, text=True)
            if proc.returncode == 0:
                sys.stdout.write(f"  prune: deleted {name}\n")
            else:
                sys.stdout.write(f"  prune: failed {name}\n")
        return 0

    if sub == "sync-report":
        remote = remote_default
        idx = 0
        while idx < len(rest):
            token = rest[idx]
            if token in {"-h", "--help"}:
                sys.stdout.write("usage: router branch sync-report [--remote NAME]\n")
                return 0
            if token == "--remote":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router branch sync-report: --remote requires a value")
                remote = rest[idx + 1].strip()
                idx += 2
                continue
            raise RuntimeError(f"router branch sync-report: unknown argument '{token}'")
        if fetch_before:
            run_git(["fetch", remote, "--prune"], check=False, capture_output=True)
        proc = run_git(
            ["for-each-ref", "--format=%(refname:short)|%(upstream:short)", "refs/heads"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        sys.stdout.write("branch_sync:\n")
        for line in proc.stdout.splitlines():
            parts = line.split("|", 1)
            if len(parts) < 2:
                continue
            name, upstream = parts
            if is_ignored(name):
                continue
            if not upstream:
                sys.stdout.write(f"  sync: {name} upstream=- ahead=0 behind=0 status=missing\n")
                continue
            counts = git_output(["rev-list", "--left-right", "--count", f"{upstream}...{name}"])
            behind, ahead = counts.split()
            status = "in-sync"
            if ahead != "0" and behind != "0":
                status = "diverged"
            elif ahead != "0":
                status = "ahead"
            elif behind != "0":
                status = "behind"
            sys.stdout.write(
                f"  sync: {name} upstream={upstream} ahead={ahead} behind={behind} status={status}\n"
            )
        return 0

    if sub == "validate-name":
        idx = 0
        branch = ""
        override_name = False
        while idx < len(rest):
            token = rest[idx]
            if token in {"-h", "--help"}:
                sys.stdout.write("usage: router branch validate-name [--branch NAME] [--override]\n")
                return 0
            if token == "--branch":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router branch validate-name: --branch requires a value")
                branch = rest[idx + 1].strip()
                idx += 2
                continue
            if token == "--override":
                override_name = True
                idx += 1
                continue
            raise RuntimeError(f"router branch validate-name: unknown argument '{token}'")

        if not branch:
            branch = git_output(["rev-parse", "--abbrev-ref", "HEAD"])
        patterns = branch_cfg.get("name_patterns", [])
        patterns = [str(item).strip() for item in patterns if str(item).strip()]
        if not patterns:
            sys.stdout.write(f"branch: {branch}\n")
            sys.stdout.write("valid: yes (no patterns configured)\n")
            return 0
        if _match_any(branch, patterns):
            sys.stdout.write(f"branch: {branch}\n")
            sys.stdout.write("valid: yes\n")
            return 0
        if override_name:
            sys.stdout.write(f"branch: {branch}\n")
            sys.stdout.write("valid: override\n")
            return 0
        sys.stdout.write(f"branch: {branch}\n")
        sys.stdout.write("valid: no\n")
        return 2

    raise RuntimeError(f"router branch: unknown subcommand '{sub}'")

