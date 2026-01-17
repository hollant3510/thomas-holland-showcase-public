"""Process execution helpers for git/gh tooling."""
from __future__ import annotations

import subprocess
from typing import Callable, Sequence


def git_output(
    args: Sequence[str],
    record_resolved: Callable[[str, Sequence[str]], None],
    get_timeout: Callable[[], float | None],
) -> str:
    """Run git and return stdout, raising when the command fails."""
    record_resolved("git", args)
    timeout = get_timeout()
    proc = subprocess.run(
        ["git", *[str(a) for a in args]],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def run_git(
    args: Sequence[str],
    record_resolved: Callable[[str, Sequence[str]], None],
    get_timeout: Callable[[], float | None],
    **kwargs,
) -> subprocess.CompletedProcess:
    """Run git and return the CompletedProcess."""
    record_resolved("git", args)
    timeout = get_timeout()
    if "timeout" not in kwargs:
        kwargs["timeout"] = timeout
    return subprocess.run(["git", *[str(a) for a in args]], **kwargs)


def run_gh(
    args: Sequence[str],
    record_resolved: Callable[[str, Sequence[str]], None],
    get_timeout: Callable[[], float | None],
) -> subprocess.CompletedProcess:
    """Run gh and return the CompletedProcess."""
    record_resolved("gh", args)
    timeout = get_timeout()
    return subprocess.run(
        ["gh", *[str(a) for a in args]],
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def run_tool(
    tool: str,
    args: Sequence[str],
    record_resolved: Callable[[str, Sequence[str]], None],
    get_timeout: Callable[[], float | None],
    **kwargs,
) -> subprocess.CompletedProcess:
    """Run a tool command and return the CompletedProcess."""
    record_resolved(tool, args)
    timeout = get_timeout()
    if "timeout" not in kwargs:
        kwargs["timeout"] = timeout
    return subprocess.run([tool, *[str(a) for a in args]], **kwargs)
