"""Tests for router diff command cases."""
from __future__ import annotations

import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TESTING_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.cli import router_cli  # noqa: E402

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None  # type: ignore


def _run(cmd: list[str], cwd: Path) -> None:
    """Run a subprocess command for test setup."""
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(repo_dir: Path) -> None:
    """Initialize a git repo with a starter commit."""
    _run(["git", "init"], repo_dir)
    _run(["git", "config", "user.email", "test@example.com"], repo_dir)
    _run(["git", "config", "user.name", "Test User"], repo_dir)
    (repo_dir / "sample.txt").write_text("Hello\n", encoding="utf-8")
    _run(["git", "add", "sample.txt"], repo_dir)
    _run(["git", "commit", "-m", "initial"], repo_dir)


def _iter_case_dirs() -> list[Path]:
    """Return sorted case directories for diff tests."""
    root = TESTING_ROOT / "cases" / "wrapper_router_diff"
    return sorted([p for p in root.iterdir() if p.is_dir()])


def _load_config(path: Path) -> dict:
    """Load a YAML config for test cases."""
    if yaml is None:  # pragma: no cover
        pytest.skip("PyYAML not installed")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise AssertionError("config must be a dict")
    return data


def _merge_dict(base: dict, override: dict) -> dict:
    """Recursively merge override into base for test configs."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged.get(key, {}), value)
        else:
            merged[key] = value
    return merged


def _apply_setup(case_repo: Path, setup: dict) -> None:
    """Apply setup mutations to the test repo."""
    if setup.get("whitespace_change"):
        (case_repo / "sample.txt").write_text("Hello \n", encoding="utf-8")
    if setup.get("content_change"):
        (case_repo / "sample.txt").write_text("Hello\nWorld\n", encoding="utf-8")
    if setup.get("multi_line_change"):
        (case_repo / "sample.txt").write_text("Hello\nWorld\nAgain\n", encoding="utf-8")
    if setup.get("docs_change"):
        docs_path = case_repo / "docs" / "readme.md"
        docs_path.parent.mkdir(parents=True, exist_ok=True)
        docs_path.write_text("Docs update\n", encoding="utf-8")
    if setup.get("multi_change"):
        (case_repo / "keep.txt").write_text("Keep\n", encoding="utf-8")
        (case_repo / "drop.txt").write_text("Drop\n", encoding="utf-8")
        _run(["git", "add", "keep.txt", "drop.txt"], case_repo)
        _run(["git", "commit", "-m", "add extra files"], case_repo)
        (case_repo / "keep.txt").write_text("Keep updated\n", encoding="utf-8")
        (case_repo / "drop.txt").write_text("Drop updated\n", encoding="utf-8")
    if setup.get("nested_change"):
        nested_dir = case_repo / "src"
        nested_dir.mkdir(parents=True, exist_ok=True)
        (nested_dir / "one.txt").write_text("One\n", encoding="utf-8")
        (nested_dir / "two.txt").write_text("Two\n", encoding="utf-8")
        _run(["git", "add", "src/one.txt", "src/two.txt"], case_repo)
        _run(["git", "commit", "-m", "add nested"], case_repo)
        (nested_dir / "one.txt").write_text("One\nMore\n", encoding="utf-8")
        (nested_dir / "two.txt").write_text("Two\nMore\n", encoding="utf-8")
    if setup.get("long_paths_change"):
        long_dir = case_repo / "src" / "components" / "super" / "long" / "nested" / "path" / "segment"
        long_dir.mkdir(parents=True, exist_ok=True)
        for name in ["alpha_component.txt", "beta_component.txt", "gamma_component.txt"]:
            (long_dir / name).write_text("Line 1\nLine 2\n", encoding="utf-8")
        _run(["git", "add", str(long_dir)], case_repo)
        _run(["git", "commit", "-m", "add long path files"], case_repo)
        for name in ["alpha_component.txt", "beta_component.txt", "gamma_component.txt"]:
            (long_dir / name).write_text("Line 1\nLine 2\nLine 3\n", encoding="utf-8")


def test_router_diff_cases(tmp_path, monkeypatch, capsys) -> None:
    """Run diff command cases against fixture setups."""
    if shutil.which("git") is None:
        pytest.skip("git not available")
    for case_dir in _iter_case_dirs():
        config_path = case_dir / "input" / "config.yaml"
        command_path = case_dir / "input" / "command.txt"
        setup_path = case_dir / "input" / "setup.yaml"
        command = command_path.read_text(encoding="utf-8").strip().lstrip("\ufeff")
        args = shlex.split(command)

        case_repo = tmp_path / f"repo_{case_dir.name}"
        case_repo.mkdir()
        _init_repo(case_repo)
        monkeypatch.chdir(case_repo)

        if setup_path.exists():
            setup = _load_config(setup_path)
            _apply_setup(case_repo, setup)

        base_config = _load_config(PROJECT_ROOT / "config" / "cli_router.yaml")
        merged = _merge_dict(base_config, _load_config(config_path))
        router_cfg = merged.setdefault("router", {})
        custom_default = PROJECT_ROOT / "config" / "cli_router_custom_commands.yaml"
        custom_current = str(router_cfg.get("custom_commands_file", "")).strip()
        if not custom_current or not Path(custom_current).is_absolute():
            router_cfg["custom_commands_file"] = str(custom_default)
        merged_path = tmp_path / f"config_{case_dir.name}.yaml"
        merged_path.write_text(yaml.safe_dump(merged, sort_keys=False), encoding="utf-8")

        router_args = ["--config", str(merged_path)]
        router_args.extend(args)

        rc = router_cli.run(router_args)
        output = capsys.readouterr()

        exit_code_path = case_dir / "expected_output" / "exit_code.txt"
        expected_raw = exit_code_path.read_text(encoding="utf-8").strip()
        expected_code = int(expected_raw.lstrip("\ufeff"))
        assert rc == expected_code

        stdout_expected = case_dir / "expected_output" / "output.txt"
        if stdout_expected.exists():
            expected_text = stdout_expected.read_text(encoding="utf-8").strip().lstrip("\ufeff")
            assert output.out.strip() == expected_text

        stdout_contains = case_dir / "expected_output" / "output_contains.txt"
        if stdout_contains.exists():
            expected_lines = [
                line.strip().lstrip("\ufeff")
                for line in stdout_contains.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            for line in expected_lines:
                assert line in output.out

        stdout_not_contains = case_dir / "expected_output" / "output_not_contains.txt"
        if stdout_not_contains.exists():
            unexpected_lines = [
                line.strip().lstrip("\ufeff")
                for line in stdout_not_contains.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            for line in unexpected_lines:
                assert line not in output.out


