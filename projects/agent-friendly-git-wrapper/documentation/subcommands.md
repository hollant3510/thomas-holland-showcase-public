# Subcommand Catalog

This is the reference list for router subcommands, grouped by purpose. Each
entry names what it does and the key flags that shape output. For setup and
quick examples, see `documentation/quickstart.md`. For profiles and guardrails,
see `documentation/configuration.md`.

## Global flags (apply to most commands)

- `--profile <name>`: Select a config profile (default comes from config).
- `--safe`: Block destructive operations (rebase, reset --hard, force push, etc).
- `--require-clean`: Require a clean worktree before mutating ops.
- `--override`: Explicitly override guardrails when allowed.
- `--log / --log-all / --log-file <path> / --log-format <json|toon|txt>`:
  Action logging controls.

## State and inspection

- `router state`
  - Snapshot of repo status: branch, clean/dirty, ahead/behind, active ops.
- `router files`
  - Flags: `--changed`, `--commit <sha>`, `--range <A..B>`, `--since-branch`
  - Output shaping: `--stat`, `--name-status`
- `router show <sha>`
  - Flags: `--patch` (metadata-only by default)
- `router log`
  - Flags: `--n`, `--since`, `--range`, `--path`, `--short-hash`
- `router base`
  - Merge-base helper using configured default base branch.

## Diffs and comparisons

- `router diff`
- `router compare <base>..<head>`
- `router history`

Shared diff-style flags:
- `--noise` / `--noise=<level>`: Apply configured noise filters.
- `--context <N>`: Patch context size (U0/U1/U2).
- `--detail 0..3`: Detail level (files -> name-status -> patch -> patch+stat).
- `--summary`, `--files-only`, `--stat`, `--name-status`
- `--compact` / `--compact=<profile>`: Compact output shaping.
- `--include <path>` / `--exclude <path>`: Path filtering.
- `--ops <spec>`: Optional compact shaping controls.

## Branch hygiene

- `router branch report-merged [--base <branch>]`
- `router branch cleanup-merged --dry-run | --apply`
- `router branch audit-unmerged [--base <branch>]`
- `router branch prune-local`
- `router branch sync-report`
- `router branch validate-name [--override]`

## Safety / guardrails

- `router scan conflicts [--paths <...>]`

## Pull requests (GitHub CLI)

- `router pr status`
- `router pr merge-state`
- `router pr view --summary`
- `router pr open-draft`
- `router pr open+status`
- `router pr ready+merge-state`
- `router pr create --template <name>`
- `router pr update`

## Router passthrough

- `router <git|gh> <command...>`
  - Uses configured routing rules and per-command allow/deny settings.

## Command details

Short, per-command notes on intent, outputs, and common flags, grouped by area.

---
### State and inspection

#### router state

Purpose: fast snapshot of repo state for an agent (branch, clean/dirty, ahead/behind, active ops).

Outputs: compact status text; designed for quick context before running diffs or history.

Example output:
```
branch: feature/agent-friendly-git-wrapper
worktree: clean
ahead/behind: ahead 2, behind 0 (origin/feature/agent-friendly-git-wrapper)
ops: none
```

#### router files

Purpose: list changed files or files touched by a commit/range.

Outputs: file list with optional `--stat` or `--name-status`.

Common flags: `--changed`, `--commit <sha>`, `--range <A..B>`, `--since-branch`.

Example output:
```
M app/router.py
A documentation/subcommands.md
```

#### router show <sha>

Purpose: show commit metadata, with optional patch content.

Outputs: metadata by default; add `--patch` for diff output.

Example output:
```
commit 31d9b6f
author: example-user
date: 2026-01-14
summary: docs: refresh readme navigation and setup docs
```

#### router log

Purpose: compact commit history listing.

Outputs: commit list; supports scoped ranges and paths.

Common flags: `--n`, `--since`, `--range`, `--path`, `--short-hash`.

Example output:
```
31d9b6f docs: refresh readme navigation and setup docs
4c67308 feat: add token-opt profile tweaks
```

#### router base

Purpose: compute merge-base against configured default branch.

Outputs: base commit hash for comparisons.

Example output:
```
5bc3e32
```

---
### Diffs and comparisons

#### router diff

Purpose: diff working tree or refs with compact output shaping.

Outputs: diff or file summary based on detail flags.

Common flags: `--detail`, `--summary`, `--files-only`, `--stat`, `--name-status`,
`--context`, `--noise`, `--compact`, `--include`, `--exclude`.

Example output:
```
M app/router.py
M documentation/subcommands.md
```

#### router compare <base>..<head>

Purpose: compare two refs/branches with the same output shaping as `diff`.

Outputs: diff or summary for the range.

Example output:
```
M documentation/benchmarks/history_compaction_benchmark.md
A documentation/subcommands.md
```

#### router history

Purpose: history-focused diff across a range of commits.

Outputs: diff across multiple commits with compact controls.

Example output:
```
commit 4c67308
M app/router.py
commit 31d9b6f
M README.md
```

---
### Branch hygiene

#### router branch report-merged

Purpose: list branches already merged into a base branch.

Outputs: merged branch list, optionally scoped by `--base`.

Example output:
```
merged: feature/benchmarks
merged: feature/cli-router
```

#### router branch cleanup-merged

Purpose: delete merged branches.

Outputs: dry-run or applied deletion list.

Example output:
```
dry-run: would delete feature/benchmarks
dry-run: would delete feature/cli-router
```

#### router branch audit-unmerged

Purpose: list branches not merged into base and show age/author/upstream status.

Outputs: unmerged branch report.

Example output:
```
feature/wip-search  14d  example-user  ahead 2 / behind 0
```

#### router branch prune-local

Purpose: prune stale local tracking refs.

Outputs: pruned refs summary.

Example output:
```
pruned: origin/feature/old-branch
```

#### router branch sync-report

Purpose: summarize ahead/behind/diverged status per branch.

Outputs: per-branch sync state, including missing upstream.

Example output:
```
main: behind 3 (origin/main)
feature/token-opt: ahead 1 / behind 0 (origin/feature/token-opt)
```

#### router branch validate-name

Purpose: enforce branch naming rules from config.

Outputs: validation result; `--override` allows bypass where configured.

Example output:
```
valid: cc/router/example-user/compact-flags
```

---
### Safety / guardrails

#### router scan conflicts

Purpose: scan for merge conflict markers.

Outputs: file/line matches for `<<<<<<<`, `=======`, `>>>>>>>`.

Common flags: `--paths <...>`.

Example output:
```
app/router.py:214:<<<<<<< HEAD
```

---
### Pull requests (GitHub CLI)

#### router pr status

Purpose: summary of PR checks, reviews, and CI status.

Outputs: condensed PR status view.

Example output:
```
checks: 5/5 passed
reviews: 1 approved
mergeable: yes
```

#### router pr merge-state

Purpose: mergeability + blocking reasons.

Outputs: merge state plus next-action hints.

Example output:
```
blocked: missing review
next: request review from @owner
```

#### router pr view --summary

Purpose: short PR summary (title, labels, files, checks).

Outputs: one-screen summary.

Example output:
```
title: docs: add subcommand catalog
labels: docs
files: 3 changed
```

#### router pr open-draft

Purpose: open a draft PR from configured template.

Outputs: PR URL + status summary.

Example output:
```
created: https://github.com/org/repo/pull/42
status: draft
```

#### router pr open+status

Purpose: create/open PR and immediately display status.

Outputs: PR URL + status summary.

Example output:
```
created: https://github.com/org/repo/pull/43
checks: running
```

#### router pr ready+merge-state

Purpose: mark PR ready and show mergeability.

Outputs: merge state + blockers.

Example output:
```
ready: true
mergeable: blocked (missing review)
```

#### router pr create --template <name>

Purpose: create PR using a named template section.

Outputs: PR creation result + URL.

Example output:
```
created: https://github.com/org/repo/pull/44
template: basic
```

#### router pr update

Purpose: update controlled sections of an existing PR body.

Outputs: updated PR confirmation.

Example output:
```
updated: pull/42 (sections: summary, checklist)
```

---
### Router passthrough

#### router <git|gh> <command...>

Purpose: pass through to the configured tool with router guardrails.

Outputs: underlying git/gh output, subject to guardrails and logging.

Example output:
```
router: intercepted git; use 'router' or 'router.sh' for direct routing
```
