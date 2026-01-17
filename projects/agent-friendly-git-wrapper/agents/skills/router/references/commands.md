# Router Commands

This file documents the built-in router commands supported by
`projects/agent-friendly-git-wrapper`.

## Commands

- `router state` - Compact repo/branch/worktree snapshot.
  - See `references/state.md` for details.
- `router diff` - Diff with noise filtering and detail controls.
  - See `references/diff.md` for details.
- `router log` - One-line commit history for quick context.
  - See `references/log.md` for details.
- `router history` - Commit history with optional patch output and compact controls.
  - See `references/history.md` for details.
- `router files` - Impacted files for working tree, commit, or range.
  - See `references/files.md` for details.
- `router branch` - Branch hygiene helpers (reports, cleanup, audit, prune, sync).
  - See `references/branch.md` for details.
- `router scan` - Repository scans (conflict markers, etc.).
  - See `references/scan.md` for details.
- `router base` - Resolve merge-base between target and base.
  - See `references/base.md` for details.
- `router compare` - Diff between two refs or branches with diff-style options.
  - See `references/compare.md` for details.
- `router show` - Commit metadata with optional patch/stat output.
  - See `references/show.md` for details.
- `router pr` - PR status, mergeability, and template-driven workflows.
  - See `references/pr.md` for details.

## Notes

- Built-in commands are enabled/disabled via the `commands` section in
  `config/cli_router.yaml`.
- Custom macro commands live in `config/cli_router_custom_commands.yaml`.

