"""Configuration helpers for router CLI."""
from __future__ import annotations

from pathlib import Path

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None  # type: ignore


def _load_config(path: Path) -> dict:
    """Load a YAML config file into a dict."""
    if yaml is None:  # pragma: no cover
        raise RuntimeError("PyYAML is required to load router config.")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise RuntimeError("Router config must be a YAML dict.")
    return data


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge two dicts and return the result."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _merge_custom_commands(config: dict, config_path: Path) -> None:
    """Add custom commands from a separate file into the active config."""
    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    custom_file = str(router_cfg.get("custom_commands_file", "")).strip()
    if not custom_file:
        return
    custom_path = Path(custom_file)
    if not custom_path.is_absolute():
        custom_path = (config_path.parent / custom_file).resolve()
    if not custom_path.exists():
        raise RuntimeError(f"Custom commands file not found: {custom_path}")
    if yaml is None:  # pragma: no cover
        raise RuntimeError("PyYAML is required to load router config.")
    custom_doc = yaml.safe_load(custom_path.read_text(encoding="utf-8")) or {}
    if not isinstance(custom_doc, dict):
        raise RuntimeError("Custom commands file must be a YAML dict.")
    custom_commands = custom_doc.get("custom_commands", {})
    if not isinstance(custom_commands, dict):
        raise RuntimeError("custom_commands must be a dict.")
    config.setdefault("custom_commands", {})
    if not isinstance(config["custom_commands"], dict):
        raise RuntimeError("custom_commands in main config must be a dict.")
    for key, value in custom_commands.items():
        config["custom_commands"][str(key).strip().lower()] = value


def _load_noise_flags(config: dict, level: str) -> list[str]:
    """Read the noise flag list for a named noise level."""
    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    levels = router_cfg.get("diff_noise_levels", {})
    if not isinstance(levels, dict):
        levels = {}
    info = levels.get(level, {})
    if isinstance(info, dict):
        flags = info.get("flags", [])
    else:
        flags = info
    if not flags:
        return []
    if not isinstance(flags, list):
        raise RuntimeError("router diff: noise flags must be a list")
    return [str(flag) for flag in flags if str(flag).strip()]


def _resolve_noise_level(config: dict, noise_level: str) -> tuple[str, list[str]]:
    """Pick the noise level and flag list using config defaults."""
    level = (noise_level or "").strip()
    if not level:
        router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
        level = str(router_cfg.get("diff_default_noise", "max")).strip() or "max"
    return level, _load_noise_flags(config, level)


def _load_default_excludes(config: dict) -> list[str]:
    """Read default diff exclude patterns from config."""
    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    patterns = router_cfg.get("diff_default_excludes", [])
    if not patterns:
        return []
    if not isinstance(patterns, list):
        raise RuntimeError("router diff: diff_default_excludes must be a list")
    return [str(item).strip() for item in patterns if str(item).strip()]


def _load_compact_defaults(config: dict) -> dict:
    """Read default compact options from config."""
    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    defaults = router_cfg.get("compact_defaults", {})
    if defaults is None:
        defaults = {}
    if not isinstance(defaults, dict):
        raise RuntimeError("router compact_defaults must be a dict")
    return {
        "context": int(defaults.get("context", 0)),
        "drop_headers": bool(defaults.get("drop_headers", True)),
        "no_prefix": bool(defaults.get("no_prefix", True)),
        "drop_diff_header": bool(defaults.get("drop_diff_header", False)),
        "drop_hunk_header": bool(defaults.get("drop_hunk_header", False)),
        "short_diff_header": bool(defaults.get("short_diff_header", False)),
        "short_hunk_header": bool(defaults.get("short_hunk_header", False)),
        "drop_filemode": bool(defaults.get("drop_filemode", False)),
        "drop_rename": bool(defaults.get("drop_rename", False)),
        "drop_similarity": bool(defaults.get("drop_similarity", False)),
        "drop_binary": bool(defaults.get("drop_binary", False)),
        "path_strip": str(defaults.get("path_strip", "") or ""),
        "path_basename": bool(defaults.get("path_basename", False)),
        "path_table": bool(defaults.get("path_table", False)),
        "path_common_prefix": bool(defaults.get("path_common_prefix", False)),
        "path_prefix_token": str(defaults.get("path_prefix_token", "...") or "..."),
        "hunk_new_only": bool(defaults.get("hunk_new_only", False)),
        "prefix_first_only": bool(defaults.get("prefix_first_only", False)),
    }


def _load_history_compact_meta_overrides(config: dict) -> dict:
    """Read history compact meta overrides from config."""
    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    overrides = router_cfg.get("history_compact_meta_overrides", {}) or {}
    if not isinstance(overrides, dict):
        raise RuntimeError("router history_compact_meta_overrides must be a dict")
    return overrides


def _merge_compact_options(base: dict, override: dict) -> dict:
    """Merge compact option overrides into the base options dict."""
    merged = dict(base)
    for key, value in override.items():
        merged[key] = value
    return merged


def _load_compact_profiles(config: dict) -> dict:
    """Read compact profiles from config."""
    router_cfg = config.get("router", {}) if isinstance(config.get("router"), dict) else {}
    profiles = router_cfg.get("compact_profiles", {}) or {}
    if not isinstance(profiles, dict):
        raise RuntimeError("router compact_profiles must be a dict")
    return profiles
