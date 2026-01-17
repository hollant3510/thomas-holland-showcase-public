"""Runtime helpers for router execution context."""
from __future__ import annotations

from typing import Sequence


class RuntimeContext:
    """Hold runtime config and helpers for router execution."""

    def __init__(self) -> None:
        """Initialize an empty runtime context."""
        self.config: dict | None = None

    def set_config(self, config: dict | None) -> None:
        """Set the active runtime configuration dict."""
        self.config = config if isinstance(config, dict) else None

    def get_config(self) -> dict | None:
        """Return the active runtime configuration dict."""
        return self.config

    def record_resolved(self, tool: str, args: Sequence[str]) -> None:
        """Store a resolved command entry for logging."""
        runtime = self.get_config()
        if not runtime:
            return
        meta = runtime.get("_runtime")
        if not isinstance(meta, dict):
            return
        resolved = meta.setdefault("resolved_commands", [])
        if isinstance(resolved, list):
            resolved.append({"tool": tool, "args": [str(a) for a in args]})

    def get_timeout(self) -> float | None:
        """Return a timeout value based on router config."""
        runtime = self.get_config()
        if not runtime:
            return None
        router_cfg = runtime.get("router", {}) if isinstance(runtime.get("router"), dict) else {}
        timeout = router_cfg.get("command_timeout")
        if timeout is None:
            return None
        try:
            value = float(timeout)
        except (TypeError, ValueError):
            raise RuntimeError("router.command_timeout must be a number")
        if value <= 0:
            return None
        return value
