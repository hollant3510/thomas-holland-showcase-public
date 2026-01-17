# Router History

## Purpose

Return commit history with optional patch output and compact controls.

## When to use

- Inspect commit patches across a range (`--patch`).
- Reduce metadata noise by selecting commit header fields.
- Apply compact output to patch data for token savings.

## Usage

```bash
router history --n 10
router history --n 10 --patch
router history --n 20 --range main..feature
router history --since v1.2.0 --patch
router history --commit-meta none --patch
router history --commit-meta short --short-hash
router history --compact
router history --compact=tokens
router history --n 10 --include src/** --exclude docs/**
```

## Flags

- `--n N`: max commits.
- `--since REF` / `--range A..B`: limit commit range.
- `--path PATH`: limit history to a path.
- `--patch` / `--no-patch`: include/exclude patch output.
- `--summary`: shortstat output (no patch).
- `--files-only`: names only (no patch).
- `--name-status`: status + filenames (no patch).
- `--stat`: diffstat (no patch).
- `--noise` / `--noise=LEVEL`: apply diff noise filters when patching.
- `--context N`: unified context for patch output.
- `--compact[=SPEC]`: compact patch output (same options as `router diff`).
- `--ops LIST`: diff-filter ops (added, modified, deleted, renamed, copied, typechange, unmerged, broken, unknown).
- `--include PATTERN[,PATTERN...]`: include pathspecs (comma-delimited, repeatable).
- `--exclude PATTERN[,PATTERN...]`: exclude pathspecs (comma-delimited, repeatable).
- `--auto-tune` / `--no-auto-tune`: override compact auto-tune for this invocation.

Commit metadata controls:

- `--commit-meta MODE`: `none|hash|subject|short|full`.
- `--short-hash`: use abbreviated hash when included.
- `--no-hash`, `--no-author`, `--no-date`, `--no-subject`: remove fields.

## Config

- Default commit meta: `router.history_default_commit_meta`
- Compact meta overrides: `router.history_compact_meta_overrides` (ex: `tokens: none`)
- Default patch on/off: `router.history_default_patch`
- Diff noise defaults: `router.diff_default_noise` + `router.diff_noise_levels`
- Compact defaults/profiles: `router.compact_defaults`, `router.compact_profiles`
- Auto-tune compact: `router.compact_auto_tune`
