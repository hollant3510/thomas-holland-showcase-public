---
name: agent-setup
description: Set up the agent-friendly git wrapper router (venv, PATH shims, config, verification). Use when installing or troubleshooting the router, git/gh shims, or CLI routing behavior for this project.
---

# Agent Setup

## Workflow

1) Open the setup guide: `documentation/setup.md`.
2) Follow the venv + requirements steps for this project.
3) Wire `bin` to PATH in the target shell (WSL preferred).
4) Verify routing with `type -a git` / `type -a gh` and
   `router.sh --check status`.
5) If you want a `router` shortcut, add an alias or symlink to `router.sh`.
6) Confirm config behavior in `config/cli_router.yaml` (override with `--config` if needed).

## References

- `documentation/setup.md`: venv setup, PATH wiring, and verification steps.
- `documentation/quickstart.md`: quick command list to confirm routing works.
- `documentation/testing.md`: optional test run after setup changes.
- `documentation/wrappers.md`: router entry points and shim behavior.
- `config/cli_router.yaml`: default profiles + routing settings.
- `config/cli_router_custom_commands.yaml`: custom command sequences.

