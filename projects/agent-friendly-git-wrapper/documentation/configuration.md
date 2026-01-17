# Configuration

This guide explains how the router configuration is structured and where to
change defaults, profiles, and guardrails.

## Files

- `config/cli_router.yaml`: primary router configuration (defaults, profiles,
  guardrails, command registry).
- `config/cli_router_custom_commands.yaml`: optional macro command sequences.

## Router defaults

The `router` section controls defaults for diff/history output shaping:

- `diff_default_detail`, `diff_default_context`, `diff_default_noise`
- `compact_defaults` and `compact_profiles`
- `history_default_commit_meta`, `history_default_patch`

If you want a different default profile for a specific use case, set
`router.default_profile`.

## Profiles

Profiles let you tailor behavior for different agents (worker vs. orchestrator,
docs vs. code). They can override router defaults and guardrails.

Example idea:

- A worker profile can disable push/rebase and enforce clean worktrees.
- An orchestrator profile can allow overrides and broader scope.

Profiles live under `profiles:` in `config/cli_router.yaml`.

## Guardrails

Guardrails define protected branches and safe-mode blocks. Use them to prevent
destructive operations unless the agent explicitly overrides.

Relevant keys:

- `guardrails.protected_branches`
- `guardrails.protected_ops`
- `guardrails.require_clean_ops`
- `guardrails.safe_block_ops`
- `guardrails.safe_mode`

## Command routing

Commands can be enabled/disabled under `commands:` and overridden per tool
under `command_overrides:`.

For overlap commands (`status`, `help`, `version`), the default tool is defined
under `overlap_commands:`.

## Practical tweaks

- Change default noise level: `router.diff_default_noise`
- Enable compact tokens profile by default: `router.default_profile: tokens`
- Limit a worker agent to a subpath via profile overrides + `--include`

For flag-level overrides, see `documentation/quickstart.md` and
`documentation/guides/history_compaction_guide.md`.
