# Router Config

The router reads its config from:

- `config/cli_router.yaml`
- Custom command macros: `config/cli_router_custom_commands.yaml`

## Key sections

- `router.*` core switches (enable/disable tools, routing defaults, base branch)
- `router.enable_git` / `router.enable_gh`: toggle tool routing on/off.
- `router.allow_prefixed`: allow `router git ...` / `router gh ...` prefixes.
- `router.overlap_default`: tool used when commands overlap (git vs gh).
- `router.unknown_command_policy`: `error` or `passthrough`.
- `router.default_command_enabled`: default on/off for commands not listed in `commands`.
- `router.diff_default_noise`: default diff noise level
- `router.diff_default_detail`: default diff detail (0..3)
- `router.diff_default_context`: default diff context (optional)
- `router.history_default_commit_meta`: default commit meta mode for `router history`
- `router.history_default_patch`: default patch on/off for `router history`
- `router.history_compact_meta_overrides`: override commit meta defaults for compact presets (ex: `tokens: none`)
- `router.default_profile`: profile applied when `--profile` is not provided
- `router.diff_noise_levels`: map noise levels to git diff flags
- `router.diff_default_excludes`: default pathspec excludes for diff/compare
- `router.command_timeout`: optional timeout (seconds)
- `router.log_all`, `router.log_file`, `router.log_format`, `router.log_output_max`
- `router.compact_defaults`: defaults for compact diff output
- `router.compact_profiles`: named compact option bundles (ex: tokens)
  - `path_common_prefix`: when true, shortens shared path prefix to a token.
  - `path_prefix_token`: prefix marker used for common prefix replacement (default `...`).
  - `hunk_new_only`: when true, short hunk headers show only new start line.
  - `prefix_first_only`: when true, show `+`/`-` only on the first line of a run.
- `router.compact_auto_tune`: optional auto-tuning for compact output.
  - `enabled`: toggle auto-tune on/off.
  - `metric`: `tokens` (uses tiktoken if installed, else chars) or `chars`.
  - `encoding`: tiktoken encoding (ex: `cl100k_base`).
  - `candidates`: list of compact spec tokens to try in order.
- CLI overrides: `--auto-tune` / `--no-auto-tune` for per-command control.
- `router.custom_commands_file`: path to macro command file (see below).
- `commands.*` built-in command registry (enable/disable built-ins)
- `overlap_commands`, `git_only_commands`, `gh_only_commands`
- `command_overrides` (per-command allow/deny)
- `branch_hygiene` defaults for branch helpers (including name patterns)
- `guardrails` global safety gating (protected branches, safe mode, scans)
- `profiles` profile-specific overrides (ci/safe/default)
  - Example: `compact_auto` enables compact auto-tuning for token savings.
- `pr_helpers` template + notes block settings for `router pr`

## Built-in registry example

```yaml
commands:
  state:
    enabled: true
    handler: state
  diff:
    enabled: true
    handler: diff
  log:
    enabled: true
    handler: log
  files:
    enabled: true
    handler: files
  branch:
    enabled: true
    handler: branch
  scan:
    enabled: true
    handler: scan
  base:
    enabled: true
    handler: base
  compare:
    enabled: true
    handler: compare
  show:
    enabled: true
    handler: show
  pr:
    enabled: true
    handler: pr
```

## Custom macros

`cli_router_custom_commands.yaml` contains custom sequences that the router
can execute as a single command.

## Branch hygiene defaults

```yaml
branch_hygiene:
  default_base: develop
  default_remote: origin
  include_remotes: true
  fetch_before: true
  protected_branches:
    - main
    - develop
  protected_patterns: []
  ignore_patterns: []
  merge_policies:
    - target: main
      allowed_sources: [develop]
      enforce_cleanup: false
  cleanup:
    default_apply: false
    enforce_merge_policy: false
  prune:
    pattern: "codex-cli/*"
    default_apply: false
  name_patterns:
    - "cc/*/*/*"
```

## Guardrails defaults

```yaml
guardrails:
  protected_branches:
    - main
    - develop
  protected_ops:
    - commit
    - push
    - rebase
    - merge
    - cherry-pick
    - reset
    - branch
  require_clean_ops:
    - rebase
    - merge
    - cherry-pick
    - reset
    - branch
    - push
  enforce_branch_name_ops: []
  branch_name_patterns:
    - "cc/*/*/*"
  safe_block_ops:
    - rebase
    - "reset --hard"
    - "push --force"
    - "push --force-with-lease"
    - "push -f"
    - "branch -D"
  merge_policies:
    - target: main
      allowed_sources: [develop]
  conflict_scan:
    paths: []
    exclude_patterns:
      - ".git/*"
  safe_mode: false
```

## Profiles

Profiles overlay config sections (router/command_overrides/guardrails/etc.).
Select via `--profile NAME` or `router.default_profile`.

```yaml
profiles:
  default: {}
  ci:
    router:
      diff_default_noise: max
      diff_default_detail: 1
      command_timeout: 30
    command_overrides:
      git:
        push: false
        rebase: false
        reset: false
  safe:
    guardrails:
      safe_mode: true
    command_overrides:
      git:
        push: false
        rebase: false
        reset: false
```

## PR helper defaults

```yaml
pr_helpers:
  default_template: basic
  templates:
    basic: pr_templates/basic.md
  notes_block:
    start: "<!-- NOTES START -->"
    end: "<!-- NOTES END -->"
```

