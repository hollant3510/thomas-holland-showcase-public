"""Handle the router base command."""
from __future__ import annotations

import sys
from typing import Callable


def dispatch_base(
    args: list[str],
    config: dict,
    git_output: Callable[[list[str]], str],
) -> int:
    """Resolve and print the merge-base between a branch and base."""
    base = ""
    branch = ""

    idx = 0
    while idx < len(args):
        token = args[idx]
        if token in {"-h", "--help"}:
            sys.stdout.write("usage: router base [--base NAME] [--branch NAME]\n")
            return 0
        if token == "--base":
            if idx + 1 >= len(args):
                raise RuntimeError("router base: --base requires a value")
            base = args[idx + 1].strip()
            idx += 2
            continue
        if token == "--branch":
            if idx + 1 >= len(args):
                raise RuntimeError("router base: --branch requires a value")
            branch = args[idx + 1].strip()
            idx += 2
            continue
        raise RuntimeError(f"router base: unknown argument '{token}'")

    if not branch:
        branch = git_output(["rev-parse", "--abbrev-ref", "HEAD"])
    if not base:
        router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
        base = str(router_cfg.get("default_base", "")).strip()
    if not base:
        raise RuntimeError("router base: base branch required (set default_base or --base)")

    merge_base = git_output(["merge-base", base, branch])
    merge_short = git_output(["rev-parse", "--short", merge_base])

    sys.stdout.write(f"base: {base}\n")
    sys.stdout.write(f"target: {branch}\n")
    sys.stdout.write(f"merge_base: {merge_base}\n")
    sys.stdout.write(f"merge_base_short: {merge_short}\n")
    return 0

