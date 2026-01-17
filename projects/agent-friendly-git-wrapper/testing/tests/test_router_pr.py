"""Tests for router PR helpers and template behavior."""
from __future__ import annotations

import json
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
from app.utils import exec_utils  # noqa: E402

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    yaml = None  # type: ignore


def _iter_case_dirs() -> list[Path]:
    """Return sorted test case directories for PR scenarios."""
    root = TESTING_ROOT / "cases" / "wrapper_router_pr"
    return sorted([p for p in root.iterdir() if p.is_dir()])


def _load_config(path: Path) -> dict:
    """Load a YAML config dict for a PR test case."""
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


def _fake_pr_payload() -> dict:
    """Return a minimal PR payload for gh pr view responses."""
    return {
        "title": "Example PR",
        "state": "OPEN",
        "isDraft": False,
        "url": "https://example.com/pr/1",
        "mergeable": "MERGEABLE",
        "mergeStateStatus": "CLEAN",
        "reviewDecision": "APPROVED",
        "statusCheckRollup": [
            {"state": "SUCCESS"},
            {"state": "PENDING"},
        ],
        "labels": [{"name": "bug"}, {"name": "needs-review"}],
        "files": [{"path": "a.txt"}, {"path": "b.txt"}],
    }


def _fake_body() -> str:
    """Return a PR body template with a preserved Notes block."""
    return "# Summary\n- previous\n\n# Notes\n<!-- NOTES START -->\nKeep this note\n<!-- NOTES END -->\n"


def _fake_run_factory(record: dict) -> callable:
    """Return a subprocess.run stub that records PR body changes."""
    def _fake_run(
        args,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        **kwargs,
    ):
        """Stub gh subprocess calls for PR tests."""
        cmd = [str(a) for a in args]
        if cmd and cmd[0] == "gh":
            if cmd[1:3] == ["pr", "view"] and "--json" in cmd:
                if "body" in cmd:
                    payload = {"body": _fake_body()}
                else:
                    payload = _fake_pr_payload()
                return subprocess.CompletedProcess(cmd, 0, json.dumps(payload), "")
            if cmd[1:3] == ["pr", "create"]:
                if "--body-file" in cmd:
                    body_path = Path(cmd[cmd.index("--body-file") + 1])
                    record["create_body"] = body_path.read_text(encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, "created\n", "")
            if cmd[1:3] == ["pr", "edit"]:
                if "--body-file" in cmd:
                    body_path = Path(cmd[cmd.index("--body-file") + 1])
                    record["edit_body"] = body_path.read_text(encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, "updated\n", "")
            if cmd[1:3] == ["pr", "ready"]:
                return subprocess.CompletedProcess(cmd, 0, "ready\n", "")
            return subprocess.CompletedProcess(cmd, 0, "", "")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    return _fake_run


def test_router_pr_cases(tmp_path, monkeypatch, capsys) -> None:
    """Run fixture-driven PR command cases."""
    for case_dir in _iter_case_dirs():
        record: dict = {}
        monkeypatch.setattr(router_cli.shutil, "which", lambda _: "gh")
        monkeypatch.setattr(exec_utils.subprocess, "run", _fake_run_factory(record))

        config_path = case_dir / "input" / "config.yaml"
        command_path = case_dir / "input" / "command.txt"
        command = command_path.read_text(encoding="utf-8").strip().lstrip("\ufeff")
        args = shlex.split(command)

        base_config = _load_config(PROJECT_ROOT / "config" / "cli_router.yaml")
        merged = _merge_dict(base_config, _load_config(config_path))
        pr_helpers = merged.setdefault("pr_helpers", {})
        templates = pr_helpers.setdefault("templates", {})
        templates["basic"] = str(PROJECT_ROOT / "documentation" / "pr_templates" / "basic.md")
        pr_helpers.setdefault("default_template", "basic")

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

        if case_dir.name == "case_create":
            assert "# Summary" in record.get("create_body", "")
        if case_dir.name == "case_update":
            assert "Keep this note" in record.get("edit_body", "")


