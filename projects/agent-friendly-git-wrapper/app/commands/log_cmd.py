"""Handle the router log command."""
from __future__ import annotations

import sys
from typing import Callable

from app.cli.cli_parse import _parse_log_like_args


def dispatch_log(
    args: list[str],
    config: dict,
    run_git: Callable[..., object],
) -> int:
    """Render a concise git log based on the provided options."""
    if "-h" in args or "--help" in args:
        sys.stdout.write(
            "usage: router log --n N [--since REF|--range A..B] [--path PATH] [--short-hash]\n"
        )
        return 0

    parsed, rest = _parse_log_like_args(args, "log")
    if rest:
        raise RuntimeError(f"router log: unknown argument '{rest[0]}'")
    count = parsed["count"]
    since = parsed["since"]
    rev_range = parsed["rev_range"]
    path = parsed["path"]
    short_hash = parsed["short_hash"]

    if rev_range and since:
        raise RuntimeError("router log: use either --since or --range, not both")

    log_args = ["log"]
    if count is not None:
        log_args.append(f"--max-count={count}")

    if rev_range:
        log_args.append(rev_range)
    elif since:
        log_args.append(f"{since}..HEAD")

    if short_hash:
        log_args.append("--abbrev-commit")
        log_args.append("--pretty=format:%h %s")
    else:
        log_args.append("--pretty=format:%H %s")

    if path:
        log_args.append("--")
        log_args.append(path)

    proc = run_git(
        log_args,
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


