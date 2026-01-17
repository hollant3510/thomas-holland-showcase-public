# Logging

Router logging is optional and can be enabled per invocation or by config.

## Flags

- `--log`: log this invocation.
- `--log-all`: always log actions (useful for shims).
- `--log-file PATH`: log destination (defaults to `router.log`).
- `--log-format json|toon|txt`: log format (default: txt).

## Output fields

Each log entry includes:
- timestamp
- command + args
- resolved tool + resolved git/gh commands
- exit code
- truncated stdout/stderr
- profile name

## Config

`config/cli_router.yaml`:

- `router.log_all`
- `router.log_file`
- `router.log_format`
- `router.log_output_max`

