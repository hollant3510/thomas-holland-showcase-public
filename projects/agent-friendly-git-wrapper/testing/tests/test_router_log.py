"""Tests for router log command scenarios and logging output."""
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
    """Run a command in the provided working directory."""
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(repo_dir: Path) -> None:
    """Initialize a git repo with a baseline commit."""
    _run(["git", "init"], repo_dir)
    _run(["git", "config", "user.email", "test@example.com"], repo_dir)
    _run(["git", "config", "user.name", "Test User"], repo_dir)
    (repo_dir / "sample.txt").write_text("Hello\n", encoding="utf-8")
    _run(["git", "add", "sample.txt"], repo_dir)
    _run(["git", "commit", "-m", "initial"], repo_dir)


def _iter_case_dirs() -> list[Path]:
    """Return sorted test case directories for log scenarios."""
    root = TESTING_ROOT / "cases" / "wrapper_router_log"
    return sorted([p for p in root.iterdir() if p.is_dir()])


def _load_config(path: Path) -> dict:
    """Load a YAML config dict for a test case."""
    if yaml is None:  # pragma: no cover
        pytest.skip("PyYAML not installed")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise AssertionError("config must be a dict")
    return data


def _merge_dict(base: dict, override: dict) -> dict:
    """Return a shallow+recursive merge of two dict objects."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged.get(key, {}), value)
        else:
            merged[key] = value
    return merged


def _apply_commits(case_repo: Path, commits: list[dict]) -> None:
    """Apply commit definitions from the test setup file."""
    for entry in commits:
        message = entry.get("message", "update")
        file_path = entry.get("file", "sample.txt")
        path = case_repo / file_path
        if "content" in entry:
            content = entry["content"]
            path.write_text(content, encoding="utf-8")
        else:
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            path.write_text(f"{existing}{message}\n", encoding="utf-8")
        _run(["git", "add", file_path], case_repo)
        _run(["git", "commit", "-m", message], case_repo)


def test_router_log_cases(tmp_path, monkeypatch, capsys) -> None:
    """Run fixture-driven router log cases."""
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

        short_hash = False
        if setup_path.exists():
            setup = _load_config(setup_path)
            commits = setup.get("extra_commits", [])
            if commits:
                _apply_commits(case_repo, commits)
            short_hash = bool(setup.get("short_hash", False))

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

        output_contains = case_dir / "expected_output" / "output_contains.txt"
        expected_lines = [
            line.strip().lstrip("\ufeff")
            for line in output_contains.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for line in expected_lines:
            assert line in output.out

        if short_hash:
            first_line = output.out.strip().splitlines()[0]
            token = first_line.split(" ", 1)[0]
            assert 4 <= len(token) <= 8


def test_router_log_includes_resolved(tmp_path, monkeypatch) -> None:
    """Assert router logging includes resolved command details."""
    if shutil.which("git") is None:
        pytest.skip("git not available")
    case_repo = tmp_path / "repo_log_resolved"
    case_repo.mkdir()
    _init_repo(case_repo)
    monkeypatch.chdir(case_repo)

    base_config = _load_config(PROJECT_ROOT / "config" / "cli_router.yaml")
    router_cfg = base_config.setdefault("router", {})
    custom_default = PROJECT_ROOT / "config" / "cli_router_custom_commands.yaml"
    custom_current = str(router_cfg.get("custom_commands_file", "")).strip()
    if not custom_current or not Path(custom_current).is_absolute():
        router_cfg["custom_commands_file"] = str(custom_default)
    config_path = tmp_path / "config_log_resolved.yaml"
    config_path.write_text(yaml.safe_dump(base_config, sort_keys=False), encoding="utf-8")

    log_path = tmp_path / "router_log_resolved.txt"
    router_args = [
        "--config",
        str(config_path),
        "--log",
        "--log-file",
        str(log_path),
        "state",
    ]
    rc = router_cli.run(router_args)
    assert rc == 0
    log_text = log_path.read_text(encoding="utf-8")
    assert "resolved:" in log_text
    assert "git rev-parse --show-toplevel" in log_text




