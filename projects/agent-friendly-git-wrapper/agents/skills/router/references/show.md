# router show

Show commit metadata with optional patch/stat output.

## Usage

router show <sha> [--patch] [--stat] [--name-status] [--oneline] [--short-hash]

## Defaults

- Shows commit metadata only (no patch).
- Uses a fuller metadata format for clarity.

## Flags

- `--patch`: include the full patch.
- `--stat`: include file stats (no full patch unless combined).
- `--name-status`: include file status lines (A/M/D/etc.).
- `--oneline`: compact metadata format.
- `--short-hash`: alias for oneline with abbreviated commit hash.

## Examples

router show HEAD
router show HEAD --stat
router show HEAD --patch
router show HEAD --oneline
router show HEAD --short-hash
