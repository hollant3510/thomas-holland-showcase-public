"""Handle the router files command."""
from __future__ import annotations

import sys
from typing import Callable

from app.cli.cli_parse import _validate_stat_name_status


def dispatch_files(
    args: list[str],
    config: dict,
    git_output: Callable[[list[str]], str],
    run_git: Callable[..., object],
) -> int:
    """Report changed files for commits, ranges, or working state."""
    mode = ""
    commit = ""
    rev_range = ""
    since_branch = ""
    show_stat = False
    show_name_status = False

    idx = 0
    while idx < len(args):
        token = args[idx]
        if token in {"-h", "--help"}:
            sys.stdout.write(
                "usage: router files --changed | --commit SHA | --range A..B | --since-branch [NAME]\n"
                "                    [--stat | --name-status]\n"
            )
            return 0
        if token == "--changed":
            mode = "changed"
            idx += 1
            continue
        if token == "--commit":
            if idx + 1 >= len(args):
                raise RuntimeError("router files: --commit requires a value")
            mode = "commit"
            commit = args[idx + 1].strip()
            idx += 2
            continue
        if token == "--range":
            if idx + 1 >= len(args):
                raise RuntimeError("router files: --range requires a value")
            mode = "range"
            rev_range = args[idx + 1].strip()
            idx += 2
            continue
        if token == "--since-branch":
            mode = "since-branch"
            if idx + 1 < len(args) and not args[idx + 1].startswith("-"):
                since_branch = args[idx + 1].strip()
                idx += 2
            else:
                idx += 1
            continue
        if token == "--stat":
            show_stat = True
            idx += 1
            continue
        if token == "--name-status":
            show_name_status = True
            idx += 1
            continue
        raise RuntimeError(f"router files: unknown argument '{token}'")

    _validate_stat_name_status("files", show_stat, show_name_status)

    if not mode:
        raise RuntimeError("router files: choose one of --changed, --commit, --range, --since-branch")

    if mode == "since-branch":
        if not since_branch:
            router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
            since_branch = str(router_cfg.get("default_base", "")).strip()
        if not since_branch:
            raise RuntimeError("router files: --since-branch requires a branch or default_base")
        base = git_output(["merge-base", since_branch, "HEAD"])
        rev_range = f"{base}..HEAD"

    args_base: list[str]
    if mode == "commit":
        if not commit:
            raise RuntimeError("router files: --commit requires a value")
        args_base = ["show", commit, "--pretty="]
    else:
        args_base = ["diff"]
        if mode == "changed":
            args_base.append("HEAD")
        elif mode in {"range", "since-branch"}:
            if not rev_range:
                raise RuntimeError("router files: --range requires a value")
            args_base.append(rev_range)

    if show_stat:
        args_base.append("--stat")
    elif show_name_status:
        args_base.append("--name-status")
    else:
        args_base.append("--name-only")

    proc = run_git(
        args_base,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc.returncode


