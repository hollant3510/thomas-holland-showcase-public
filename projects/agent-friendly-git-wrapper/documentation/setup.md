# Agent-Friendly Git Wrapper Setup

This guide covers the required setup for the agent-friendly git wrapper project,
including Python dependencies, router configuration, and shell wiring.

## Prerequisites

- Python 3.11+ (per repo standard)
- Git installed and available on PATH
- Optional: GitHub CLI (`gh`) if you want GH routing
- WSL is supported; Windows PowerShell is optional

## Python environment

From the repo root:

```bash
cd projects/agent-friendly-git-wrapper
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Note: `requirements.txt` includes `pytest` so tests run in this venv.

## Router wiring (WSL)

The wrapper works by placing `bin` first on PATH so `git` and `gh`
resolve to the shim scripts that call `router`.

### One-session PATH

```bash
export PATH="$PWD/bin:$PATH"
```

### Persistent PATH

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="/path/to/your/clone/projects/agent-friendly-git-wrapper/bin:$PATH"
```

Reload your shell or run `source ~/.bashrc`.

## Router configuration

- Default config: `config/cli_router.yaml`
- Custom commands file: `config/cli_router_custom_commands.yaml`
- Override config path when needed:

```bash
router --config /path/to/cli_router.yaml status
```

## Quick verification

Check the shim is first on PATH:

```bash
type -a git
type -a gh
```

Run a basic command through the router:

```bash
projects/agent-friendly-git-wrapper/router.sh status
projects/agent-friendly-git-wrapper/router.sh --check status
python projects/agent-friendly-git-wrapper/app/main.py router status
```

If you call `git` or `gh` directly, the shim prints a notice and forwards to
`router`. Set `ROUTER_QUIET=1` to suppress the notice.

If you want a `router` shortcut, add an alias or symlink to `router.sh`.

## Disabling the wrapper

To disable routing, remove the `bin` entry from PATH (or comment it
out in your shell profile), then start a new shell session.
