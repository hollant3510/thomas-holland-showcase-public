# router files

List impacted files for working tree changes, a commit, or a range.

## Usage

router files --changed | --commit SHA | --range A..B | --since-branch [NAME]
            [--stat | --name-status]

## Defaults

- Output is name-only unless `--stat` or `--name-status` is provided.
- `--since-branch` uses `router.default_base` when no branch name is given.

## Flags

- `--changed`: list files changed in the working tree vs HEAD.
- `--commit SHA`: list files from a specific commit.
- `--range A..B`: list files changed across a range.
- `--since-branch [NAME]`: list files since merge-base with branch.
- `--stat`: include stats per file.
- `--name-status`: include status codes (A/M/D/etc.).

## Examples

router files --changed
router files --commit HEAD
router files --range main..feature
router files --since-branch main
router files --since-branch --name-status
