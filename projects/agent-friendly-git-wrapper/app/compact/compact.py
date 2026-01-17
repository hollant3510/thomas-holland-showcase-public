"""Compact diff helpers for router output shaping."""
from __future__ import annotations

from app.config.config_loader import _load_compact_profiles, _merge_compact_options

try:
    import tiktoken  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    tiktoken = None  # type: ignore


def _apply_compact_options(
    compact_enabled: bool,
    compact_spec: str,
    compact_opts: dict,
    compact_profiles: dict,
    context: int | None,
    context_set: bool,
) -> tuple[dict, int | None, bool]:
    """Apply compact settings and return updated options plus context."""
    if not compact_enabled:
        return compact_opts, context, False
    compact_opts = _parse_compact_spec(compact_spec, compact_opts, compact_profiles)
    if not context_set:
        context = int(compact_opts["context"])
    return compact_opts, context, bool(compact_opts.get("no_prefix"))


def _render_compact_output(
    output_text: str,
    compact_enabled: bool,
    include_patch: bool,
    compact_opts: dict,
    config: dict,
    error_message: str,
) -> str:
    """Return compact output when enabled, otherwise return the original text."""
    if compact_enabled and not include_patch:
        raise RuntimeError(error_message)
    if compact_enabled and include_patch:
        return _auto_tune_compact(output_text, compact_opts, config)
    return output_text


def _measure_text(text: str, metric: str, encoding: str) -> int:
    """Measure text size using characters or tokens."""
    metric = (metric or "chars").strip().lower()
    if metric == "tokens":
        if tiktoken is None:
            return len(text)
        enc = tiktoken.get_encoding(encoding or "cl100k_base")
        return len(enc.encode(text))
    return len(text)


def _auto_tune_compact(text: str, options: dict, config: dict) -> str:
    """Try optional compact tweaks and keep the smallest result."""
    if not text:
        return text
    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    auto_cfg = router_cfg.get("compact_auto_tune", {})
    if not isinstance(auto_cfg, dict) or not auto_cfg.get("enabled", False):
        return _compact_output(text, options)
    metric = str(auto_cfg.get("metric", "tokens")).strip().lower()
    encoding = str(auto_cfg.get("encoding", "cl100k_base")).strip()
    candidates = auto_cfg.get("candidates", [])
    if not isinstance(candidates, list):
        raise RuntimeError("router compact_auto_tune candidates must be a list")
    profiles = _load_compact_profiles(config)

    best_options = dict(options)
    best_output = _compact_output(text, best_options)
    best_score = _measure_text(best_output, metric, encoding)

    for candidate in candidates:
        if not isinstance(candidate, str) or not candidate.strip():
            continue
        candidate_opts = _parse_compact_spec(candidate.strip(), best_options, profiles)
        candidate_output = _compact_output(text, candidate_opts)
        candidate_score = _measure_text(candidate_output, metric, encoding)
        if candidate_score < best_score:
            best_score = candidate_score
            best_output = candidate_output
            best_options = candidate_opts

    return best_output


def _parse_compact_spec(spec: str, defaults: dict, profiles: dict) -> dict:
    """Turn a compact spec string into option overrides."""
    options = dict(defaults)
    if not spec:
        return options
    for raw in spec.split(","):
        part = raw.strip()
        if not part:
            continue
        token = part.strip()
        token_lower = token.lower()
        if token_lower.startswith("profile="):
            profile_name = token.split("=", 1)[1].strip()
            if not profile_name:
                raise RuntimeError("router diff: compact profile name is required")
            profile = profiles.get(profile_name)
            if profile is None:
                raise RuntimeError(f"router diff: unknown compact profile '{profile_name}'")
            if not isinstance(profile, dict):
                raise RuntimeError("router compact_profiles entries must be dicts")
            options = _merge_compact_options(options, profile)
            continue
        if token in profiles:
            profile = profiles.get(token)
            if not isinstance(profile, dict):
                raise RuntimeError("router compact_profiles entries must be dicts")
            options = _merge_compact_options(options, profile)
            continue
        if token_lower in {"drop-headers", "no-headers"}:
            options["drop_headers"] = True
            continue
        if token_lower in {"keep-headers", "headers"}:
            options["drop_headers"] = False
            continue
        if token_lower in {"no-prefix", "drop-prefix"}:
            options["no_prefix"] = True
            continue
        if token_lower in {"keep-prefix", "prefix"}:
            options["no_prefix"] = False
            continue
        if token_lower in {"drop-diff-header", "no-diff-header"}:
            options["drop_diff_header"] = True
            continue
        if token_lower in {"keep-diff-header", "diff-header"}:
            options["drop_diff_header"] = False
            continue
        if token_lower in {"short-diff-header", "short-file-header"}:
            options["short_diff_header"] = True
            continue
        if token_lower in {"drop-hunk-header", "no-hunk-header"}:
            options["drop_hunk_header"] = True
            continue
        if token_lower in {"keep-hunk-header", "hunk-header"}:
            options["drop_hunk_header"] = False
            continue
        if token_lower in {"short-hunk-header", "short-hunk"}:
            options["short_hunk_header"] = True
            continue
        if token_lower in {"drop-filemode", "no-filemode"}:
            options["drop_filemode"] = True
            continue
        if token_lower in {"drop-rename", "no-rename"}:
            options["drop_rename"] = True
            continue
        if token_lower in {"drop-similarity", "no-similarity"}:
            options["drop_similarity"] = True
            continue
        if token_lower in {"drop-binary", "no-binary"}:
            options["drop_binary"] = True
            continue
        if token_lower.startswith("path-strip="):
            options["path_strip"] = token.split("=", 1)[1]
            continue
        if token_lower in {"path-basename", "basename"}:
            options["path_basename"] = True
            continue
        if token_lower in {"path-table", "path-id", "path-ids"}:
            options["path_table"] = True
            options["short_diff_header"] = True
            continue
        if token_lower in {"hunk-new-only", "hunk-new"}:
            options["hunk_new_only"] = True
            continue
        if token_lower in {"hunk-full", "hunk-both"}:
            options["hunk_new_only"] = False
            continue
        if token_lower in {"path-common-prefix", "common-prefix"}:
            options["path_common_prefix"] = True
            continue
        if token_lower in {"no-common-prefix", "no-path-common-prefix"}:
            options["path_common_prefix"] = False
            continue
        if token_lower.startswith("path-prefix-token="):
            options["path_prefix_token"] = token.split("=", 1)[1]
            continue
        if token_lower in {"prefix-first", "prefix-first-only", "run-prefix-first"}:
            options["prefix_first_only"] = True
            continue
        if token_lower in {"prefix-full", "prefix-all", "prefix-every"}:
            options["prefix_first_only"] = False
            continue
        if token_lower.startswith("context="):
            options["context"] = int(token_lower.split("=", 1)[1])
            continue
        if token_lower.startswith("u") and token_lower[1:].isdigit():
            options["context"] = int(token_lower[1:])
            continue
        raise RuntimeError(f"router diff: unknown compact option '{part}'")
    return options


def _compact_output(text: str, options: dict) -> str:
    """Transform a diff into a compact form based on options."""
    if not text:
        return text
    drop_headers = bool(options.get("drop_headers", False))
    drop_diff_header = bool(options.get("drop_diff_header", False))
    drop_hunk_header = bool(options.get("drop_hunk_header", False))
    short_diff_header = bool(options.get("short_diff_header", False))
    short_hunk_header = bool(options.get("short_hunk_header", False))
    drop_filemode = bool(options.get("drop_filemode", False))
    drop_rename = bool(options.get("drop_rename", False))
    drop_similarity = bool(options.get("drop_similarity", False))
    drop_binary = bool(options.get("drop_binary", False))
    path_strip = str(options.get("path_strip", "") or "")
    path_basename = bool(options.get("path_basename", False))
    path_table = bool(options.get("path_table", False))
    path_common_prefix = bool(options.get("path_common_prefix", False))
    path_prefix_token = str(options.get("path_prefix_token", "...") or "...")
    hunk_new_only = bool(options.get("hunk_new_only", False))
    prefix_first_only = bool(options.get("prefix_first_only", False))

    lines = text.splitlines()
    kept: list[str] = []
    last_prefix = ""

    path_ids: dict[str, int] = {}
    path_display: dict[str, str] = {}

    def _extract_path(diff_line: str) -> str:
        """Extract the file path from a diff header line."""
        parts = diff_line.split()
        if len(parts) < 4:
            return ""
        a_path = parts[2]
        b_path = parts[3]
        path = b_path if b_path.startswith("b/") else a_path
        if path.startswith("a/") or path.startswith("b/"):
            path = path[2:]
        if path_strip and path.startswith(path_strip):
            path = path[len(path_strip) :]
            if path.startswith("/"):
                path = path[1:]
        if path_basename:
            path = path.rsplit("/", 1)[-1]
        return path

    paths: list[str] = []
    for line in lines:
        if line.startswith("diff --git "):
            path = _extract_path(line)
            if path and path not in paths:
                paths.append(path)

    def _common_dir_prefix(items: list[str]) -> str:
        """Find the shared directory prefix across file paths."""
        if not items:
            return ""
        dirs: list[list[str]] = []
        for item in items:
            if "/" not in item:
                return ""
            parts = item.split("/")[:-1]
            if not parts:
                return ""
            dirs.append(parts)
        if not dirs:
            return ""
        min_len = min(len(parts) for parts in dirs)
        if min_len == 0:
            return ""
        idx = 0
        while idx < min_len and all(parts[idx] == dirs[0][idx] for parts in dirs):
            idx += 1
        if idx == 0:
            return ""
        return "/".join(dirs[0][:idx]) + "/"

    common_prefix = _common_dir_prefix(paths) if path_common_prefix else ""

    def _apply_common_prefix(path: str) -> str:
        """Apply the common prefix token to shorten a path."""
        if common_prefix and path.startswith(common_prefix):
            trimmed = path[len(common_prefix) :].lstrip("/")
            if trimmed:
                return f"{path_prefix_token}/{trimmed}"
            return path_prefix_token
        return path

    if path_table and paths:
        for path in paths:
            path_ids[path] = len(path_ids) + 1
            path_display[path] = _apply_common_prefix(path)
        kept.append(f"files[{len(path_ids)}]{{id,path}}:")
        for path, idx in path_ids.items():
            kept.append(f"  {idx},{path_display.get(path, path)}")
    for line in lines:
        if drop_headers:
            if line.startswith("index "):
                continue
            if line.startswith("--- "):
                continue
            if line.startswith("+++ "):
                continue
        if drop_filemode:
            if line.startswith("new file mode "):
                continue
            if line.startswith("deleted file mode "):
                continue
        if drop_similarity:
            if line.startswith("similarity index "):
                continue
            if line.startswith("dissimilarity index "):
                continue
        if drop_rename:
            if line.startswith("rename from "):
                continue
            if line.startswith("rename to "):
                continue
            if line.startswith("copy from "):
                continue
            if line.startswith("copy to "):
                continue
        if drop_binary:
            if line.startswith("Binary files "):
                continue
            if line.startswith("GIT binary patch"):
                continue
        if line.startswith("diff --git "):
            if drop_diff_header:
                continue
            if short_diff_header:
                path = _extract_path(line)
                if path_table and path in path_ids:
                    kept.append(f"f {path_ids[path]}")
                    last_prefix = ""
                    continue
                if path:
                    kept.append(f"f {_apply_common_prefix(path)}".rstrip())
                    last_prefix = ""
                    continue
        if line.startswith("@@ "):
            if short_hunk_header:
                import re

                match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@.*", line)
                if match:
                    old_start = match.group(1)
                    old_len = match.group(2) or "1"
                    new_start = match.group(3)
                    new_len = match.group(4) or "1"
                    if hunk_new_only:
                        kept.append(f"@ {new_start}")
                    else:
                        kept.append(f"@ {old_start},{old_len} {new_start},{new_len}")
                    last_prefix = ""
                    continue
            if drop_hunk_header:
                last_prefix = ""
                continue
        if prefix_first_only:
            if line.startswith(("+", "-", " ")):
                prefix = line[0]
                body = line[1:]
                if prefix == last_prefix:
                    kept.append(body)
                else:
                    kept.append(line)
                last_prefix = prefix
                continue
            last_prefix = ""
        if path_table and line.startswith(("--- ", "+++ ")):
            if line.startswith("--- "):
                prefix = "--- "
                path = line[len(prefix):]
            else:
                prefix = "+++ "
                path = line[len(prefix):]
            if path.startswith("a/") or path.startswith("b/"):
                path = path[2:]
            path = _apply_common_prefix(path)
            if path in path_ids:
                kept.append(prefix + f"{path_ids[path]}")
                continue
        kept.append(line)

    return "\n".join(kept) + ("\n" if text.endswith("\n") else "")

