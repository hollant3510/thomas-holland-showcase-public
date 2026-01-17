"""Handle the router history command."""
from __future__ import annotations

import sys
from typing import Callable

from app.cli.cli_parse import (
    _build_pathspecs,
    _parse_list_arg,
    _parse_log_like_args,
    _parse_noise_flag,
    _parse_ops,
)
from app.compact.compact import _apply_compact_options, _render_compact_output
from app.config.config_loader import (
    _load_compact_defaults,
    _load_compact_profiles,
    _load_default_excludes,
    _load_history_compact_meta_overrides,
    _resolve_noise_level,
)


def dispatch_history(
    args: list[str],
    config: dict,
    run_git: Callable[..., object],
) -> int:
    """Render commit history with optional diff and compact output."""
    count = None
    since = ""
    rev_range = ""
    path = ""
    short_hash = False
    commit_meta = ""
    no_hash = False
    no_author = False
    no_date = False
    no_subject = False
    detail_mode = ""
    include_patch = None
    context = None
    context_set = False
    noise_level = ""
    includes: list[str] = []
    excludes: list[str] = _load_default_excludes(config)
    ops = ""
    compact_enabled = False
    compact_spec = ""
    compact_opts = _load_compact_defaults(config)
    compact_profiles = _load_compact_profiles(config)

    if "-h" in args or "--help" in args:
        sys.stdout.write(
            "usage: router history --n N [--since REF|--range A..B] [--path PATH]\n"
            "                     [--patch|--no-patch] [--summary|--files-only|--stat|--name-status]\n"
            "                     [--noise[=LEVEL]] [--context N] [--compact[=SPEC]] [--ops LIST]\n"
            "                     [--commit-meta MODE] [--short-hash] [--no-hash] [--no-author]\n"
            "                     [--no-date] [--no-subject]\n"
        )
        return 0

    parsed, remaining = _parse_log_like_args(args, "history")
    count = parsed["count"]
    since = parsed["since"]
    rev_range = parsed["rev_range"]
    path = parsed["path"]
    short_hash = parsed["short_hash"]
    args = remaining

    idx = 0
    while idx < len(args):
        token = args[idx]
        if token == "--commit-meta":
            if idx + 1 >= len(args):
                raise RuntimeError("router history: --commit-meta requires a value")
            commit_meta = args[idx + 1].strip().lower()
            idx += 2
            continue
        if token == "--no-hash":
            no_hash = True
            idx += 1
            continue
        if token == "--no-author":
            no_author = True
            idx += 1
            continue
        if token == "--no-date":
            no_date = True
            idx += 1
            continue
        if token == "--no-subject":
            no_subject = True
            idx += 1
            continue
        if token == "--patch":
            include_patch = True
            idx += 1
            continue
        if token == "--no-patch":
            include_patch = False
            idx += 1
            continue
        if token == "--summary":
            detail_mode = "summary"
            idx += 1
            continue
        if token == "--files-only":
            detail_mode = "files"
            idx += 1
            continue
        if token == "--name-status":
            detail_mode = "name-status"
            idx += 1
            continue
        if token == "--stat":
            detail_mode = "stat"
            idx += 1
            continue
        handled, parsed_noise, new_idx = _parse_noise_flag(args, idx, "history")
        if handled:
            noise_level = parsed_noise
            idx = new_idx
            continue
        if token == "--context":
            if idx + 1 >= len(args):
                raise RuntimeError("router history: --context requires a value")
            context = int(args[idx + 1])
            context_set = True
            idx += 2
            continue
        if token.startswith("--compact="):
            compact_enabled = True
            compact_spec = token.split("=", 1)[1].strip()
            idx += 1
            continue
        if token == "--compact":
            compact_enabled = True
            if idx + 1 < len(args) and not args[idx + 1].startswith("-"):
                compact_spec = args[idx + 1].strip()
                idx += 2
            else:
                idx += 1
            continue
        if token == "--include":
            if idx + 1 >= len(args):
                raise RuntimeError("router history: --include requires a value")
            includes.extend(_parse_list_arg(args[idx + 1]))
            idx += 2
            continue
        if token == "--exclude":
            if idx + 1 >= len(args):
                raise RuntimeError("router history: --exclude requires a value")
            excludes.extend(_parse_list_arg(args[idx + 1]))
            idx += 2
            continue
        if token == "--ops":
            if idx + 1 >= len(args):
                raise RuntimeError("router history: --ops requires a value")
            ops = _parse_ops(args[idx + 1])
            idx += 2
            continue
        raise RuntimeError(f"router history: unknown argument '{token}'")

    if rev_range and since:
        raise RuntimeError("router history: use either --since or --range, not both")

    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    noise_level, noise_flags = _resolve_noise_level(config, noise_level)

    if include_patch is None:
        include_patch = bool(router_cfg.get("history_default_patch", True))

    if compact_enabled and not commit_meta:
        history_meta_overrides = _load_history_compact_meta_overrides(config)
        compact_key = compact_spec.strip().lower() if compact_spec else ""
        if not compact_key:
            compact_key = "default"
        override = history_meta_overrides.get(compact_key)
        if override is not None:
            commit_meta = str(override).strip().lower()

    if not commit_meta:
        commit_meta = str(router_cfg.get("history_default_commit_meta", "short")).strip().lower()

    include_hash = False
    include_subject = False
    include_author = False
    include_date = False

    if commit_meta in {"none", "off", "false", "0"}:
        include_hash = False
    elif commit_meta == "hash":
        include_hash = True
    elif commit_meta == "subject":
        include_subject = True
    elif commit_meta == "short":
        include_hash = True
        include_subject = True
    elif commit_meta == "full":
        include_hash = True
        include_subject = True
        include_author = True
        include_date = True
    else:
        raise RuntimeError("router history: --commit-meta must be none|hash|subject|short|full")

    if no_hash:
        include_hash = False
    if no_subject:
        include_subject = False
    if no_author:
        include_author = False
    if no_date:
        include_date = False

    compact_opts, context, no_prefix = _apply_compact_options(
        compact_enabled,
        compact_spec,
        compact_opts,
        compact_profiles,
        context,
        context_set,
    )

    format_parts: list[str] = []
    if include_hash:
        format_parts.append("%h" if short_hash else "%H")
    if include_subject:
        format_parts.append("%s")
    if include_author:
        format_parts.append("%an")
    if include_date:
        format_parts.append("%ad")

    log_args = ["log"]
    if count is not None:
        log_args.append(f"--max-count={count}")

    if rev_range:
        log_args.append(rev_range)
    elif since:
        log_args.append(f"{since}..HEAD")

    format_str = " ".join(format_parts)
    log_args.append(f"--pretty=format:{format_str}")
    if include_date:
        log_args.append("--date=short")

    if detail_mode == "summary":
        include_patch = False
        log_args.append("--shortstat")
    elif detail_mode == "stat":
        include_patch = False
        log_args.append("--stat")
    elif detail_mode == "name-status":
        include_patch = False
        log_args.append("--name-status")
    elif detail_mode == "files":
        include_patch = False
        log_args.append("--name-only")
    elif include_patch:
        log_args.append("--patch")

    if compact_enabled and not include_patch:
        raise RuntimeError("router history: --compact requires patch output")

    if include_patch:
        if compact_enabled and no_prefix:
            log_args.append("--no-prefix")
        if context is not None:
            log_args.append(f"--unified={context}")
        log_args.extend(noise_flags)
        if ops:
            log_args.append(f"--diff-filter={ops}")

    pathspecs = _build_pathspecs(includes, excludes)
    if path:
        pathspecs.append(path)
    if pathspecs:
        log_args.append("--")
        log_args.extend(pathspecs)

    proc = run_git(
        log_args,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output_text = proc.stdout or ""
    output_text = _render_compact_output(
        output_text,
        compact_enabled,
        include_patch,
        compact_opts,
        config,
        "router history: --compact requires patch output",
    )
    if output_text:
        sys.stdout.write(output_text)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc.returncode


