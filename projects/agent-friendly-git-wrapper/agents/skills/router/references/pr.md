# router pr

PR helper commands (GitHub CLI required). These helpers provide concise status
summaries and template-driven PR creation/update flows.

## Status

- `router pr status [--repo owner/name]`
  - Prints: title, state, draft, review decision, checks summary, mergeability, labels, URL.
- `router pr merge-state [--repo owner/name]`
  - Prints: mergeable, merge-state status, checks summary, review decision.
- `router pr view --summary [--repo owner/name]`
  - Prints: title, labels, file count, checks summary.

## Workflow macros

- `router pr open-draft [--template NAME] [--title TITLE] [--base BR] [--head BR] [--fill] [--repo owner/name]`
  - Creates a draft PR using a template body.
- `router pr open+status [--template NAME] [--title TITLE] [--base BR] [--head BR] [--fill] [--repo owner/name]`
  - Creates a PR then prints the status summary.
- `router pr ready+merge-state [--repo owner/name]`
  - Marks PR ready, then prints merge-state summary.

## Templates

- `router pr create --template NAME [--title TITLE] [--base BR] [--head BR] [--fill] [--repo owner/name]`
  - Uses the template body to create a PR (non-draft by default).
- `router pr update --template NAME [--repo owner/name]`
  - Re-renders the template and preserves content inside the notes block.

Template settings live in `config/cli_router.yaml` under `pr_helpers`.
Notes block markers default to:

- `<!-- NOTES START -->`
- `<!-- NOTES END -->`

Anything between these markers in the current PR body is retained on update.

