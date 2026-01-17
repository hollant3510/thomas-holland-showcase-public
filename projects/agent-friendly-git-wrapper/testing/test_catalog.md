# Test Catalog

This catalog maps each automated test to the cases it exercises, what it is
verifying, and the kinds of regressions it is meant to catch.

## How tests are structured

- Test files live in `testing/tests/`.
- Case fixtures live in `testing/cases/<area>/case_name/`.
- Each case contains `input/` (commands/config/setup) and `expected_output/`
  (exit code and output checks).
- Tests run the router in a temporary repo, apply any case setup, then compare
  output to the expected fixtures. This catches changes in flag parsing, output
  shaping, guardrails, and routing behavior.

## Command test suites

### Router config + routing

Test file: [testing/tests/test_router_cli.py](testing/tests/test_router_cli.py)

Purpose:
- Validates config parsing, command routing, and allow/deny logic.

What it catches:
- Command routing regressions, config override mistakes, missing custom commands,
  or unexpected allow/deny outcomes.

Cases ([testing/cases/wrapper_router_config/](testing/cases/wrapper_router_config/)):
- [case_command_override_denied](testing/cases/wrapper_router_config/case_command_override_denied/) - denies a command when overrides are disabled.
- [case_custom_command](testing/cases/wrapper_router_config/case_custom_command/) - accepts a custom command from config.
- [case_default_check](testing/cases/wrapper_router_config/case_default_check/) - validates `--check` mode against config.
- [case_prefixed_disabled](testing/cases/wrapper_router_config/case_prefixed_disabled/) - blocks prefixed tool usage when disabled.
- [case_profile_ci_denies_push](testing/cases/wrapper_router_config/case_profile_ci_denies_push/) - CI profile denies push as expected.
- [case_tool_override_gh](testing/cases/wrapper_router_config/case_tool_override_gh/) - tool override routes to gh.
- [case_unknown_command](testing/cases/wrapper_router_config/case_unknown_command/) - unknown commands return a controlled error.

### router state

Test file: [testing/tests/test_router_state.py](testing/tests/test_router_state.py)

Purpose:
- Verifies state snapshot output for clean/dirty repos.

What it catches:
- Incorrect clean/dirty detection or missing fields in state output.

Cases ([testing/cases/wrapper_router_state/](testing/cases/wrapper_router_state/)):
- [case_clean](testing/cases/wrapper_router_state/case_clean/) - clean repo output.
- [case_dirty](testing/cases/wrapper_router_state/case_dirty/) - dirty repo output.

### router base

Test file: [testing/tests/test_router_base.py](testing/tests/test_router_base.py)

Purpose:
- Ensures merge-base logic uses default and override base branches correctly.

What it catches:
- Wrong base resolution or override logic bugs.

Cases ([testing/cases/wrapper_router_base/](testing/cases/wrapper_router_base/)):
- [case_default](testing/cases/wrapper_router_base/case_default/) - default base branch behavior.
- [case_override](testing/cases/wrapper_router_base/case_override/) - explicit base override behavior.

### router branch

Test file: [testing/tests/test_router_branch.py](testing/tests/test_router_branch.py)

Purpose:
- Verifies branch hygiene commands and output formatting.

What it catches:
- Incorrect branch filtering, prune/cleanup logic, or naming validation issues.

Cases ([testing/cases/wrapper_router_branch/](testing/cases/wrapper_router_branch/)):
- [case_report_merged](testing/cases/wrapper_router_branch/case_report_merged/) - merged branches report.
- [case_cleanup_merged](testing/cases/wrapper_router_branch/case_cleanup_merged/) - dry-run/apply cleanup output.
- [case_audit_unmerged](testing/cases/wrapper_router_branch/case_audit_unmerged/) - unmerged audit output.
- [case_prune_local](testing/cases/wrapper_router_branch/case_prune_local/) - pruning stale refs.
- [case_sync_report](testing/cases/wrapper_router_branch/case_sync_report/) - ahead/behind sync report.
- [case_validate_name](testing/cases/wrapper_router_branch/case_validate_name/) - branch naming enforcement.

### router diff

Test file: [testing/tests/test_router_diff.py](testing/tests/test_router_diff.py)

Purpose:
- Exercises diff output shaping, compact profiles, noise filters, and path filters.

What it catches:
- Regressions in compact output, include/exclude path logic, detail flags,
  and noise-level handling.

Cases ([testing/cases/wrapper_router_diff/](testing/cases/wrapper_router_diff/)):
- [case_compact_auto_tune](testing/cases/wrapper_router_diff/case_compact_auto_tune/) - auto-tune compact options.
- [case_compact_auto_tune_override](testing/cases/wrapper_router_diff/case_compact_auto_tune_override/) - manual override of auto-tune.
- [case_compact_common_prefix](testing/cases/wrapper_router_diff/case_compact_common_prefix/) - common prefix shortening.
- [case_compact_default](testing/cases/wrapper_router_diff/case_compact_default/) - default compact profile.
- [case_compact_hunk_new_only](testing/cases/wrapper_router_diff/case_compact_hunk_new_only/) - new-line-only hunk headers.
- [case_compact_path_table](testing/cases/wrapper_router_diff/case_compact_path_table/) - path table compression.
- [case_compact_prefix_first](testing/cases/wrapper_router_diff/case_compact_prefix_first/) - prefix-first-only behavior.
- [case_compact_requires_patch](testing/cases/wrapper_router_diff/case_compact_requires_patch/) - compact requires patch output.
- [case_compact_short_headers](testing/cases/wrapper_router_diff/case_compact_short_headers/) - short header formatting.
- [case_default_excludes](testing/cases/wrapper_router_diff/case_default_excludes/) - default exclude patterns.
- [case_default_noise](testing/cases/wrapper_router_diff/case_default_noise/) - default noise level.
- [case_detail_name_only](testing/cases/wrapper_router_diff/case_detail_name_only/) - detail=files behavior.
- [case_files_only](testing/cases/wrapper_router_diff/case_files_only/) - files-only behavior.
- [case_include_exclude](testing/cases/wrapper_router_diff/case_include_exclude/) - include/exclude paths.
- [case_name_status_flag](testing/cases/wrapper_router_diff/case_name_status_flag/) - name-status output.
- [case_noise_flag_default](testing/cases/wrapper_router_diff/case_noise_flag_default/) - noise flag default.
- [case_noise_none](testing/cases/wrapper_router_diff/case_noise_none/) - noise off.
- [case_ops_invalid](testing/cases/wrapper_router_diff/case_ops_invalid/) - invalid ops spec error handling.
- [case_stat_flag](testing/cases/wrapper_router_diff/case_stat_flag/) - stat output.
- [case_summary_flag](testing/cases/wrapper_router_diff/case_summary_flag/) - summary output.

### router compare

Test file: [testing/tests/test_router_compare.py](testing/tests/test_router_compare.py)

Purpose:
- Verifies compare output shares the same shaping controls as diff.

What it catches:
- Range compare parsing or output shaping regressions.

Cases ([testing/cases/wrapper_router_compare/](testing/cases/wrapper_router_compare/)):
- [case_default](testing/cases/wrapper_router_compare/case_default/) - default compare.
- [case_default_excludes](testing/cases/wrapper_router_compare/case_default_excludes/) - default excludes.
- [case_include_exclude](testing/cases/wrapper_router_compare/case_include_exclude/) - include/exclude paths.
- [case_name_only](testing/cases/wrapper_router_compare/case_name_only/) - name-only output.
- [case_summary_flag](testing/cases/wrapper_router_compare/case_summary_flag/) - summary output.
- [case_files_only_flag](testing/cases/wrapper_router_compare/case_files_only_flag/) - files-only output.
- [case_compact_default](testing/cases/wrapper_router_compare/case_compact_default/) - default compact profile.
- [case_compact_path_table](testing/cases/wrapper_router_compare/case_compact_path_table/) - path table compression.
- [case_compact_short_headers](testing/cases/wrapper_router_compare/case_compact_short_headers/) - short headers.
- [case_compact_requires_patch](testing/cases/wrapper_router_compare/case_compact_requires_patch/) - compact requires patch output.
- [case_noise_none](testing/cases/wrapper_router_compare/case_noise_none/) - noise off.
- [case_extra_arg](testing/cases/wrapper_router_compare/case_extra_arg/) - extra arg passthrough handling.

### router history

Test file: [testing/tests/test_router_history.py](testing/tests/test_router_history.py)

Purpose:
- Verifies history output shaping across commit ranges.

What it catches:
- History compact profile regressions or missing commit metadata controls.

Cases ([testing/cases/wrapper_router_history/](testing/cases/wrapper_router_history/)):
- [case_default_patch](testing/cases/wrapper_router_history/case_default_patch/) - default history patch output.
- [case_commit_meta_none](testing/cases/wrapper_router_history/case_commit_meta_none/) - commit metadata removed.
- [case_compact_tokens](testing/cases/wrapper_router_history/case_compact_tokens/) - token-optimized compact profile.
- [case_compact_requires_patch](testing/cases/wrapper_router_history/case_compact_requires_patch/) - compact requires patch output.

### router log

Test file: [testing/tests/test_router_log.py](testing/tests/test_router_log.py)

Purpose:
- Verifies log output for count, range, and path-scoped modes.

What it catches:
- Range parsing errors or short-hash formatting issues.

Cases ([testing/cases/wrapper_router_log/](testing/cases/wrapper_router_log/)):
- [case_n1](testing/cases/wrapper_router_log/case_n1/) - single commit output.
- [case_range](testing/cases/wrapper_router_log/case_range/) - commit range output.
- [case_path_short](testing/cases/wrapper_router_log/case_path_short/) - path-scoped output.

### router files

Test file: [testing/tests/test_router_files.py](testing/tests/test_router_files.py)

Purpose:
- Verifies file listing modes and conflicts between output flags.

What it catches:
- Wrong file list behavior or stat/name-status conflicts.

Cases ([testing/cases/wrapper_router_files/](testing/cases/wrapper_router_files/)):
- [case_changed](testing/cases/wrapper_router_files/case_changed/) - working tree changes.
- [case_commit](testing/cases/wrapper_router_files/case_commit/) - files from a commit.
- [case_range](testing/cases/wrapper_router_files/case_range/) - files from a range.
- [case_since_branch](testing/cases/wrapper_router_files/case_since_branch/) - files since branch.
- [case_stat_name_conflict](testing/cases/wrapper_router_files/case_stat_name_conflict/) - conflicting flags.

### router show

Test file: [testing/tests/test_router_show.py](testing/tests/test_router_show.py)

Purpose:
- Verifies show output modes (metadata, patch, stat, oneline).

What it catches:
- Wrong default output or invalid flag combinations.

Cases ([testing/cases/wrapper_router_show/](testing/cases/wrapper_router_show/)):
- [case_default](testing/cases/wrapper_router_show/case_default/) - default metadata.
- [case_oneline](testing/cases/wrapper_router_show/case_oneline/) - one-line output.
- [case_patch](testing/cases/wrapper_router_show/case_patch/) - patch output.
- [case_stat](testing/cases/wrapper_router_show/case_stat/) - stat output.
- [case_stat_name_conflict](testing/cases/wrapper_router_show/case_stat_name_conflict/) - conflicting flags.

### router scan

Test file: [testing/tests/test_router_scan.py](testing/tests/test_router_scan.py)

Purpose:
- Ensures conflict marker scanning finds expected markers.

What it catches:
- Missing matches or path-scoped scan issues.

Cases ([testing/cases/wrapper_router_scan/](testing/cases/wrapper_router_scan/)):
- [case_conflicts](testing/cases/wrapper_router_scan/case_conflicts/) - conflict marker detection.

### router guardrails

Test file: [testing/tests/test_router_guardrails.py](testing/tests/test_router_guardrails.py)

Purpose:
- Verifies guardrail enforcement and safe-mode behavior.

What it catches:
- Protected branch rules, require-clean enforcement, or safe-mode bypasses.

Cases ([testing/cases/wrapper_router_guardrails/](testing/cases/wrapper_router_guardrails/)):
- [case_protected_commit](testing/cases/wrapper_router_guardrails/case_protected_commit/) - protected branch guard.
- [case_require_clean](testing/cases/wrapper_router_guardrails/case_require_clean/) - clean worktree required.
- [case_safe_mode](testing/cases/wrapper_router_guardrails/case_safe_mode/) - safe mode blocks destructive ops.

### router pr (GitHub CLI)

Test file: [testing/tests/test_router_pr.py](testing/tests/test_router_pr.py)

Purpose:
- Verifies PR command routing and output shaping.

What it catches:
- PR command routing, template selection, or summary output changes.

Cases ([testing/cases/wrapper_router_pr/](testing/cases/wrapper_router_pr/)):
- [case_status](testing/cases/wrapper_router_pr/case_status/) - PR status summary.
- [case_merge_state](testing/cases/wrapper_router_pr/case_merge_state/) - mergeability output.
- [case_view_summary](testing/cases/wrapper_router_pr/case_view_summary/) - short PR summary.
- [case_create](testing/cases/wrapper_router_pr/case_create/) - PR creation output.
- [case_update](testing/cases/wrapper_router_pr/case_update/) - PR update output.

### Benchmark history compaction

Test file: [testing/tests/test_benchmark_history_compaction.py](testing/tests/test_benchmark_history_compaction.py)

Purpose:
- Validates benchmark table outputs remain stable.

What it catches:
- Changes in compaction profiles, tokenization settings, or output formatting
  that would invalidate stored benchmarks.

Cases ([testing/cases/benchmark_history_compaction/](testing/cases/benchmark_history_compaction/)):
- [case_codex_last_10](testing/cases/benchmark_history_compaction/case_codex_last_10/)
- [case_codex_last_20](testing/cases/benchmark_history_compaction/case_codex_last_20/)
- [case_codex_last_50](testing/cases/benchmark_history_compaction/case_codex_last_50/)
- [case_codex_last_100](testing/cases/benchmark_history_compaction/case_codex_last_100/)
