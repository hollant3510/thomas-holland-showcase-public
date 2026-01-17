# router branch

Branch hygiene helpers for reporting, cleanup, audits, pruning, and sync status.

## Subcommands

- `report-merged` — list branches merged into base.
- `cleanup-merged` — delete merged local branches (dry-run default).
- `audit-unmerged` — list branches not merged into base with age/author/ahead/behind.
- `prune-local` — prune local branches whose upstream is gone (dry-run default).
- `sync-report` — per-branch ahead/behind status vs upstream.
- `validate-name` — validate branch naming against configured patterns.

## Usage

router branch validate-name [--branch NAME] [--override]
router branch report-merged [--base BRANCH] [--remote NAME] [--local-only]
router branch cleanup-merged [--base BRANCH] [--remote NAME] [--dry-run|--apply]
router branch audit-unmerged [--base BRANCH] [--remote NAME] [--local-only]
router branch prune-local [--remote NAME] [--pattern GLOB] [--dry-run|--apply]
router branch sync-report [--remote NAME]

## Config defaults

- `branch_hygiene.default_base`: base branch when not provided.
- `branch_hygiene.default_remote`: remote name (default `origin`).
- `branch_hygiene.include_remotes`: include remote branches in reports.
- `branch_hygiene.fetch_before`: fetch/prune before reporting.
- `branch_hygiene.protected_branches` / `protected_patterns`: never delete.
- `branch_hygiene.ignore_patterns`: skip from reports.
- `branch_hygiene.merge_policies`: merge rules (ex: main only from develop).
- `branch_hygiene.cleanup.default_apply`: default apply for cleanup.
- `branch_hygiene.cleanup.enforce_merge_policy`: block cleanup when policy violates.
- `branch_hygiene.prune.pattern`: glob for prune-local.
- `branch_hygiene.prune.default_apply`: default apply for prune-local.
- `branch_hygiene.name_patterns`: allowed branch naming patterns.

## Notes

- Cleanup never removes the current branch.
- Remote branches are reported by default, but cleanup only touches local branches.
