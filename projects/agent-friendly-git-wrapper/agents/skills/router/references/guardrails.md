# Guardrails

Global safety switches enforced by the router for risky operations.

## Flags

- `--override` / `--i-know-what-im-doing`: bypass guardrails for this invocation.
- `--require-clean`: require clean worktree regardless of command.
- `--safe`: enable safe mode (blocks destructive ops).
- `--profile safe`: same as `--safe`.

## Config

See `guardrails` in `config/cli_router.yaml`.

Key options:
- `protected_branches` / `protected_patterns`: branches guarded against risky ops.
- `protected_ops`: operations blocked on protected branches.
- `require_clean_ops`: operations that require a clean worktree.
- `safe_block_ops`: operations blocked in safe mode.
- `branch_name_patterns`: allowed branch naming globs.
- `enforce_branch_name_ops`: ops that require matching patterns.
- `merge_policies`: rules like "main only from develop".
- `conflict_scan.*`: defaults for `router scan conflicts`.

