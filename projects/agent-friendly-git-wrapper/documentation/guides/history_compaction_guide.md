# History Compaction Guide

## Table of Contents
- [Overview](#overview)
- [Profiles and when to use them](#profiles-and-when-to-use-them)
- [Flag reference (helpful vs harmful)](#flag-reference-helpful-vs-harmful)
- [Excluded from token_opt profile (by default)](#excluded-from-token_opt-profile-by-default)
- [Where to configure](#where-to-configure)

## Overview
This guide explains how to use the history compaction flags and profiles to reduce diff context while keeping enough signal for agents to work efficiently. For the measurement data that informed these defaults, see `documentation/benchmarks/history_compaction_benchmark.md`.

## Profiles and when to use them
- **unified**: raw `git log -p` output. Use only for deep debugging or patch reconstruction.
- **compact_u0**: unified diff with U0, no prefixes, headers removed, and shared path prefixes shortened.
  Good for a quick scan of actual edits.
- **token_opt**: compact defaults plus the `tokens` profile overrides (short headers + hunk short form + prefix-first). Best default for agents.
- **super_compact**: file names only. Best for triage and deciding what to open next.

All flags are configurable via CLI and `config/cli_router.yaml`; teams can add profiles or override settings per run.

**File-type filtering:** use `--include` / `--exclude` (or `diff_default_excludes` in config) to scope the diff to certain paths or extensions (e.g., exclude `docs/**` or `**/*.md`). This can significantly reduce output size, but the effect is workload-dependent.

## Flag reference (helpful vs harmful)
- `prefix_first_only`: trims repeated +/- prefixes; safe for agents, minimal risk.
- `short_diff_header` / `short_hunk_header`: compress headers; safe unless you need exact header syntax.
- `hunk_new_only`: drops old hunk range; fine for search-driven workflows.
- `path_table` / `path_common_prefix`: token savings with no semantic loss (varies by dataset).
- `no_prefix`: drops a/ and b/ path prefixes; safe.
- `drop_headers`: removes index/---/+++; harmless unless reconstructing patch metadata.
- `drop_filemode` / `drop_similarity` / `drop_rename` / `drop_binary`: removes file metadata; risky if you need rename/binary context.
- `context=0`: removes context lines; higher risk for understanding intent.
- `diff_default_noise:max`: ignores whitespace-only churn; risky if whitespace changes are semantically meaningful.
- `history_compact_meta_overrides.tokens: none`: removes commit identity; add back when debugging or tracing authorship.

Auto-tune note: `--auto-tune` (or profile `compact_auto`) will try optional compact flags in order and
keep the smallest output. If `metric: tokens` is set, the router uses tiktoken when installed and falls
back to character counts otherwise.

## Excluded from token_opt profile (by default)
These flags are not part of the `tokens` profile overrides and only apply if
you enable them explicitly (or via auto-tune). Defaults in
`router.compact_defaults` still apply.

- `path-table`: adds a file table; overhead can outweigh savings when patch bodies dominate.
- `drop-similarity`: no similarity lines in most diffs.
- `drop-rename`: no rename/copy lines in most diffs.
- `drop-binary`: no binary markers in most diffs.

## Where to configure
- CLI: `router history --compact` plus flags (see `router --help`).
- Config: `config/cli_router.yaml` (profiles, defaults, overrides).

