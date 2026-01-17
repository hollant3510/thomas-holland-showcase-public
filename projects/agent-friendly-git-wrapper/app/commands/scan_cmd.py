"""Handle the router scan command."""
from __future__ import annotations

import sys
from fnmatch import fnmatch
from pathlib import Path
from typing import Callable

from app.cli.cli_parse import _parse_list_arg


_SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "dist",
    "build",
}


def _is_binary_file(path: Path, sample_bytes: int = 4096) -> bool:
    """Return True if a file looks binary based on a small sample."""
    try:
        sample = path.read_bytes()[:sample_bytes]
    except OSError:
        return False
    return b"\x00" in sample


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
            if any(part in _SKIP_DIRS for part in file_path.parts):
                continue
            if "/.git/" in rel or rel.startswith(".git/"):
                continue
            if any(fnmatch(rel, pattern) for pattern in exclude_patterns):
                continue
            if _is_binary_file(file_path):
                continue
            try:
                text = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for idx, line in enumerate(text.splitlines(), start=1):
                line = line.lstrip("\ufeff")
                for marker in markers:
                    if line.startswith(marker):
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

