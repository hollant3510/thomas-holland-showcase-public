# router base

Resolve the merge-base between a target branch and a configured base branch.

## Usage

router base [--base NAME] [--branch NAME]

## Defaults

- `--branch` defaults to the current branch.
- `--base` defaults to `router.default_base`.

## Output

- `base`: base branch used for merge-base.
- `target`: target branch.
- `merge_base`: full SHA.
- `merge_base_short`: abbreviated SHA.

## Examples

router base
router base --base main
router base --base main --branch feature
