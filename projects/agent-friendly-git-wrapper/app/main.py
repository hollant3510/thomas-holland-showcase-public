"""CLI entrypoint for agent-friendly git wrapper."""
from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.cli import router_cli  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser for the wrapper app."""
    parser = argparse.ArgumentParser(description="Agent-friendly git/gh router.")
    sub = parser.add_subparsers(dest="command", required=True)

    router = sub.add_parser("router", help="Route git/gh commands via config")
    router.add_argument("--config", default="")
    router.add_argument("--tool", choices=["git", "gh"], default="")
    router.add_argument("--check", action="store_true", help="Check routing decision only.")
    router.add_argument("args", nargs=argparse.REMAINDER)
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Run the wrapper CLI and return an exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "router":
        return router_cli.run(
            [
                *([f"--config={args.config}"] if args.config else []),
                *([f"--tool={args.tool}"] if args.tool else []),
                *(["--check"] if args.check else []),
                *args.args,
            ]
        )
    parser.error("Unsupported command")
    return 2


def main() -> None:
    """CLI entrypoint for console execution."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()

