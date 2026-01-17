# Project Architecture

This document describes the current project layout and the responsibilities of
each folder and key file.

## Root layout

- `app/`: router implementation and CLI entrypoint.
- `config/`: live router configuration files.
- `bin/`: git/gh shims that forward into the router.
- `router.sh`: shell entrypoint that runs the router.
- `documentation/`: usage guides, benchmarks, and architectural notes.
- `agents/`: project skills and reference material.
- `testing/`: test cases and automated tests.
- `requirements.txt`: Python dependencies for the project.
- `README.md`: project overview and quickstart.

## App layout (implementation)

```
app/
  main.py
  cli/
    router_cli.py
    cli_parse.py
  routing/
    routing.py
  policy/
    guardrails.py
  compact/
    compact.py
  config/
    config_loader.py
  utils/
    exec_utils.py
    log_utils.py
    runtime.py
  commands/
    state.py
    diff_cmd.py
    compare_cmd.py
    history_cmd.py
    log_cmd.py
    files_cmd.py
    branch_cmd.py
    base_cmd.py
    show_cmd.py
    scan_cmd.py
    pr_cmd.py
```

### Key files and responsibilities

- `app/main.py`: top-level CLI entrypoint; forwards into the router.
- `app/cli/router_cli.py`: router CLI orchestration (arg parsing, config load,
  handler dispatch, logging).
- `app/cli/cli_parse.py`: shared CLI parsing helpers for diff/log/history flags.
- `app/routing/routing.py`: tool selection and routing logic (git vs gh).
- `app/policy/guardrails.py`: safety checks (protected branches, safe mode,
  require-clean gating).
- `app/compact/compact.py`: compact diff transforms and auto-tune logic.
- `app/config/config_loader.py`: config loading + merge helpers.
- `app/utils/exec_utils.py`: process execution wrappers for git/gh.
- `app/utils/log_utils.py`: logging utilities and output capture helpers.
- `app/utils/runtime.py`: runtime context for timeouts and resolved command
  tracking.
- `app/commands/*`: command handlers for each router subcommand.

## Config files

- `config/cli_router.yaml`: main router configuration (defaults, profiles,
  guardrails, command registry).
- `config/cli_router_custom_commands.yaml`: macro command sequences.

## Shell entrypoints

- `router.sh`: runs `app/main.py` with the router command.
- `bin/git`, `bin/gh`: shims that forward to `router.sh` and emit a notice by
  default (suppressed by `ROUTER_QUIET=1`).
