# Testing

Case and test folders follow the same pattern as the rest of this repo:

- `testing/cases/`: fixtures and config samples
- `testing/tests/`: automated tests

## Test catalog

See `testing/test_catalog.md` for a list of automated tests, the case folders
they exercise, and what each case is meant to protect.

## Running tests

From the project root:

```bash
python -m pytest testing/tests -q
```

## Adding new cases

Add new cases under `testing/cases/<area>/case_name/`.
