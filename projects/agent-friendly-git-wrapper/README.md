# Agent-Friendly Git Wrapper

This project is an agent-focused wrapper for git and GitHub CLI.

I started this after watching agents repeatedly run multiple git commands and
consume large, redundant outputs just to understand what changed. This wrapper
unifies both tools (including PR workflows) and standardizes the workflows we
want agents to follow (branching, PR creation, review). With the token-saving defaults in the config, agents should save at least ~10% on git command output (see [Benchmarks](#benchmarks)), by removing details I judged unlikely to affect their understanding.

It enables:

- Narrower-scoped output using **contextual knowledge from the current session**.
  Less context used up generally leads to more efficient agent performance (a
  common view in the LLM field), so the goal is to keep the window focused on
  what matters most. [1]
- Consistent command usage so agents don't improvise five variants.
- Guardrails that control what actions are allowed and how they are performed,
  so workflows stay consistent and safe.
- Profile-driven systems for single agents and multi-agent orchestrations, with
  custom profiles per agent to limit commands or work scope as needed.
- Compact profiles to trade context for speed when needed, with full detail
  available via flags when it actually matters.

Included in this project:

- **Router wrapper**: see [documentation/wrappers.md](documentation/wrappers.md) for git/gh routing,
  custom branch controls, token-optimization flags, and config options.
- **Agent skills** (ready to use):
  - [agents/skills/agent-setup/](agents/skills/agent-setup/) - setup and environment wiring.
  - [agents/skills/router/](agents/skills/router/) - how to use the router effectively.
- **Subcommand catalog**: see [documentation/subcommands.md](documentation/subcommands.md) for the list of
  commands, their flags, config options, and intended use.
- **Profiles, flags, and guardrails**: [documentation/configuration.md](documentation/configuration.md).
- **Benchmark guidance**: [documentation/benchmarks/history_compaction_benchmark.md](documentation/benchmarks/history_compaction_benchmark.md)
  and [documentation/guides/history_compaction_guide.md](documentation/guides/history_compaction_guide.md) show token savings
  even before an agent applies flexible filtering.

I also tested converting unified diffs into the TOON format. The conclusion:
unified diff is already very compact, so TOON didn't help. Instead, the gains
come from **output shaping** (noise filters, compact modes, and targeted views).

Depending on commit size and settings, savings range from ~10% to just under
40%, because we're trimming details the agent can recover on demand (via search
or targeted diffs) and filtering low-signal changes like docs/lockfiles when
they aren't relevant.



Under the hood this is **config- and flag-driven output shaping**: you pick a
profile, the router applies it consistently, and the agent can override upward
when it needs more detail. Profiles let you define **custom roles** for
different agents (worker vs. orchestrator, docs vs. tests vs. code), including
what they can and cannot do and how much context they should see. For example:

- A worker agent can be blocked from merging to protected branches and forced
  to log actions, while an orchestrator can override.
- A documentation-focused agent can default to filtering out code paths, and a
  backend-focused agent can exclude docs and front-end assets.
- A test-focused agent can narrow history to `tests/` and `fixtures/` to avoid
  unrelated diffs.
- An orchestrator can scope a worker to a specific subpath for history/diff
  output, either as a hard block or a default that can be overridden. This
  applies to the git output the agent pulls as well (not just how it searches
  the local files).

If the agent already knows the problem is in a narrow area (a path, file type,
or subsystem), it can cut output further with `--include` and `--exclude`
rather than rerunning verbose commands. The point is to give vetted, repeatable
levers so the agent tightens context based on what it already knows, without
writing ad-hoc command sequences that might be wrong or inconsistent.

## Table of Contents
- [Project Layout](#project-layout)
- [How agents use it (example flow)](#how-agents-use-it-example-flow)
- [Benchmarks](#benchmarks)
- [Documentation](#documentation)
- [Future ideas (this project or separate projects)](#future-ideas-this-project-or-separate-projects)
- [Project scope](#project-scope)
- [Future additions](#future-additions)
- [Support](#support)
- [Navigation guide](#navigation-guide)

## Project Layout

- `app/`: router implementation + CLI entrypoint.
- `config/`: live config files (router settings + custom commands).
- `bin/`: git/gh shims that forward into the router.
- `router.sh`: shell entrypoint at repo root.
- `documentation/`: docs, guides, benchmarks.
- `agents/`: project skills and references.
- `testing/`: test cases and tests.

## How agents use it (example flow)

A practical triage flow for an agent diagnosing an issue:

1) **Find touched files fast**
   - `router history --n 20 --files-only --no-patch`
2) **Zoom into relevant paths**
   - `router history --n 20 --include src/ --compact=tokens`
3) **Inspect a specific change**
   - `router show <sha> --patch` or `router diff --context 2`

This keeps initial context small, then expands only where the agent needs it.

## Benchmarks

The compaction experiments are documented here:

- `documentation/benchmarks/history_compaction_benchmark.md`
- `documentation/guides/history_compaction_guide.md`

Summary: with real repo history, compact profiles typically save **~10-40%**
tokens depending on commit size and patch makeup. Super-compact modes (file
names only) save far more, but remove most context and are intended for triage.

## Documentation

See these docs for setup and usage details:

- [documentation/quickstart.md](documentation/quickstart.md) (command list + examples)
- [documentation/subcommands.md](documentation/subcommands.md) (command catalog + flags)
- [documentation/setup.md](documentation/setup.md) (venv, PATH wiring, verification)
- [documentation/configuration.md](documentation/configuration.md) (profiles, guardrails, defaults)
- [documentation/testing.md](documentation/testing.md) (how to run tests + benchmark cases)

## Future ideas (this project or separate projects)

- **Search helpers** for locating code quickly after compact output
- **Path-focused macros** for narrow diagnostics (e.g., `--include src/`)
- **Role-based presets** for different agent roles (triage vs. deep debug)

## Project scope

This is a personal convenience tool that I cleaned up to share. I'm not
treating it as a full open-source project, so if you need changes, you'll
likely have the best experience forking and adapting it to your needs.

## Future additions

If this is helpful, keep an eye out for future helpers. I tend to explore
different setups and proof-of-concepts, so new tools will likely show up under
other project folders.

## Support
Since this is a personal project support isn’t expected but if you appreciate the project & would like to, you can show support via [Ko-fi](https://ko-fi.com/thomaspaulholland).

## Navigation guide

Start here:
- [documentation/quickstart.md](documentation/quickstart.md) - command list, examples, and when to use each.
- [documentation/subcommands.md](documentation/subcommands.md) - catalog of commands, flags, and intended use.
- [documentation/setup.md](documentation/setup.md) - venv setup, PATH wiring, and verification steps.

How it works:
- [documentation/architecture.md](documentation/architecture.md) - system layout and responsibilities.
- [documentation/configuration.md](documentation/configuration.md) - profiles, guardrails, defaults, and flags.

Performance and compaction:
- [documentation/benchmarks/history_compaction_benchmark.md](documentation/benchmarks/history_compaction_benchmark.md) - benchmark results and tables.
- [documentation/guides/history_compaction_guide.md](documentation/guides/history_compaction_guide.md) - how to use compaction flags in practice.

Testing:
- [documentation/testing.md](documentation/testing.md) - how to run tests and benchmark cases.

Config entry point:
- [config/cli_router.yaml](config/cli_router.yaml) - default profiles and routing settings.
