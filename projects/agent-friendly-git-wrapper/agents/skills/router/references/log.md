# Router Log

## Purpose

Return a one-line commit history for quick context before deeper review.

## When to use

- Quick "what changed" scan: `--n` + optional `--path`.
- Review a slice: `--range A..B` for comparisons.
- Trim hash length for compact displays: `--short-hash`.

## Usage

```bash
router log --n 10
router log --n 5 --short-hash
router log --since main
router log --range main..HEAD
router log --path src/app.py --n 10
```

## Flags

- `--n N`: max commits.
- `--since REF`: show commits after REF (uses `REF..HEAD`).
- `--range A..B`: explicit range (mutually exclusive with `--since`).
- `--path PATH`: restrict log to a path.
- `--short-hash`: use abbreviated commit hash in output.
