# Router State

## Purpose

Return a compact snapshot of repo + branch + worktree status.

## Usage

```bash
router state
router state --branch <name>
router state --base <name>
```

## Output fields

- `repo`: repo root path
- `branch`: target branch (current by default)
- `worktree_branch`: current branch if different from `--branch`
- `head`: short SHA
- `head_full`: full SHA
- `worktree`: `clean` or `dirty`
- `dirty_count`: number of dirty entries
- `base`: base branch used for ahead/behind (from config or `--base`)
- `behind` / `ahead`: counts vs base (if base resolvable)
- `upstream`: upstream ref if configured
- `ops`: in-progress ops (merge/rebase/cherry-pick/bisect/sequencer) or `none`

## Config

- Default base branch: `router.default_base` in `config/cli_router.yaml`
- Enable/disable: `commands.state.enabled`

