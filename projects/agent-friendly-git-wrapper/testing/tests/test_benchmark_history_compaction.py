"""Tests for history compaction benchmark table snapshots."""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None  # type: ignore


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TESTING_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.compact import compact as compact_mod  # noqa: E402


def _iter_case_dirs() -> list[Path]:
    """Collect benchmark case directories under testing/cases."""
    case_root = TESTING_ROOT / "cases" / "benchmark_history_compaction"
    if not case_root.exists():
        raise FileNotFoundError(f"Missing benchmark cases: {case_root}")
    return sorted(path for path in case_root.iterdir() if path.is_dir())


def _format_int(value: int) -> str:
    """Format an integer with thousands separators."""
    return f"{value:,}"


def _format_pct(value: float) -> str:
    """Format a percent with two decimal places."""
    return f"{value:.2f}%"


def _saved_percent(base: int, current: int) -> float:
    """Return the percentage saved vs the base value."""
    if base == 0:
        return 0.0
    return (1 - (current / base)) * 100


def _build_table(variants: list[dict], case_dir: Path) -> str:
    """Build the tier table for stored variant outputs."""
    if not variants:
        raise AssertionError("Missing variants for benchmark case.")

    outputs: dict[str, dict[str, int]] = {}
    for variant in variants:
        name = str(variant.get("name", "")).strip()
        output_ref = str(variant.get("output", "")).strip()
        if not name or not output_ref:
            raise AssertionError("Variant entries require name + output.")
        output_path = case_dir / "input" / output_ref
        if not output_path.exists():
            raise FileNotFoundError(f"Missing output file: {output_path}")
        text = output_path.read_text(encoding="utf-8")
        if compact_mod.tiktoken is None:
            raise RuntimeError("tiktoken is required for benchmark tests.")
        chars = int(compact_mod._measure_text(text, "chars", "cl100k_base"))
        tokens = int(compact_mod._measure_text(text, "tokens", "cl100k_base"))
        outputs[name] = {"chars": chars, "tokens": tokens}

    if "unified" not in outputs:
        raise AssertionError("Benchmark variants must include unified output.")
    unified_chars = outputs["unified"]["chars"]
    unified_tokens = outputs["unified"]["tokens"]

    lines = ["variant | chars | tokens | chars saved vs unified | tokens saved vs unified"]
    for variant in variants:
        name = str(variant.get("name", "")).strip()
        stats = outputs.get(name)
        if stats is None:
            raise AssertionError(f"Missing stats for variant {name}")
        chars = stats["chars"]
        tokens = stats["tokens"]
        chars_saved = _saved_percent(unified_chars, chars)
        tokens_saved = _saved_percent(unified_tokens, tokens)
        lines.append(
            " | ".join(
                [
                    name,
                    _format_int(chars),
                    _format_int(tokens),
                    _format_pct(chars_saved),
                    _format_pct(tokens_saved),
                ]
            )
        )
    return "\n".join(lines)


def test_history_compaction_tier_tables_snapshot() -> None:
    """Match the derived tier table against the expected snapshot."""
    if yaml is None:  # pragma: no cover
        raise RuntimeError("PyYAML is required for benchmark tests.")
    for case_dir in _iter_case_dirs():
        commands_path = case_dir / "input" / "commands.yaml"
        if not commands_path.exists():
            raise FileNotFoundError(f"Missing commands: {commands_path}")
        commands = yaml.safe_load(commands_path.read_text(encoding="utf-8"))
        variants = commands.get("variants", [])
        if not variants:
            raise AssertionError("Benchmark commands must include variants.")
        actual = _build_table(variants, case_dir).strip()
        expected = (
            case_dir / "expected_output" / "tier_table.txt"
        ).read_text(encoding="utf-8").strip().lstrip("\ufeff")
        assert actual == expected
