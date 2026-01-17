"""Handle the router pr command."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Callable


def _pr_config(config: dict) -> dict:
    """Return PR helper configuration from the router config."""
    pr_cfg = config.get("pr_helpers", {})
    if not isinstance(pr_cfg, dict):
        return {}
    return pr_cfg


def _gh_json(args: list[str], gh_run: Callable[[list[str]], object]) -> dict:
    """Run gh with JSON output and parse the response."""
    proc = gh_run(args)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "gh command failed")
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"gh returned invalid JSON: {exc}") from exc


def _resolve_template_path(
    template_name: str, config: dict
) -> Path:
    """Resolve a PR template path using config and runtime context."""
    pr_cfg = _pr_config(config)
    templates = pr_cfg.get("templates", {})
    if not isinstance(templates, dict):
        templates = {}
    if template_name not in templates:
        raise RuntimeError(f"router pr: unknown template '{template_name}'")
    raw_path = str(templates[template_name]).strip()
    if not raw_path:
        raise RuntimeError(f"router pr: template path missing for '{template_name}'")
    template_path = Path(raw_path)
    runtime = config.get("_runtime", {}) if isinstance(config.get("_runtime"), dict) else {}
    config_path = runtime.get("config_path")
    if not template_path.is_absolute() and config_path:
        template_path = (Path(config_path).parent / template_path).resolve()
    if not template_path.exists():
        raise RuntimeError(f"router pr: template file not found at {template_path}")
    return template_path


def _pr_notes_markers(config: dict) -> tuple[str, str]:
    """Return the start/end markers for the notes block."""
    pr_cfg = _pr_config(config)
    notes = pr_cfg.get("notes_block", {})
    if not isinstance(notes, dict):
        notes = {}
    start = str(notes.get("start", "<!-- NOTES START -->")).strip() or "<!-- NOTES START -->"
    end = str(notes.get("end", "<!-- NOTES END -->")).strip() or "<!-- NOTES END -->"
    return start, end


def _extract_block(body: str, start: str, end: str) -> str | None:
    """Extract the block between start/end markers, if present."""
    start_idx = body.find(start)
    end_idx = body.find(end)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        return None
    content_start = start_idx + len(start)
    return body[content_start:end_idx]


def _merge_notes(template: str, current: str, start: str, end: str) -> str:
    """Merge notes from the current PR body into the template."""
    notes = _extract_block(current, start, end)
    if notes is None:
        return template
    t_start = template.find(start)
    t_end = template.find(end)
    if t_start == -1 or t_end == -1 or t_end < t_start:
        return template
    return template[: t_start + len(start)] + notes + template[t_end:]


def _pr_status_payload(repo: str | None, gh_run: Callable[[list[str]], object]) -> dict:
    """Fetch PR status metadata via gh."""
    args = [
        "pr",
        "view",
        "--json",
        "title,state,isDraft,url,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,labels,files",
    ]
    if repo:
        args.extend(["--repo", repo])
    return _gh_json(args, gh_run)


def _summarize_checks(checks: list[dict]) -> dict:
    """Summarize status check counts."""
    summary = {"total": 0, "success": 0, "failed": 0, "pending": 0}
    for check in checks:
        state = str(check.get("state", "")).upper()
        summary["total"] += 1
        if state in {"SUCCESS", "SKIPPED", "NEUTRAL"}:
            summary["success"] += 1
        elif state in {"FAILURE", "ERROR", "CANCELLED", "TIMED_OUT"}:
            summary["failed"] += 1
        else:
            summary["pending"] += 1
    return summary


def dispatch_pr(
    args: list[str],
    config: dict,
    gh_run: Callable[[list[str]], object],
    ensure_gh: Callable[[], None],
) -> int:
    """Dispatch PR-related subcommands."""
    if not args:
        raise RuntimeError("router pr: subcommand required")
    ensure_gh()

    sub = args[0]
    rest = args[1:]
    pr_cfg = _pr_config(config)
    default_template = str(pr_cfg.get("default_template", "basic")).strip() or "basic"
    repo = ""

    if sub in {"-h", "--help"}:
        sys.stdout.write(
            "usage: router pr <status|merge-state|view|open-draft|open+status|ready+merge-state|create|update> [...]\n"
        )
        return 0

    if sub in {"status", "merge-state"}:
        idx = 0
        while idx < len(rest):
            token = rest[idx]
            if token == "--repo":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router pr: --repo requires a value")
                repo = rest[idx + 1].strip()
                idx += 2
                continue
            raise RuntimeError(f"router pr {sub}: unknown argument '{token}'")
        payload = _pr_status_payload(repo or None, gh_run)
        checks = payload.get("statusCheckRollup", []) or []
        checks_summary = _summarize_checks(checks if isinstance(checks, list) else [])
        if sub == "status":
            labels = payload.get("labels", []) or []
            label_names = [str(item.get("name", "")) for item in labels if isinstance(item, dict)]
            sys.stdout.write(f"title: {payload.get('title','')}\n")
            sys.stdout.write(f"state: {payload.get('state','')}\n")
            sys.stdout.write(f"draft: {payload.get('isDraft', False)}\n")
            sys.stdout.write(f"review: {payload.get('reviewDecision','')}\n")
            sys.stdout.write(
                f"checks: total={checks_summary['total']} success={checks_summary['success']} "
                f"failed={checks_summary['failed']} pending={checks_summary['pending']}\n"
            )
            sys.stdout.write(f"mergeable: {payload.get('mergeable','')}\n")
            sys.stdout.write(f"merge_state: {payload.get('mergeStateStatus','')}\n")
            if label_names:
                sys.stdout.write(f"labels: {', '.join(label_names)}\n")
            sys.stdout.write(f"url: {payload.get('url','')}\n")
            return 0
        sys.stdout.write(f"mergeable: {payload.get('mergeable','')}\n")
        sys.stdout.write(f"merge_state: {payload.get('mergeStateStatus','')}\n")
        sys.stdout.write(
            f"checks: total={checks_summary['total']} success={checks_summary['success']} "
            f"failed={checks_summary['failed']} pending={checks_summary['pending']}\n"
        )
        sys.stdout.write(f"review: {payload.get('reviewDecision','')}\n")
        return 0

    if sub == "view":
        summary = False
        idx = 0
        while idx < len(rest):
            token = rest[idx]
            if token == "--summary":
                summary = True
                idx += 1
                continue
            if token == "--repo":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router pr view: --repo requires a value")
                repo = rest[idx + 1].strip()
                idx += 2
                continue
            raise RuntimeError(f"router pr view: unknown argument '{token}'")
        if not summary:
            proc = gh_run(["pr", "view"])
            if proc.stdout:
                sys.stdout.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            return proc.returncode
        payload = _pr_status_payload(repo or None, gh_run)
        checks = payload.get("statusCheckRollup", []) or []
        checks_summary = _summarize_checks(checks if isinstance(checks, list) else [])
        labels = payload.get("labels", []) or []
        label_names = [str(item.get("name", "")) for item in labels if isinstance(item, dict)]
        files = payload.get("files", []) or []
        sys.stdout.write(f"title: {payload.get('title','')}\n")
        if label_names:
            sys.stdout.write(f"labels: {', '.join(label_names)}\n")
        sys.stdout.write(f"files: {len(files)}\n")
        sys.stdout.write(
            f"checks: total={checks_summary['total']} success={checks_summary['success']} "
            f"failed={checks_summary['failed']} pending={checks_summary['pending']}\n"
        )
        return 0

    if sub in {"open-draft", "open+status", "ready+merge-state", "create", "update"}:
        template = default_template
        draft = False
        title = ""
        base = ""
        head = ""
        fill = False
        idx = 0
        while idx < len(rest):
            token = rest[idx]
            if token == "--template":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router pr: --template requires a value")
                template = rest[idx + 1].strip()
                idx += 2
                continue
            if token == "--draft":
                draft = True
                idx += 1
                continue
            if token == "--title":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router pr: --title requires a value")
                title = rest[idx + 1]
                idx += 2
                continue
            if token == "--base":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router pr: --base requires a value")
                base = rest[idx + 1]
                idx += 2
                continue
            if token == "--head":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router pr: --head requires a value")
                head = rest[idx + 1]
                idx += 2
                continue
            if token == "--fill":
                fill = True
                idx += 1
                continue
            if token == "--repo":
                if idx + 1 >= len(rest):
                    raise RuntimeError("router pr: --repo requires a value")
                repo = rest[idx + 1].strip()
                idx += 2
                continue
            raise RuntimeError(f"router pr {sub}: unknown argument '{token}'")

        if sub == "open-draft":
            draft = True

        if sub in {"create", "open-draft", "open+status"}:
            body_file = ""
            args = ["pr", "create"]
            if repo:
                args.extend(["--repo", repo])
            if draft:
                args.append("--draft")
            if title:
                args.extend(["--title", title])
            if base:
                args.extend(["--base", base])
            if head:
                args.extend(["--head", head])
            if fill:
                args.append("--fill")
            template_path = _resolve_template_path(template, config)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as tmp:
                tmp.write(template_path.read_text(encoding="utf-8"))
                body_file = tmp.name
            if body_file:
                args.extend(["--body-file", body_file])
            proc = gh_run(args)
            if proc.stdout:
                sys.stdout.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            if proc.returncode != 0:
                return proc.returncode
            if sub == "open+status":
                return dispatch_pr(["status"] + (["--repo", repo] if repo else []), config, gh_run, ensure_gh)
            return 0

        if sub == "update":
            template_path = _resolve_template_path(template, config)
            template_text = template_path.read_text(encoding="utf-8")
            start, end = _pr_notes_markers(config)
            body_data = _gh_json(
                ["pr", "view", "--json", "body"] + (["--repo", repo] if repo else []),
                gh_run,
            )
            current_body = str(body_data.get("body", ""))
            merged_body = _merge_notes(template_text, current_body, start, end)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as tmp:
                tmp.write(merged_body)
                body_file = tmp.name
            args = ["pr", "edit", "--body-file", body_file]
            if repo:
                args.extend(["--repo", repo])
            proc = gh_run(args)
            if proc.stdout:
                sys.stdout.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            return proc.returncode

        if sub == "ready+merge-state":
            args = ["pr", "ready"]
            if repo:
                args.extend(["--repo", repo])
            proc = gh_run(args)
            if proc.stdout:
                sys.stdout.write(proc.stdout)
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            if proc.returncode != 0:
                return proc.returncode
            return dispatch_pr(["merge-state"] + (["--repo", repo] if repo else []), config, gh_run, ensure_gh)

    raise RuntimeError(f"router pr: unknown subcommand '{sub}'")

