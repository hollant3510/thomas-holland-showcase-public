"""Handle the router show command."""
from __future__ import annotations

import sys
from typing import Callable

from app.cli.cli_parse import _validate_stat_name_status


def dispatch_show(
    args: list[str],
    config: dict,
    run_git: Callable[..., object],
) -> int:
    """Show commit metadata and optional diff details."""
    commit = ""
    include_patch = False
    include_stat = False
    include_name_status = False
    oneline = False
    short_hash = False

    idx = 0
    while idx < len(args):
        token = args[idx]
        if token in {"-h", "--help"}:
            sys.stdout.write(
                "usage: router show <sha> [--patch] [--stat] [--name-status] [--oneline] [--short-hash]\n"
            )
            return 0
        if token == "--patch":
            include_patch = True
            idx += 1
            continue
        if token == "--stat":
            include_stat = True
            idx += 1
            continue
        if token == "--name-status":
            include_name_status = True
            idx += 1
            continue
        if token == "--oneline":
            oneline = True
            idx += 1
            continue
        if token == "--short-hash":
            short_hash = True
            idx += 1
            continue
        if token.startswith("-"):
            raise RuntimeError(f"router show: unknown argument '{token}'")
        if not commit:
            commit = token
            idx += 1
            continue
        raise RuntimeError(f"router show: unexpected argument '{token}'")

    if not commit:
        raise RuntimeError("router show: commit sha is required")
    _validate_stat_name_status("show", include_stat, include_name_status)

    show_args = ["show", commit]
    if short_hash:
        oneline = True
        show_args.append("--abbrev-commit")
    if oneline:
        show_args.append("--pretty=oneline")
    else:
        show_args.append("--pretty=fuller")

    if include_patch:
        show_args.append("--patch")
    elif include_stat:
        show_args.append("--stat")
    elif include_name_status:
        show_args.append("--name-status")

    proc = run_git(
        show_args,
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


