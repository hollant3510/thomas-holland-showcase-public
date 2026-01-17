"""Routing helpers for command selection and dispatch."""
from __future__ import annotations

import difflib
import sys
from typing import Callable, Dict, Sequence

DEFAULT_COMMANDS = {
    "state": {"enabled": True, "handler": "state"},
}

_EXTRA_SUGGESTIONS = [
    "pr status",
    "pr merge-state",
    "pr view",
    "pr open-draft",
    "pr open+status",
    "pr ready+merge-state",
    "pr create",
    "pr update",
    "branch report-merged",
    "branch cleanup-merged",
    "branch audit-unmerged",
    "branch prune-local",
    "branch sync-report",
    "branch validate-name",
    "scan conflicts",
]


def suggest_commands(command: str, config: dict) -> list[str]:
    """Return close matches to help when a command is unknown."""
    candidates: list[str] = []
    commands = load_commands(config)
    candidates.extend(list(commands.keys()))
    custom = config.get("custom_commands", {}) if isinstance(config.get("custom_commands"), dict) else {}
    candidates.extend([str(k).strip().lower() for k in custom.keys() if str(k).strip()])
    candidates.extend(_EXTRA_SUGGESTIONS)
    unique = sorted({item for item in candidates if item})
    return difflib.get_close_matches(command, unique, n=3, cutoff=0.4)


def load_commands(config: dict) -> Dict[str, dict]:
    """Load built-in commands and apply config overrides."""
    commands: Dict[str, dict] = {}
    for name, meta in DEFAULT_COMMANDS.items():
        commands[name] = dict(meta)
    configured = config.get("commands", {})
    if isinstance(configured, dict):
        for key, value in configured.items():
            cmd = str(key).strip().lower()
            if not cmd:
                continue
            if isinstance(value, dict):
                merged = dict(commands.get(cmd, {}))
                merged.update(value)
                commands[cmd] = merged
            else:
                commands[cmd] = {"enabled": bool(value)}
    return commands


def _lower_set(values: Sequence[str] | None) -> set[str]:
    """Convert a list of strings into a lowercase set."""
    return {str(v).strip().lower() for v in (values or []) if str(v).strip()}


def _normalize_overrides(section: dict | None) -> Dict[str, bool]:
    """Convert override keys to lowercase booleans."""
    overrides: Dict[str, bool] = {}
    if not isinstance(section, dict):
        return overrides
    for key, value in section.items():
        cmd = str(key).strip().lower()
        if not cmd:
            continue
        overrides[cmd] = bool(value)
    return overrides


def pick_tool(command: str, tool_override: str, config: dict) -> str:
    """Pick git or gh for a command using config and overrides."""
    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    overlap_default = str(router_cfg.get("overlap_default", "git")).strip().lower() or "git"
    enable_git = bool(router_cfg.get("enable_git", True))
    enable_gh = bool(router_cfg.get("enable_gh", True))
    unknown_policy = str(router_cfg.get("unknown_command_policy", "passthrough")).strip().lower()

    if tool_override:
        return tool_override

    overlap = config.get("overlap_commands", {}) if isinstance(config.get("overlap_commands"), dict) else {}
    overlap_defaults = {
        str(k).strip().lower(): str(v.get("default", overlap_default)).strip().lower()
        for k, v in overlap.items()
        if isinstance(v, dict)
    }
    git_only = _lower_set(config.get("git_only_commands", []))
    gh_only = _lower_set(config.get("gh_only_commands", []))

    if command in overlap_defaults:
        preferred = overlap_defaults[command]
        if preferred == "git" and enable_git:
            return "git"
        if preferred == "gh" and enable_gh:
            return "gh"
        if enable_git:
            return "git"
        if enable_gh:
            return "gh"
        return preferred

    if command in git_only:
        return "git"
    if command in gh_only:
        return "gh"

    if unknown_policy == "passthrough":
        if overlap_default == "git" and enable_git:
            return "git"
        if overlap_default == "gh" and enable_gh:
            return "gh"
        if enable_git:
            return "git"
        if enable_gh:
            return "gh"
        return overlap_default

    suggestions = suggest_commands(command, config) if command else []
    message = f"router: unrecognized command '{command}'."
    if suggestions:
        message += "\nDid you mean: " + ", ".join(suggestions)
    raise RuntimeError(message)


def command_allowed(tool: str, command: str, config: dict) -> bool:
    """Return True when a command is allowed for the tool."""
    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    default_enabled = bool(router_cfg.get("default_command_enabled", True))
    overrides = config.get("command_overrides", {}) if isinstance(config.get("command_overrides"), dict) else {}
    tool_overrides = _normalize_overrides(overrides.get(tool, {}))
    if command in tool_overrides:
        return tool_overrides[command]
    return default_enabled


def tool_enabled(tool: str, config: dict) -> bool:
    """Return True when a tool is enabled in config."""
    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    if tool == "git":
        return bool(router_cfg.get("enable_git", True))
    if tool == "gh":
        return bool(router_cfg.get("enable_gh", True))
    return False


def dispatch_custom(
    command: str,
    config: dict,
    pick_tool_func: Callable[[str, str, dict], str],
    tool_enabled_func: Callable[[str, dict], bool],
    command_allowed_func: Callable[[str, str, dict], bool],
    guardrails_block: Callable[[str, list[str], dict, Callable[[list[str]], str]], str | None],
    run_tool: Callable[..., object],
    git_output: Callable[[list[str]], str],
) -> int | None:
    """Run a custom command sequence from config."""
    custom = config.get("custom_commands", {}) if isinstance(config.get("custom_commands"), dict) else {}
    entry = custom.get(command)
    if entry is None:
        return None
    if isinstance(entry, dict):
        steps = entry.get("steps", [])
    else:
        steps = entry
    if not isinstance(steps, list):
        raise RuntimeError(f"Custom command '{command}' has invalid steps.")
    for step in steps:
        if isinstance(step, str):
            raise RuntimeError(f"Custom command '{command}' steps must be dicts.")
        if not isinstance(step, dict):
            raise RuntimeError(f"Custom command '{command}' steps must be dicts.")
        tool = str(step.get("tool", "")).strip().lower()
        args = step.get("args", [])
        if not isinstance(args, list) or not args:
            raise RuntimeError(f"Custom command '{command}' has invalid args.")
        if tool:
            selected = tool
        else:
            selected = pick_tool_func(str(args[0]).strip().lower(), "", config)
        if not tool_enabled_func(selected, config):
            raise RuntimeError(f"router: {selected} is disabled by config")
        cmd_name = str(args[0]).strip().lower()
        if cmd_name and not command_allowed_func(selected, cmd_name, config):
            raise RuntimeError(f"router: {selected} {cmd_name} denied by config")
        guard_err = guardrails_block(selected, [str(a) for a in args], config, git_output)
        if guard_err:
            raise RuntimeError(guard_err)
        proc = run_tool(
            selected,
            [str(a) for a in args],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.stdout:
            sys.stdout.write(proc.stdout)
        if proc.stderr:
            sys.stderr.write(proc.stderr)
        if proc.returncode != 0:
            return proc.returncode
    return 0


def dispatch_builtin(
    command: str,
    args: list[str],
    config: dict,
    handlers: dict[str, Callable[[list[str], dict], int]],
) -> int | None:
    """Run a built-in router command when configured."""
    commands = load_commands(config)
    meta = commands.get(command)
    if meta is None:
        return None
    if not bool(meta.get("enabled", True)):
        raise RuntimeError(f"router: command '{command}' is disabled by config")
    handler = str(meta.get("handler", "")).strip().lower() or command
    func = handlers.get(handler)
    if func is None:
        raise RuntimeError(f"router: unknown builtin handler '{handler}' for command '{command}'")
    return func(args, config)
