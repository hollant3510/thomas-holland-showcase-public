---
name: router
description: Use the agent-friendly git wrapper router, its built-in commands (state/diff/log/files/branch/scan/base/compare/show/pr), routing rules, and config. Use when asked how to run the wrapper, enable/disable commands, or extend router behavior.
---

# Router

Use this skill when working with the agent-friendly git wrapper router.

## Workflow

1) Read `documentation/wrappers.md` for entry points + routing overview.
2) Use `documentation/subcommands.md` for the full command catalog + flags.
3) For command-specific details, open the matching reference (ex: `references/state.md`).
4) For setup/venv/PATH wiring, use the `agent-setup` skill and `documentation/setup.md`.
5) If modifying router code, follow `documentation/standards/comments-and-style.md`
   and `documentation/standards/python.md` (docstrings required for all modules/classes/functions).

## References

- `documentation/wrappers.md`: entry points, router responsibilities, and routing flow.
- `documentation/quickstart.md`: command list with short examples and use cases.
- `documentation/subcommands.md`: full command catalog with flags + example outputs.
- `documentation/testing.md`: how to run tests and benchmark cases.
- `references/commands.md`: high-level command list and short usage notes.
- `references/state.md`: `router state` behavior and outputs.
- `references/diff.md`: `router diff` flags, compact modes, and noise controls.
- `references/log.md`: `router log` modes and filters.
- `references/history.md`: `router history` behaviors and compact profiles.
- `references/files.md`: `router files` and output shaping flags.
- `references/branch.md`: branch hygiene commands and guardrails.
- `references/scan.md`: conflict scan behavior and scopes.
- `references/base.md`: merge-base helper usage.
- `references/compare.md`: compare range handling and output shaping.
- `references/show.md`: commit view + patch controls.
- `references/pr.md`: PR commands and summaries.
- `references/config.md`: config layout, profiles, and defaults.
- `references/guardrails.md`: protected branches, safe mode, and overrides.
- `references/logging.md`: logging flags and formats.
- `documentation/guides/history_compaction_guide.md`: how to use compaction profiles in practice.
- `documentation/benchmarks/history_compaction_benchmark.md`: benchmark tables and context on savings.
- `config/cli_router.yaml`: default profiles + routing settings.
- `config/cli_router_custom_commands.yaml`: custom command sequences.
- `testing/test_catalog.md`: test coverage map and case intent.
- `documentation/standards/comments-and-style.md`: code commenting requirements.
- `documentation/standards/python.md`: Python conventions for this repo.

