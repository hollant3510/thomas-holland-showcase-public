"""CLI parsing helpers for router commands."""
from __future__ import annotations

from app.config.config_loader import _load_default_excludes


def _parse_noise_flag(args: list[str], idx: int, command: str) -> tuple[bool, str, int]:
    """Read a --noise flag and return the value plus the next index to read."""
    token = args[idx]
    if token.startswith("--noise="):
        return True, token.split("=", 1)[1].strip(), idx + 1
    if token == "--noise":
        if idx + 1 < len(args) and not args[idx + 1].startswith("-"):
            return True, args[idx + 1].strip(), idx + 2
        return True, "max", idx + 1
    return False, "", idx


def _parse_list_arg(value: str) -> list[str]:
    """Split a comma-delimited list into trimmed values."""
    items = []
    for part in value.split(","):
        part = part.strip()
        if part:
            items.append(part)
    return items


def _parse_ops(value: str) -> str:
    """Translate diff filter labels into the git diff-filter letters."""
    mapping = {
        "added": "A",
        "modified": "M",
        "deleted": "D",
        "renamed": "R",
        "copied": "C",
        "typechange": "T",
        "unmerged": "U",
        "unknown": "X",
        "broken": "B",
    }
    letters = []
    for part in _parse_list_arg(value):
        key = part.strip().lower()
        if not key:
            continue
        if len(key) == 1 and key.isalpha():
            letters.append(key.upper())
            continue
        if key in mapping:
            letters.append(mapping[key])
            continue
        raise RuntimeError(f"router diff: unknown ops value '{part}'")
    return "".join(sorted(set(letters)))


def _parse_diff_style_args(
    args: list[str],
    config: dict,
    command: str,
    *,
    allow_positional: bool,
) -> tuple[dict, list[str]]:
    """Turn diff-style CLI flags into a shared settings dict plus positionals."""
    # Initialize parse state and defaults for diff-style commands.
    noise_level = ""
    context = None
    context_set = False
    detail = 2
    detail_mode = ""
    includes: list[str] = []
    excludes: list[str] = _load_default_excludes(config)
    ops = ""
    compact_enabled = False
    compact_spec = ""
    positionals: list[str] = []

    idx = 0
    # Scan tokens left-to-right, consuming flags and collecting positionals.
    while idx < len(args):
        token = args[idx]
        handled, parsed_noise, new_idx = _parse_noise_flag(args, idx, command)
        if handled:
            # Noise flags are parsed in a helper so --noise/--noise= work consistently.
            noise_level = parsed_noise
            idx = new_idx
            continue
        if token == "--context":
            if idx + 1 >= len(args):
                raise RuntimeError(f"router {command}: --context requires a value")
            # Context size only matters when patch output is included.
            context = int(args[idx + 1])
            context_set = True
            idx += 2
            continue
        if token == "--detail":
            if idx + 1 >= len(args):
                raise RuntimeError(f"router {command}: --detail requires a value")
            # Detail overrides the output mode, switching to patch/stat/name-only later.
            detail = int(args[idx + 1])
            detail_mode = "detail"
            idx += 2
            continue
        if token.startswith("--compact="):
            # Compact mode can be toggled with an inline profile or spec.
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
        if token == "--summary":
            # Output shaping flags select the detail mode without changing detail number.
            detail_mode = "summary"
            idx += 1
            continue
        if token == "--files-only":
            detail_mode = "files"
            idx += 1
            continue
        if token == "--super-compact":
            detail_mode = "files"
            idx += 1
            continue
        if token == "--stat":
            detail_mode = "stat"
            idx += 1
            continue
        if token == "--name-status":
            detail_mode = "name-status"
            idx += 1
            continue
        if token == "--include":
            if idx + 1 >= len(args):
                raise RuntimeError(f"router {command}: --include requires a value")
            # Include/exclude lists support comma-delimited pathspec groups.
            includes.extend(_parse_list_arg(args[idx + 1]))
            idx += 2
            continue
        if token == "--exclude":
            if idx + 1 >= len(args):
                raise RuntimeError(f"router {command}: --exclude requires a value")
            excludes.extend(_parse_list_arg(args[idx + 1]))
            idx += 2
            continue
        if token == "--ops":
            if idx + 1 >= len(args):
                raise RuntimeError(f"router {command}: --ops requires a value")
            # Ops filters map user-friendly labels to git diff filter letters.
            ops = _parse_ops(args[idx + 1])
            idx += 2
            continue
        if token.startswith("-"):
            raise RuntimeError(f"router {command}: unknown argument '{token}'")
        if allow_positional:
            # Positional args are only permitted for commands like compare/history.
            positionals.append(token)
            idx += 1
            continue
        raise RuntimeError(f"router {command}: unknown argument '{token}'")

    return (
        {
            "noise_level": noise_level,
            "context": context,
            "context_set": context_set,
            "detail": detail,
            "detail_mode": detail_mode,
            "includes": includes,
            "excludes": excludes,
            "ops": ops,
            "compact_enabled": compact_enabled,
            "compact_spec": compact_spec,
        },
        positionals,
    )


def _parse_log_like_args(args: list[str], command: str) -> tuple[dict, list[str]]:
    """Turn log/history flags into a settings dict plus leftover tokens."""
    # Initialize parse state for log/history flags and any remaining tokens.
    count = None
    since = ""
    rev_range = ""
    path = ""
    short_hash = False
    rest: list[str] = []

    idx = 0
    # Walk the arg list, consuming recognized flags and collecting leftovers.
    while idx < len(args):
        token = args[idx]
        if token == "--n":
            if idx + 1 >= len(args):
                raise RuntimeError(f"router {command}: --n requires a value")
            # --n controls the number of commits to return.
            count = int(args[idx + 1])
            idx += 2
            continue
        if token == "--since":
            if idx + 1 >= len(args):
                raise RuntimeError(f"router {command}: --since requires a value")
            # --since scopes history by a time/commit reference.
            since = args[idx + 1].strip()
            idx += 2
            continue
        if token == "--range":
            if idx + 1 >= len(args):
                raise RuntimeError(f"router {command}: --range requires a value")
            # --range accepts A..B style rev ranges for log/history.
            rev_range = args[idx + 1].strip()
            idx += 2
            continue
        if token == "--path":
            if idx + 1 >= len(args):
                raise RuntimeError(f"router {command}: --path requires a value")
            # --path limits history output to a single pathspec.
            path = args[idx + 1].strip()
            idx += 2
            continue
        if token == "--short-hash":
            # --short-hash toggles abbreviated commit identifiers.
            short_hash = True
            idx += 1
            continue
        rest.append(token)
        idx += 1

    return (
        {
            "count": count,
            "since": since,
            "rev_range": rev_range,
            "path": path,
            "short_hash": short_hash,
        },
        rest,
    )


def _build_diff_args(
    detail: int, detail_mode: str, range_ref: str | None = None
) -> tuple[list[str], bool]:
    """Build git diff args from detail settings and report patch inclusion."""
    diff_args = ["diff"]
    if range_ref:
        diff_args.append(range_ref)
    include_patch = False
    mode = detail_mode or "detail"
    if mode == "files":
        # Files-only output keeps filenames without patch content.
        diff_args.append("--name-only")
    elif mode == "name-status":
        # Name-status emits filename plus change status codes.
        diff_args.append("--name-status")
    elif mode == "stat":
        # Stat output keeps summary counts without patch hunks.
        diff_args.append("--stat")
    elif mode == "summary":
        # Shortstat provides a minimal summary line.
        diff_args.append("--shortstat")
    else:
        if detail == 0:
            diff_args.append("--name-only")
        elif detail == 1:
            diff_args.append("--name-status")
        elif detail == 2:
            diff_args.append("--patch")
            include_patch = True
        else:
            diff_args.extend(["--patch", "--stat"])
            include_patch = True
    return diff_args, include_patch


def _build_pathspecs(includes: list[str], excludes: list[str]) -> list[str]:
    """Build git pathspecs from include/exclude lists."""
    pathspecs: list[str] = []
    for item in includes:
        pathspecs.append(item)
    for item in excludes:
        pathspecs.append(f":(exclude){item}")
    return pathspecs


def _validate_stat_name_status(command: str, show_stat: bool, show_name_status: bool) -> None:
    """Error when --stat and --name-status are both requested."""
    if show_stat and show_name_status:
        raise RuntimeError(f"router {command}: choose --stat or --name-status, not both")

