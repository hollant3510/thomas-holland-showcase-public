# History Compaction Benchmark

## Table of Contents
- [Overview](#overview)
- [Tier tables (10/20/50/100 commits)](#tier-tables-102050100-commits)
- [Single-flag impact (patch-only baseline, 10 commits)](#single-flag-impact-patch-only-baseline-10-commits)
- [Commit-meta impact (10 commits)](#commit-meta-impact-10-commits)
- [Cumulative build-up to token_opt (patch-only baseline, 10 commits)](#cumulative-build-up-to-token_opt-patch-only-baseline-10-commits)
- [Reordered cumulative (greedy monotonic, vs unified 10 commits)](#reordered-cumulative-greedy-monotonic-vs-unified-10-commits)

## Overview
This benchmark captures how different history output tiers trade context size for agent utility. It provides reproducible hashes for the last 10/20/50/100 commits and documents how the compact tiers reduce tokens so agents can iterate efficiently without losing essential signal.

Codex repo: `https://github.com/openai/codex`

**Reproducibility:** ranges list the oldest commit of the last N (start) and the current HEAD (end). The N commits are inclusive of both ends.

For usage guidance, see the companion guide: `documentation/guides/history_compaction_guide.md`.

**Note on variability:** savings depend heavily on commit content and structure. Repos with smaller commits or diffs dominated by patch bodies (vs headers/metadata) will see lower percentage savings from token-opt flags. File-type filtering (for example excluding docs or lockfiles) can materially reduce output, but it is workload-specific and not reflected in the benchmark tables.

**Config sensitivity:** these measurements reflect the config defaults and compact profiles at the time
they were generated. If you change `router.compact_defaults`, `router.compact_profiles`, or the
auto-tune candidates, rerun the benchmark to refresh the tables.

## Tier tables (10/20/50/100 commits)

### Codex last 10 commits
range: `4c673086bc5b4b04ac859d3ec06632cb0ce70724 .. 31d9b6f4d2033438d3375d4c3fbadcd5c08660d9`

```text
variant | chars | tokens | chars saved vs unified | tokens saved vs unified
unified | 437,433 | 104,603 | 0.00% | 0.00%
compact_u0 | 378,965 | 88,849 | 13.37% | 15.06%
token_opt | 361,697 | 82,249 | 17.31% | 21.37%
super_compact | 2,694 | 963 | 99.38% | 99.08%
```

### Codex last 20 commits
range: `2651980bdf803ec3dd7d7540648de286e4de2ec2 .. 31d9b6f4d2033438d3375d4c3fbadcd5c08660d9`

```text
variant | chars | tokens | chars saved vs unified | tokens saved vs unified
unified | 626,913 | 151,764 | 0.00% | 0.00%
compact_u0 | 507,026 | 121,730 | 19.12% | 19.79%
token_opt | 472,275 | 108,656 | 24.67% | 28.40%
super_compact | 5,688 | 2,051 | 99.09% | 98.65%
```

### Codex last 50 commits
range: `898e5f82f08d0cba3ee8719c1e4ba83b38a38f60 .. 31d9b6f4d2033438d3375d4c3fbadcd5c08660d9`

```text
variant | chars | tokens | chars saved vs unified | tokens saved vs unified
unified | 1,406,645 | 345,339 | 0.00% | 0.00%
compact_u0 | 1,071,542 | 261,039 | 23.82% | 24.41%
token_opt | 962,799 | 220,585 | 31.55% | 36.13%
super_compact | 18,452 | 6,444 | 98.69% | 98.13%
```

### Codex last 100 commits
range: `5bc3e325a6cee50f12632ebb94f2cc8f27b3ffe2 .. 31d9b6f4d2033438d3375d4c3fbadcd5c08660d9`

```text
variant | chars | tokens | chars saved vs unified | tokens saved vs unified
unified | 3,155,217 | 836,503 | 0.00% | 0.00%
compact_u0 | 2,546,591 | 683,501 | 19.29% | 18.29%
token_opt | 2,321,599 | 604,179 | 26.42% | 27.77%
super_compact | 38,385 | 13,126 | 98.78% | 98.43%
```

## Single-flag impact (patch-only baseline, 10 commits)
Baseline here is patch-only output with commit metadata removed (`--commit-meta none`) to isolate diff formatting changes.
```text
variant | chars | tokens | chars saved vs unified | tokens saved vs unified
unified_patch_only | 437,959 | 104,565 | 0.00% | 0.00%
prefix_first_only | 435,410 | 102,035 | 0.58% | 2.42%
short_diff_header | 435,382 | 103,676 | 0.59% | 0.85%
short_hunk_header | 432,036 | 103,402 | 1.35% | 1.11%
hunk_new_only (+short_hunk_header) | 430,517 | 102,291 | 1.70% | 2.17%
path_table | 435,499 | 103,940 | 0.56% | 0.60%
path_common_prefix (+path_table) | 435,499 | 103,940 | 0.56% | 0.60%
no_prefix | 437,527 | 104,140 | 0.10% | 0.41%
drop_headers | 432,107 | 102,227 | 1.34% | 2.24%
drop_filemode | 437,875 | 104,537 | 0.02% | 0.03%
drop_similarity | 437,959 | 104,565 | 0.00% | 0.00%
drop_rename | 437,959 | 104,565 | 0.00% | 0.00%
drop_binary | 437,959 | 104,565 | 0.00% | 0.00%
context=0 | 385,575 | 91,276 | 11.96% | 12.71%
diff_default_noise:max | 437,294 | 104,366 | 0.15% | 0.19%
```

## Commit-meta impact (10 commits)
This shows the impact of stripping commit metadata only.
```text
variant | chars | tokens | chars saved vs unified | tokens saved vs unified
commit_meta_short | 438,808 | 104,918 | 0.00% | 0.00%
commit_meta_none | 437,959 | 104,565 | 0.19% | 0.34%
```

## Cumulative build-up to token_opt (patch-only baseline, 10 commits)
Each step adds the next compact flag to the previous step (and enables noise filtering at its step).
```text
step | added | compact_spec | noise | chars | tokens | chars saved vs unified | tokens saved vs unified
0 | baseline | (none) | no | 437,959 | 104,565 | 0.00% | 0.00%
1 | prefix_first_only | prefix-first | no | 435,410 | 102,035 | 0.58% | 2.42%
2 | short_diff_header | prefix-first,short-diff-header | no | 432,833 | 101,146 | 1.17% | 3.27%
3 | short_hunk_header | prefix-first,short-diff-header,short-hunk-header | no | 426,910 | 99,983 | 2.52% | 4.38%
4 | hunk_new_only | prefix-first,short-diff-header,short-hunk-header,hunk-new-only | no | 425,391 | 98,872 | 2.87% | 5.44%
5 | path_table | prefix-first,short-diff-header,short-hunk-header,hunk-new-only,path-table | no | 425,508 | 99,136 | 2.84% | 5.19%
6 | path_common_prefix | prefix-first,short-diff-header,short-hunk-header,hunk-new-only,path-table,path-common-prefix | no | 425,508 | 99,136 | 2.84% | 5.19%
7 | no_prefix | prefix-first,short-diff-header,short-hunk-header,hunk-new-only,path-table,path-common-prefix,no-prefix | no | 425,296 | 98,927 | 2.89% | 5.39%
8 | drop_headers | prefix-first,short-diff-header,short-hunk-header,hunk-new-only,path-table,path-common-prefix,no-prefix,drop-headers | no | 419,656 | 96,798 | 4.18% | 7.43%
9 | drop_filemode | prefix-first,short-diff-header,short-hunk-header,hunk-new-only,path-table,path-common-prefix,no-prefix,drop-headers,drop-filemode | no | 419,572 | 96,770 | 4.20% | 7.45%
10 | drop_similarity | prefix-first,short-diff-header,short-hunk-header,hunk-new-only,path-table,path-common-prefix,no-prefix,drop-headers,drop-filemode,drop-similarity | no | 419,572 | 96,770 | 4.20% | 7.45%
11 | drop_rename | prefix-first,short-diff-header,short-hunk-header,hunk-new-only,path-table,path-common-prefix,no-prefix,drop-headers,drop-filemode,drop-similarity,drop-rename | no | 419,572 | 96,770 | 4.20% | 7.45%
12 | drop_binary | prefix-first,short-diff-header,short-hunk-header,hunk-new-only,path-table,path-common-prefix,no-prefix,drop-headers,drop-filemode,drop-similarity,drop-rename,drop-binary | no | 419,572 | 96,770 | 4.20% | 7.45%
13 | context=0 | prefix-first,short-diff-header,short-hunk-header,hunk-new-only,path-table,path-common-prefix,no-prefix,drop-headers,drop-filemode,drop-similarity,drop-rename,drop-binary,context=0 | no | 363,729 | 82,841 | 16.95% | 20.78%
14 | diff_default_noise:max | prefix-first,short-diff-header,short-hunk-header,hunk-new-only,path-table,path-common-prefix,no-prefix,drop-headers,drop-filemode,drop-similarity,drop-rename,drop-binary,context=0 | yes | 362,324 | 82,628 | 17.27% | 20.98%
```

## Reordered cumulative (greedy monotonic, vs unified 10 commits)
This order is chosen to keep every step strictly decreasing while maximizing token savings. Savings shown are vs the unified 10-commit baseline.
```text
step | added | chars | tokens | chars saved vs unified | tokens saved vs unified
1 | context=0 | 385,575 | 91,276 | 13.30% | 14.31%
2 | prefix-first | 383,026 | 88,746 | 13.87% | 16.69%
3 | drop-headers | 377,174 | 86,408 | 15.19% | 18.88%
4 | short-hunk-header | 368,421 | 85,141 | 17.16% | 20.07%
5 | hunk-new-only | 366,273 | 83,494 | 17.64% | 21.62%
6 | short-diff-header | 363,696 | 82,605 | 18.22% | 22.45%
7 | noise=max | 362,291 | 82,392 | 18.53% | 22.65%
8 | drop-filemode | 362,207 | 82,364 | 18.55% | 22.68%
```

Skipped (no additional improvement while keeping monotonic decreases):
`path-table`, `path-common-prefix`, `no-prefix`, `drop-similarity`, `drop-rename`, `drop-binary`
