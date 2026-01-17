# router compare

Diff between two refs/branches using the same controls as `router diff`.

## Usage

router compare <base>..<head> [--noise[=LEVEL]] [--context N] [--detail 0..3]
                     [--summary|--files-only|--stat|--name-status] [--compact[=SPEC]]
                     [--include PATTERN] [--exclude PATTERN] [--ops LIST]

## Defaults

- Uses `router.diff_default_noise` for noise filtering.
- Detail defaults to patch output (detail 2).

## Flags

- `--noise` / `--noise=LEVEL`: apply noise filtering (max/standard/none by default).
- `--context N`: set unified context lines (detail 2/3 only).
- `--detail 0..3`:
  - 0: names only
  - 1: name + status
  - 2: patch
  - 3: patch + stat
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
- `--include` / `--exclude`: pathspec filters (comma-delimited, repeatable).
- `--ops`: diff filter (added/modified/deleted/renamed/copied/typechange/unmerged/broken/unknown).
- `--auto-tune` / `--no-auto-tune`: override compact auto-tune for this invocation.

## Config

- Default noise level: `router.diff_default_noise`
- Default detail: `router.diff_default_detail`
- Default context: `router.diff_default_context`
- Noise levels: `router.diff_noise_levels.*.flags`
- Default excludes: `router.diff_default_excludes`
- Compact defaults: `router.compact_defaults`
- Auto-tune compact: `router.compact_auto_tune`

## Examples

router compare main..feature
router compare main..feature --detail 0
router compare main..feature --files-only
router compare main..feature --super-compact
router compare main..feature --summary
router compare main..feature --compact
router compare main..feature --compact=short-diff-header,short-hunk-header
router compare main..feature --compact=tokens
router compare main..feature --noise standard --context 3
router compare main..feature --include src --exclude docs
router compare main..feature --ops added,modified
