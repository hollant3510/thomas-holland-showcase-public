"""Tests for router branch command scenarios."""
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
    _run(["git", "init", "-b", "main"], repo_dir)
    _run(["git", "config", "user.email", "test@example.com"], repo_dir)
    _run(["git", "config", "user.name", "Test User"], repo_dir)
    (repo_dir / "sample.txt").write_text("Hello\n", encoding="utf-8")
    _run(["git", "add", "sample.txt"], repo_dir)
    _run(["git", "commit", "-m", "initial"], repo_dir)


def _iter_case_dirs() -> list[Path]:
    """Return sorted case directories for branch command tests."""
    root = TESTING_ROOT / "cases" / "wrapper_router_branch"
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


def _commit_change(repo_dir: Path, message: str, content: str = "Update\n") -> None:
    """Commit a content change for test scenarios."""
    path = repo_dir / "sample.txt"
    path.write_text(content, encoding="utf-8")
    _run(["git", "add", "sample.txt"], repo_dir)
    _run(["git", "commit", "-m", message], repo_dir)


def _checkout(repo_dir: Path, branch: str, create: bool = False) -> None:
    """Checkout an existing or new branch in the test repo."""
    if create:
        _run(["git", "checkout", "-b", branch], repo_dir)
    else:
        _run(["git", "checkout", branch], repo_dir)


def _setup_remote(repo_dir: Path, remote_dir: Path) -> None:
    """Create a bare remote and add it as origin."""
    _run(["git", "init", "--bare", str(remote_dir)], repo_dir)
    _run(["git", "remote", "add", "origin", str(remote_dir)], repo_dir)
    _run(["git", "push", "-u", "origin", "main"], repo_dir)


def _apply_setup(repo_dir: Path, setup: dict, tmp_path: Path) -> None:
    """Configure repo branches and remotes for branch tests."""
    base_branch = setup.get("base_branch", "main")
    merged_branch = setup.get("merged_branch")
    unmerged_branch = setup.get("unmerged_branch")
    ahead_branch = setup.get("ahead_branch")
    remote = bool(setup.get("remote", False))
    push_branches = setup.get("push_branches", [])
    delete_remote = setup.get("delete_remote_branches", [])
    checkout = setup.get("checkout", base_branch)

    if base_branch != "main":
        _checkout(repo_dir, base_branch, create=True)
        _commit_change(repo_dir, "base commit", "Base\n")
        _checkout(repo_dir, "main")

    if merged_branch:
        _checkout(repo_dir, merged_branch, create=True)
        _commit_change(repo_dir, "merged change", "Merged\n")
        _checkout(repo_dir, base_branch)
        _run(["git", "merge", "--no-ff", merged_branch, "-m", "merge"], repo_dir)

    if unmerged_branch:
        _checkout(repo_dir, unmerged_branch, create=True)
        _commit_change(repo_dir, "unmerged change", "Unmerged\n")

    if ahead_branch:
        _checkout(repo_dir, ahead_branch, create=True)
        _commit_change(repo_dir, "ahead change", "Ahead\n")

    if remote:
        remote_dir = tmp_path / f"remote_{repo_dir.name}"
        _setup_remote(repo_dir, remote_dir)
        for br in push_branches:
            _run(["git", "push", "-u", "origin", br], repo_dir)
        for br in delete_remote:
            _run(["git", "push", "origin", "--delete", br], repo_dir)

    if checkout:
        _checkout(repo_dir, checkout)


def test_router_branch_cases(tmp_path, monkeypatch, capsys) -> None:
    """Run branch command cases against fixture setups."""
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
            _apply_setup(case_repo, setup, tmp_path)

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

        stdout_contains = case_dir / "expected_output" / "output_contains.txt"
        expected_lines = [
            line.strip().lstrip("\ufeff")
            for line in stdout_contains.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        for line in expected_lines:
            assert line in output.out


