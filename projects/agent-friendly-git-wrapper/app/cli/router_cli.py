"""Router for git/gh commands with config-based policies."""
from __future__ import annotations

import argparse
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "cli_router.yaml"
CURRENT_CONFIG: dict | None = None

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.cli.cli_parse import (
    _build_diff_args,
    _build_pathspecs,
    _parse_diff_style_args,
    _parse_list_arg,
    _parse_log_like_args,
    _parse_ops,
    _validate_stat_name_status,
)
from app.commands.base_cmd import dispatch_base as _dispatch_base
from app.commands.branch_cmd import dispatch_branch as _dispatch_branch
from app.commands.compare_cmd import dispatch_compare as _dispatch_compare
from app.commands.diff_cmd import dispatch_diff as _dispatch_diff
from app.commands.files_cmd import dispatch_files as _dispatch_files
from app.commands.history_cmd import dispatch_history as _dispatch_history
from app.commands.log_cmd import dispatch_log as _dispatch_log
from app.commands.pr_cmd import dispatch_pr as _dispatch_pr
from app.commands.scan_cmd import dispatch_scan as _dispatch_scan
from app.commands.show_cmd import dispatch_show as _dispatch_show
from app.commands.state import dispatch_state as _dispatch_state
from app.compact.compact import _apply_compact_options, _render_compact_output
from app.utils.exec_utils import git_output as _git_output_exec
from app.utils.exec_utils import run_gh as _run_gh_exec
from app.utils.exec_utils import run_git as _run_git_exec
from app.utils.exec_utils import run_tool as _run_tool_exec
from app.policy.guardrails import get_guardrails as _get_guardrails
from app.policy.guardrails import guardrails_block as _guardrails_block
from app.utils.log_utils import TeeStream as _TeeStream
from app.utils.log_utils import write_log_entries as _write_log_entries
from app.routing.routing import command_allowed as _command_allowed
from app.routing.routing import dispatch_builtin as _dispatch_builtin
from app.routing.routing import dispatch_custom as _dispatch_custom
from app.routing.routing import pick_tool as _pick_tool
from app.routing.routing import tool_enabled as _tool_enabled
from app.utils.runtime import RuntimeContext
from app.config.config_loader import (
    _deep_merge,
    _load_compact_defaults,
    _load_compact_profiles,
    _load_config,
    _load_default_excludes,
    _load_history_compact_meta_overrides,
    _merge_compact_options,
    _merge_custom_commands,
    _resolve_noise_level,
)

RUNTIME_CONTEXT = RuntimeContext()


def _git_output(args: Sequence[str]) -> str:
    """Run a git command and return stdout."""
    return _git_output_exec(args, RUNTIME_CONTEXT.record_resolved, RUNTIME_CONTEXT.get_timeout)


def _run_git(args: Sequence[str], **kwargs):
    """Run a git command using the configured runtime context."""
    return _run_git_exec(args, RUNTIME_CONTEXT.record_resolved, RUNTIME_CONTEXT.get_timeout, **kwargs)


def _gh_run(args: Sequence[str]):
    """Run a gh command using the configured runtime context."""
    return _run_gh_exec(args, RUNTIME_CONTEXT.record_resolved, RUNTIME_CONTEXT.get_timeout)


def _run_tool(tool: str, args: Sequence[str], **kwargs):
    """Run an arbitrary tool using the configured runtime context."""
    return _run_tool_exec(tool, args, RUNTIME_CONTEXT.record_resolved, RUNTIME_CONTEXT.get_timeout, **kwargs)


def _ensure_gh() -> None:
    """Raise when gh CLI is unavailable."""
    if shutil.which("gh") is None:
        raise RuntimeError("gh CLI not available")


def _builtin_handlers() -> dict[str, Callable[[list[str], dict], int]]:
    """Return the built-in command handler dict."""
    return {
        "state": lambda args, config: _dispatch_state(args, config, _git_output),
        "diff": lambda args, config: _dispatch_diff(args, config, _run_git),
        "log": lambda args, config: _dispatch_log(args, config, _run_git),
        "history": lambda args, config: _dispatch_history(args, config, _run_git),
        "files": lambda args, config: _dispatch_files(args, config, _git_output, _run_git),
        "branch": lambda args, config: _dispatch_branch(args, config, _git_output, _run_git),
        "base": lambda args, config: _dispatch_base(args, config, _git_output),
        "scan": lambda args, config: _dispatch_scan(args, config, _get_guardrails),
        "compare": lambda args, config: _dispatch_compare(args, config, _run_git),
        "show": lambda args, config: _dispatch_show(args, config, _run_git),
        "pr": lambda args, config: _dispatch_pr(args, config, _gh_run, _ensure_gh),
    }


def run(argv: Sequence[str] | None = None) -> int:
    """Execute the router CLI and return an exit code."""
    # Avoid UnicodeEncodeError when routing git output to a legacy Windows console.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Router for git/gh commands.")
    parser.add_argument("--config", default="")
    parser.add_argument("--tool", choices=["git", "gh"], default="")
    parser.add_argument("--check", action="store_true", help="Check routing decision only.")
    parser.add_argument("--override", action="store_true", help="Override guardrails.")
    parser.add_argument("--i-know-what-im-doing", action="store_true", dest="override")
    parser.add_argument("--require-clean", action="store_true", help="Require clean worktree for command.")
    parser.add_argument("--safe", action="store_true", help="Enable safe mode guardrails.")
    parser.add_argument("--profile", default="", help="Set guardrail profile (ex: safe).")
    auto_group = parser.add_mutually_exclusive_group()
    auto_group.add_argument(
        "--auto-tune",
        action="store_true",
        help="Enable compact auto-tune for this invocation.",
    )
    auto_group.add_argument(
        "--no-auto-tune",
        action="store_true",
        help="Disable compact auto-tune for this invocation.",
    )
    parser.add_argument("--log", action="store_true", help="Log this router invocation.")
    parser.add_argument("--log-all", action="store_true", help="Log actions for every invocation.")
    parser.add_argument("--log-file", default="", help="Log file path.")
    parser.add_argument(
        "--log-format",
        default="",
        choices=["json", "toon", "txt"],
        help="Log format (json|toon|txt).",
    )
    parser.add_argument("args", nargs=argparse.REMAINDER)
    parsed = parser.parse_args(argv)

    if not parsed.args:
        parser.error("No command provided.")

    config_path = Path(parsed.config) if parsed.config else DEFAULT_CONFIG
    rc = 0
    command = ""
    args: list[str] = []
    tool_override = ""
    config: dict = {}
    tee_out: _TeeStream | None = None
    tee_err: _TeeStream | None = None
    log_enabled = False
    log_file = ""
    log_format = "txt"
    try:
        # Load config and apply any profile overrides.
        config = _load_config(config_path)
        profiles = config.get("profiles", {}) if isinstance(config.get("profiles"), dict) else {}
        router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
        profile = parsed.profile.strip().lower() or str(router_cfg.get("default_profile", "")).strip().lower()
        if profile:
            if profile not in profiles:
                raise RuntimeError(f"router: unknown profile '{profile}'")
            profile_cfg = profiles.get(profile, {})
            if not isinstance(profile_cfg, dict):
                raise RuntimeError(f"router: profile '{profile}' must be a dict")
            config = _deep_merge(config, profile_cfg)
        router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
        if parsed.auto_tune or parsed.no_auto_tune:
            auto_cfg = router_cfg.get("compact_auto_tune", {})
            if not isinstance(auto_cfg, dict):
                auto_cfg = {}
            auto_cfg["enabled"] = bool(parsed.auto_tune) if parsed.auto_tune else False
            router_cfg["compact_auto_tune"] = auto_cfg
            config["router"] = router_cfg
        # Resolve guardrails, logging, and runtime metadata for this run.
        guardrails_cfg = config.get("guardrails", {}) if isinstance(config.get("guardrails"), dict) else {}
        profile_safe = bool(guardrails_cfg.get("safe_mode", False))
        safe_mode = bool(parsed.safe or profile_safe or profile == "safe")
        log_all = bool(parsed.log_all or router_cfg.get("log_all", False))
        log_enabled = bool(parsed.log or log_all)
        log_file = str(parsed.log_file or router_cfg.get("log_file", "router.log")).strip() or "router.log"
        log_format = str(parsed.log_format or router_cfg.get("log_format", "txt")).strip() or "txt"
        log_max = int(router_cfg.get("log_output_max", 2000))

        config["_runtime"] = {
            "override": bool(parsed.override),
            "require_clean": bool(parsed.require_clean),
            "safe_mode": safe_mode,
            "config_path": str(config_path),
            "profile": profile,
            "resolved_commands": [],
            "resolved_tool": "",
        }
        global CURRENT_CONFIG
        CURRENT_CONFIG = config
        RUNTIME_CONTEXT.set_config(config)

        if log_enabled:
            tee_out = _TeeStream(sys.stdout, log_max)
            tee_err = _TeeStream(sys.stderr, log_max)
            sys.stdout = tee_out
            sys.stderr = tee_err

        # Merge custom command definitions before dispatch.
        _merge_custom_commands(config, config_path)

        args = parsed.args
        tool_override = parsed.tool
        allow_prefixed = bool(router_cfg.get("allow_prefixed", True))
        if args and args[0] in {"git", "gh"}:
            if not allow_prefixed:
                sys.stderr.write("router: prefixed commands are disabled by config\n")
                rc = 2
                return rc
            tool_override = args[0]
            args = args[1:]

        if not args:
            parser.error("No command provided.")

        command = args[0].lstrip().lower()
        if command.startswith("-"):
            command = ""

        if parsed.check:
            # Dry-run mode: report routing decisions without executing commands.
            tool = tool_override or _pick_tool(command or "", tool_override, config)
            config["_runtime"]["resolved_tool"] = tool
            enabled = _tool_enabled(tool, config)
            allowed_cmd = True if not command else _command_allowed(tool, command, config)
            allowed = "yes" if (enabled and allowed_cmd) else "no"
            print(f"tool: {tool}")
            print(f"command: {command or '(none)'}")
            print(f"allowed: {allowed}")
            rc = 0 if allowed == "yes" else 2
            return rc

        builtin_result = _dispatch_builtin(command, args[1:], config, _builtin_handlers())
        if builtin_result is not None:
            config["_runtime"]["resolved_tool"] = "builtin"
            rc = builtin_result
            return rc

        # Try configured custom commands before falling back to git/gh passthrough.
        custom_result = _dispatch_custom(
            command,
            config,
            _pick_tool,
            _tool_enabled,
            _command_allowed,
            _guardrails_block,
            _run_tool,
            _git_output,
        )
        if custom_result is not None:
            config["_runtime"]["resolved_tool"] = "custom"
            rc = custom_result
            return rc

        # Route and run the requested git/gh command with guardrails.
        tool = tool_override or _pick_tool(command or "", tool_override, config)
        config["_runtime"]["resolved_tool"] = tool
        if not _tool_enabled(tool, config):
            sys.stderr.write(f"router: {tool} is disabled by config\n")
            rc = 2
            return rc
        if command and not _command_allowed(tool, command, config):
            sys.stderr.write(f"router: {tool} {command} denied by config\n")
            rc = 2
            return rc

        guard_err = _guardrails_block(tool, args, config, _git_output)
        if guard_err:
            sys.stderr.write(f"{guard_err}\n")
            rc = 2
            return rc

        proc = _run_tool(tool, args, check=False)
        rc = proc.returncode
        return rc
    except BrokenPipeError:
        # Allow piping/truncation (e.g. `head`) without crashing the router.
        rc = 0
        return rc
    except RuntimeError as exc:
        sys.stderr.write(f"{exc}\n")
        rc = 2
        return rc
    finally:
        if tee_out is not None:
            sys.stdout = tee_out.stream
        if tee_err is not None:
            sys.stderr = tee_err.stream
        RUNTIME_CONTEXT.set_config(None)
        if log_enabled:
            runtime = config.get("_runtime", {}) if isinstance(config, dict) else {}
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "command": command,
                "args": args,
                "tool": runtime.get("resolved_tool", ""),
                "resolved": runtime.get("resolved_commands", []),
                "exit_code": rc,
                "stdout": tee_out.buffer if tee_out else "",
                "stderr": tee_err.buffer if tee_err else "",
                "profile": runtime.get("profile", ""),
            }
            _write_log_entries([entry], log_file, log_format)


def main() -> None:
    """CLI entrypoint for the router module."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()
