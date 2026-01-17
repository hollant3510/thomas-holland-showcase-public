# Router

This project routes git/gh commands through a configurable router so teams can
enforce policy, toggle tools, and define custom command sequences.

For full setup steps (venv, PATH wiring, verification), see
`projects/agent-friendly-git-wrapper/documentation/setup.md`.

## Entry points

```bash
projects/agent-friendly-git-wrapper/router.sh status
projects/agent-friendly-git-wrapper/router.sh --tool gh pr list
projects/agent-friendly-git-wrapper/router.sh state
projects/agent-friendly-git-wrapper/router.sh diff
projects/agent-friendly-git-wrapper/router.sh log --n 10
projects/agent-friendly-git-wrapper/router.sh history --n 10 --patch
projects/agent-friendly-git-wrapper/router.sh files --changed
projects/agent-friendly-git-wrapper/router.sh branch report-merged
projects/agent-friendly-git-wrapper/router.sh scan conflicts
projects/agent-friendly-git-wrapper/router.sh base
projects/agent-friendly-git-wrapper/router.sh compare main..feature
projects/agent-friendly-git-wrapper/router.sh show HEAD
projects/agent-friendly-git-wrapper/router.sh pr status
projects/agent-friendly-git-wrapper/router.sh pr merge-state
projects/agent-friendly-git-wrapper/router.sh pr view --summary
projects/agent-friendly-git-wrapper/router.sh pr open-draft
projects/agent-friendly-git-wrapper/router.sh pr open+status
projects/agent-friendly-git-wrapper/router.sh pr ready+merge-state
projects/agent-friendly-git-wrapper/router.sh pr create --template basic
projects/agent-friendly-git-wrapper/router.sh pr update --template basic
```

Python entrypoint:

```bash
python projects/agent-friendly-git-wrapper/app/main.py router status
```

## Configuration

Router behavior is controlled by:

```
projects/agent-friendly-git-wrapper/config/cli_router.yaml
```

Custom commands:

```
projects/agent-friendly-git-wrapper/config/cli_router_custom_commands.yaml
```

Key settings:
- `router.enable_git` / `router.enable_gh`: turn tools on or off.
- `router.overlap_default`: which tool wins for overlapping commands.
- `router.default_profile`: default profile name applied when `--profile` is not provided.
- `router.allow_prefixed`: allow `router git ...` / `router gh ...` prefixed calls.
- `command_overrides`: per-command allow/deny switches.
- `router.custom_commands_file`: file with custom command sequences.
- `router.unknown_command_policy`: error or passthrough on unknown commands (default: error).
- `router.diff_default_noise`: default diff noise level (max/standard/none).
- `router.diff_noise_levels`: map noise levels to git diff flags.
- `router.compact_defaults` / `router.compact_profiles`: compact diff defaults + profiles.
- `router.compact_auto_tune`: optional auto-tune that tries safe compact flags if they reduce size
  (uses tiktoken for `tokens` if installed, otherwise falls back to character counts).
- `commands`: builtin command registry (enable/disable builtins like `state`, `diff`, `log`, `files`, `branch`, `scan`, `base`, `compare`, `show`, `pr`).
- `branch_hygiene`: defaults + protections for branch helper commands.
- `guardrails`: safety gating, protected branches, safe mode, conflict scan defaults.
- `pr_helpers`: PR template + notes block settings for `router pr` helpers.
- `profiles`: profile-specific overrides (default/ci/safe).
- Example profile `compact_auto` enables the auto-tune compact rules for token savings.

Logging config:
- `router.log_all`, `router.log_file`, `router.log_format`, `router.log_output_max`.

## Guardrail flags

- `--override` / `--i-know-what-im-doing`: bypass guardrails for this invocation.
- `--require-clean`: enforce clean worktree check.
- `--safe` or `--profile safe`: block destructive ops (rebase/reset --hard/force push/etc.).

## Output shaping flags (token control)

Use these with `router diff` and `router compare` to shrink outputs:

- `--summary`: shortstat-only output (high-level summary).
- `--files-only`: alias for detail 0 (names only).
- `--super-compact`: names only (files).
- `--stat`: stat-only output (no patch).
- `--name-status`: status + filenames (A/M/D/etc.).
- `--detail 0..3`: detail selector (0=name-only, 1=name-status, 2=patch, 3=patch+stat).
- `--context N`: unified context lines (detail >= 2).
- `--compact[=SPEC]`: compact patch output (defaults: U0 + drop headers + no-prefix + shared path prefix
  shortening). Short hunk headers are off by default; if you enable them, new-only hunk headers are used
  unless you override with `hunk-full`.
  - Extra spec options: drop/shorten diff + hunk headers, drop rename/filemode/similarity/binary lines,
    path strip/basename, `prefix-first` for run-only +/- prefixes, or `profile=<name>` (ex: `tokens`).

Default excludes live in `config/cli_router.yaml` under
`router.diff_default_excludes` (docs, lockfiles, vendor, generated).

You can further scope output with `--include` / `--exclude` (comma-delimited, repeatable)
to filter file types or folders (for example, exclude `docs/**` or `**/*.md`).

## History flags (commit metadata)

Use these with `router history` to control commit header fields:

- `--commit-meta none|hash|subject|short|full`
- `--short-hash` (when hash is included)
- `--no-hash`, `--no-author`, `--no-date`, `--no-subject`

## Command surface

Grouped commands:

- `router state`
- `router diff` / `compare` / `files` / `log` / `show` / `base`
- `router history`
- `router branch <report-merged|cleanup-merged|audit-unmerged|sync-report|prune-local|validate-name>`
- `router scan conflicts`
- `router pr <status|merge-state|view|create|update|open-draft|open+status|ready+merge-state>`

Global flags (router CLI):

- `--config PATH`
- `--tool git|gh`
- `--profile NAME`
- `--safe`, `--require-clean`, `--override`
- `--log`, `--log-all`, `--log-file`, `--log-format`
- `--auto-tune`, `--no-auto-tune`
- `--check`

Command-specific flags are documented above and in `agents/skills/router/references`.

Unknown commands show the top 3 closest matches (ex: `did you mean state?`).

## Requirements

Install dependencies from:

```
projects/agent-friendly-git-wrapper/requirements.txt
```

## Optional shims

If you want to force all calls through the router, add these shims to your PATH:

- `projects/agent-friendly-git-wrapper/bin/git`
- `projects/agent-friendly-git-wrapper/bin/gh`

When invoked, the shims print a notice that routing is happening. To silence
the notice, set `ROUTER_QUIET=1` in your environment.

