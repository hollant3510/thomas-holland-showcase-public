# Quickstart Commands

This page lists the most common router commands with a short description of
what each does and when it is useful. Commands are shown with the repo-root
`router.sh` entrypoint. If you set up a `router` alias, you can replace the
prefix with `router`.

## Common flags

These flags apply across multiple commands and let agents tighten output:

- `--profile <name>`: apply a profile from `config/cli_router.yaml`.
- `--compact` / `--compact=tokens`: compact diff output for lower token usage.
- `--noise` / `--noise=max`: apply whitespace/noise filters.
- `--context N`: set diff context lines (e.g., `--context 0` for U0).
- `--include` / `--exclude`: scope output to paths or patterns.
- `--safe`, `--require-clean`, `--override`: guardrail behavior.

## Core commands

```text
projects/agent-friendly-git-wrapper/router.sh status
```
Checks git status through the router. Useful for quick repo state checks.

```text
projects/agent-friendly-git-wrapper/router.sh state
```
Prints a compact repo snapshot (branch, clean/dirty, ahead/behind).

```text
projects/agent-friendly-git-wrapper/router.sh diff
```
Shows a diff with router defaults (noise filtering, compact rules if enabled).

```text
projects/agent-friendly-git-wrapper/router.sh log --n 10
```
Shows a one-line history summary for recent commits.

```text
projects/agent-friendly-git-wrapper/router.sh history --n 10
```
Shows commit history with patch output, optionally compacted.

```text
projects/agent-friendly-git-wrapper/router.sh files --changed
```
Lists files changed in the working tree (fast triage view).

```text
projects/agent-friendly-git-wrapper/router.sh compare main..feature
```
Compares two refs with diff-style options.

```text
projects/agent-friendly-git-wrapper/router.sh show HEAD
```
Shows a single commit summary, with optional patch/stat output.

```text
projects/agent-friendly-git-wrapper/router.sh base
```
Resolves the merge base against the configured default base branch.

```text
projects/agent-friendly-git-wrapper/router.sh scan conflicts
```
Scans for conflict markers in the working tree.

## Branch hygiene

```text
projects/agent-friendly-git-wrapper/router.sh branch report-merged
```
Lists branches already merged into the base branch.

```text
projects/agent-friendly-git-wrapper/router.sh branch cleanup-merged --dry-run
```
Shows which merged branches would be deleted.

```text
projects/agent-friendly-git-wrapper/router.sh branch audit-unmerged
```
Lists branches not merged into the base branch, with age details.

```text
projects/agent-friendly-git-wrapper/router.sh branch sync-report
```
Shows ahead/behind status against upstream.

## GitHub (gh) routing

```text
projects/agent-friendly-git-wrapper/router.sh --tool gh pr list
```
Routes to `gh` for a list of PRs (requires gh installed).

```text
projects/agent-friendly-git-wrapper/router.sh pr status
```
Summarizes PR checks and review status.

```text
projects/agent-friendly-git-wrapper/router.sh pr merge-state
```
Shows whether the PR is mergeable and why it is blocked.

```text
projects/agent-friendly-git-wrapper/router.sh pr view --summary
```
Short summary of a PR (title, labels, files, checks).

```text
projects/agent-friendly-git-wrapper/router.sh pr open-draft
```
Creates a draft PR from the configured template.

```text
projects/agent-friendly-git-wrapper/router.sh pr open+status
```
Creates/opens a PR and then prints a status summary.

```text
projects/agent-friendly-git-wrapper/router.sh pr ready+merge-state
```
Marks a PR ready for review and prints mergeability status.

```text
projects/agent-friendly-git-wrapper/router.sh pr create --template basic
```
Creates a PR using the configured template.

```text
projects/agent-friendly-git-wrapper/router.sh pr update --template basic
```
Updates managed sections of a PR body while preserving Notes.
