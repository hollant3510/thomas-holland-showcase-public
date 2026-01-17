# Router Diff

## Purpose

Return a git diff with configurable noise filtering and detail level.

## When to use

- Quick change inventory: `--detail 0` or `--detail 1` to see what changed without reading patches.
- Focused review: `--include/--exclude` to narrow to relevant paths.
- Reduce noise: `--noise` to ignore whitespace-only churn.
- Context control: `--context 0` for minimal hunks when scanning for logic changes.

## Usage

```bash
router diff
router diff --noise
router diff --noise=standard
router diff --context 0
router diff --detail 0
router diff --files-only
router diff --super-compact
router diff --name-status
router diff --stat
router diff --summary
router diff --compact
router diff --compact=context=1,keep-headers
router diff --compact=short-diff-header,short-hunk-header
router diff --compact=tokens
router diff --include src/** --exclude docs/**
router diff --ops added,modified,deleted
```

## Flags

- `--noise` / `--noise=<level>`: noise filter level (default: config).
- `--context N`: unified context lines (detail >= 2).
- `--detail 0..3`: 0=name-only, 1=name-status, 2=patch, 3=patch+stat.
- `--summary`: shortstat-only output (token-light summary).
- `--files-only`: alias for detail 0.
- `--super-compact`: alias for files-only (names only).
- `--name-status`: alias for detail 1.
- `--stat`: stat-only output (no patch).
- `--compact[=SPEC]`: compact unified diff (defaults: U0 + drop headers + no-prefix + shared path prefix shortening).
  - `context=N` or `uN`: set hunk context lines.
  - `keep-headers` / `drop-headers`: keep/remove `index/---/+++` lines.
  - `keep-prefix` / `no-prefix`: keep/remove `a/` + `b/` prefixes.
  - `drop-diff-header` / `short-diff-header`: drop or shorten `diff --git` lines.
  - `drop-hunk-header` / `short-hunk-header`: drop or shorten `@@ ... @@` lines.
  - `drop-filemode`: drop `new file mode` / `deleted file mode`.
  - `drop-rename`: drop rename/copy metadata lines.
  - `drop-similarity`: drop similarity/dissimilarity lines.
  - `drop-binary`: drop `Binary files ...` / `GIT binary patch` lines.
  - `path-strip=PREFIX`: remove a leading path prefix when shortening headers.
  - `path-basename`: shorten file paths to basename when shortening headers.
  - `path-table`: emit a file table and replace file headers with ids.
  - `path-common-prefix`: replace shared leading path with `.../` (configurable).
  - `no-common-prefix`: disable shared prefix shortening.
  - `path-prefix-token=...`: set the prefix token used for common prefix shortening.
  - `hunk-new-only`: show only the new start line in short hunk headers (default true).
  - `hunk-full`: show old+new start/len in short hunk headers.
  - `prefix-first`: only show `+`/`-` on the first line of a run.
  - `prefix-full`: keep `+`/`-` on every line (default).
  - `profile=<name>` or `<name>`: apply a compact profile from config (ex: `tokens`).
- `--include PATTERN[,PATTERN...]`: include pathspecs (comma-delimited, repeatable).
- `--exclude PATTERN[,PATTERN...]`: exclude pathspecs (comma-delimited, repeatable).
- `--ops LIST`: diff-filter ops (added, modified, deleted, renamed, copied,
  typechange, unmerged, unknown, broken) to focus on specific change types.
- `--auto-tune` / `--no-auto-tune`: override compact auto-tune for this invocation.

## Config

- Default noise level: `router.diff_default_noise`
- Default detail: `router.diff_default_detail`
- Default context: `router.diff_default_context`
- Noise levels: `router.diff_noise_levels.*.flags`
- Default excludes: `router.diff_default_excludes`
- Enable/disable: `commands.diff.enabled`
- Compact defaults: `router.compact_defaults`
- Auto-tune compact: `router.compact_auto_tune`
