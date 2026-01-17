"""Handle the router diff command."""
from __future__ import annotations

import sys
from typing import Callable, Sequence

from app.cli.cli_parse import _build_diff_args, _build_pathspecs, _parse_diff_style_args
from app.compact.compact import _apply_compact_options, _render_compact_output
from app.config.config_loader import _load_compact_defaults, _load_compact_profiles, _resolve_noise_level


def dispatch_diff(
    args: list[str],
    config: dict,
    run_git: Callable[..., object],
) -> int:
    """Render a diff with configured detail, noise, and compact settings."""
    compact_opts = _load_compact_defaults(config)
    compact_profiles = _load_compact_profiles(config)

    parse_opts: dict = {}
    idx = 0
    while idx < len(args):
        token = args[idx]
        if token in {"-h", "--help"}:
            sys.stdout.write(
                "usage: router diff [--noise[=LEVEL]] [--context N] [--detail 0..3]\n"
                "                  [--summary|--files-only|--stat|--name-status|--super-compact] [--compact[=SPEC]]\n"
                "                  [--include PATTERN] [--exclude PATTERN] [--ops LIST]\n"
            )
            return 0
        parse_opts, _ = _parse_diff_style_args(args[idx:], config, "diff", allow_positional=False)
        idx = len(args)
        break

    if not parse_opts:
        parse_opts, _ = _parse_diff_style_args([], config, "diff", allow_positional=False)

    if parse_opts["detail"] < 0 or parse_opts["detail"] > 3:
        raise RuntimeError("router diff: --detail must be 0..3")

    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    noise_level, noise_flags = _resolve_noise_level(config, parse_opts["noise_level"])
    detail_mode = parse_opts["detail_mode"]
    detail = parse_opts["detail"]
    if not detail_mode and detail == 2:
        default_detail = router_cfg.get("diff_default_detail")
        if default_detail is not None:
            detail = int(default_detail)
    compact_enabled = parse_opts["compact_enabled"]
    context = parse_opts["context"]
    context_set = parse_opts["context_set"]
    if not compact_enabled and context is None and not context_set:
        default_context = router_cfg.get("diff_default_context")
        if default_context is not None:
            context = int(default_context)
    includes = parse_opts["includes"]
    excludes = parse_opts["excludes"]
    ops = parse_opts["ops"]

    diff_args, include_patch = _build_diff_args(detail, detail_mode)

    compact_spec = parse_opts["compact_spec"]
    compact_opts, context, no_prefix = _apply_compact_options(
        compact_enabled,
        compact_spec,
        compact_opts,
        compact_profiles,
        context,
        context_set,
    )
    if compact_enabled and no_prefix:
        diff_args.append("--no-prefix")

    if context is not None and include_patch:
        diff_args.append(f"--unified={context}")

    if ops:
        diff_args.append(f"--diff-filter={ops}")

    diff_args.extend(noise_flags)

    pathspecs = _build_pathspecs(includes, excludes)
    if pathspecs:
        diff_args.append("--")
        diff_args.extend(pathspecs)

    proc = run_git(
        diff_args,
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
        "router diff: --compact requires patch output (detail 2/3)",
    )
    if output_text:
        sys.stdout.write(output_text)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    return proc.returncode


