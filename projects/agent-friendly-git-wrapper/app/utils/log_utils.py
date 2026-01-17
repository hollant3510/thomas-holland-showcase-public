"""Logging helpers for router command runs."""
from __future__ import annotations

import json
from pathlib import Path


class TeeStream:
    """Mirror writes to a real stream while capturing a bounded buffer."""

    def __init__(self, stream, limit: int) -> None:
        """Initialize the tee stream with a buffer limit."""
        self.stream = stream
        self.limit = limit
        self.buffer = ""

    def write(self, data: str) -> int:
        """Write to the wrapped stream and capture up to the limit."""
        self.stream.write(data)
        if self.limit > 0 and len(self.buffer) < self.limit:
            remaining = self.limit - len(self.buffer)
            self.buffer += data[:remaining]
        return len(data)

    def flush(self) -> None:
        """Flush the wrapped stream."""
        self.stream.flush()


def _format_log_entry(entry: dict, fmt: str) -> str:
    """Format a single log entry into the requested format."""
    fmt = fmt.lower()
    if fmt == "json":
        return json.dumps(entry, ensure_ascii=False) + "\n"
    if fmt == "toon":
        def _toon_string(value: str) -> str:
            """Return a quoted TOON-safe scalar string."""
            return json.dumps(str(value), ensure_ascii=False)

        lines: list[str] = []
        lines.append(f"timestamp: {_toon_string(entry.get('timestamp',''))}")
        lines.append(f"command: {_toon_string(entry.get('command',''))}")
        lines.append(f"tool: {_toon_string(entry.get('tool',''))}")
        lines.append(f"exit_code: {entry.get('exit_code','')}")
        args = entry.get("args", []) or []
        args_rendered = ",".join(_toon_string(item) for item in args)
        lines.append(f"args[{len(args)}]: {args_rendered}")
        resolved = entry.get("resolved", []) or []
        lines.append(f"resolved[{len(resolved)}]:")
        for item in resolved:
            tool = item.get("tool", "")
            r_args = item.get("args", []) or []
            lines.append(f"  - tool: {_toon_string(tool)}")
            r_args_rendered = ",".join(_toon_string(val) for val in r_args)
            lines.append(f"    args[{len(r_args)}]: {r_args_rendered}")
        stdout = entry.get("stdout", "")
        stderr = entry.get("stderr", "")
        lines.append(f"stdout: {_toon_string(stdout)}")
        lines.append(f"stderr: {_toon_string(stderr)}")
        return "\n".join(lines) + "\n\n"
    # Plain-text format.
    lines = [
        f"timestamp: {entry.get('timestamp','')}",
        f"command: {entry.get('command','')}",
        f"tool: {entry.get('tool','')}",
        f"exit_code: {entry.get('exit_code','')}",
        f"args: {' '.join(entry.get('args', []) or [])}",
    ]
    resolved = entry.get("resolved", []) or []
    if resolved:
        lines.append("resolved:")
        for item in resolved:
            tool_name = item.get("tool", "")
            tool_args = " ".join(item.get("args", []) or [])
            lines.append(f"  - {tool_name} {tool_args}")
    if entry.get("stdout"):
        lines.append(f"stdout: {entry.get('stdout')}")
    if entry.get("stderr"):
        lines.append(f"stderr: {entry.get('stderr')}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def write_log_entries(entries: list[dict], log_file: str, fmt: str) -> None:
    """Append formatted log entries to the configured log file."""
    if not entries:
        return
    path = Path(log_file)
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(_format_log_entry(entry, fmt))
