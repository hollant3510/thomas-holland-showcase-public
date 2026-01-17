# Testing

This project uses pytest and case-based fixtures under `testing/cases/`.

## Run the full suite

```bash
python -m pytest testing/tests -q
```

## Run a single test file

```bash
python -m pytest testing/tests/test_router_history.py -q
```

## Benchmark cases

History compaction benchmarks are stored as snapshot cases:

- `testing/cases/benchmark_history_compaction/`
- Each case includes `input/commands.yaml`, `input/outputs/*.txt`,
  and `expected_output/tier_table.txt`.

The benchmark test computes token/character counts from the saved outputs and
compares them against the snapshot table. If you update outputs, regenerate the
expected table and re-run the tests.
