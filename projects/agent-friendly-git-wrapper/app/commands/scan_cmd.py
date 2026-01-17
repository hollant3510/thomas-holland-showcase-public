"""Handle the router scan command."""
from __future__ import annotations

import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Callable

from app.cli.cli_parse import _parse_list_arg


def _scan_conflicts(paths: list[str], exclude_patterns: list[str]) -> list[tuple[str, int, str]]:
    """Scan files for merge conflict markers."""
    results: list[tuple[str, int, str]] = []
    markers = ("<<<<<<<", "=======", ">>>>>>>")
    for raw_path in paths:
        root = Path(raw_path)
        if root.is_file():
            candidates = [root]
        else:
            candidates = [p for p in root.rglob("*") if p.is_file()]
        for file_path in candidates:
            rel = file_path.as_posix()
            if "/.git/" in rel:
                continue
            if any(fnmatch(rel, pattern) for pattern in exclude_patterns):
                continue
            try:
                text = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for idx, line in enumerate(text.splitlines(), start=1):
                for marker in markers:
                    if marker in line:
                        results.append((str(file_path), idx, marker))
                        break
    return results


def dispatch_scan(
    args: list[str],
    config: dict,
    get_guardrails: Callable[[dict], dict],
) -> int:
    """Dispatch scan subcommands for safety checks."""
    if not args:
        raise RuntimeError("router scan: subcommand required")
    sub = args[0]
    rest = args[1:]
    guard = get_guardrails(config)
    scan_cfg = guard.get("conflict_scan", {}) if isinstance(guard.get("conflict_scan"), dict) else {}

    if sub in {"-h", "--help"}:
        sys.stdout.write("usage: router scan conflicts [--paths PATH[,PATH]]\n")
        return 0

    if sub != "conflicts":
        raise RuntimeError(f"router scan: unknown subcommand '{sub}'")

    paths: list[str] = []
    idx = 0
    while idx < len(rest):
        token = rest[idx]
        if token in {"-h", "--help"}:
            sys.stdout.write("usage: router scan conflicts [--paths PATH[,PATH]]\n")
            return 0
        if token == "--paths":
            if idx + 1 >= len(rest):
                raise RuntimeError("router scan conflicts: --paths requires a value")
            paths.extend(_parse_list_arg(rest[idx + 1]))
            idx += 2
            continue
        raise RuntimeError(f"router scan conflicts: unknown argument '{token}'")

    if not paths:
        paths = [str(p) for p in scan_cfg.get("paths", []) if str(p).strip()]
    if not paths:
        paths = ["."]

    exclude_patterns = [str(p).strip() for p in scan_cfg.get("exclude_patterns", []) if str(p).strip()]
    results = _scan_conflicts(paths, exclude_patterns)

    sys.stdout.write("conflicts:\n")
    for path, line_no, marker in results:
        sys.stdout.write(f"  {path}:{line_no} {marker}\n")
    sys.stdout.write(f"conflict_count: {len(results)}\n")
    return 0


