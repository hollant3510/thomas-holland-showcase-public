# router scan

Repository scans for common issues.

## Subcommands

- `conflicts`: scan for merge conflict markers.

## Usage

router scan conflicts [--paths PATH[,PATH]]

## Flags

- `--paths`: comma-delimited paths to scan. Defaults to config paths or repo root.

## Config

- `guardrails.conflict_scan.paths`: default scan paths.
- `guardrails.conflict_scan.exclude_patterns`: glob patterns to ignore.

## Examples

router scan conflicts
router scan conflicts --paths src,docs
