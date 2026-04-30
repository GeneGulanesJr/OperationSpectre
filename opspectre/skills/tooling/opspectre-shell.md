---
name: opspectre-shell
description: How to use opspectre shell command effectively.
---

# opspectre shell Playbook

## Common patterns

- Run command:
  `opspectre shell "ls -la /workspace"`

- Run with timeout:
  `opspectre shell --timeout 60 "nmap -sV target.com"`

- Chain commands:
  `opspectre shell "cd /workspace/repo && python -m pytest -v"`

- Check exit code:
  Output includes exit code. Non-zero means failure.

## Critical correctness rules

- Always use absolute paths when possible
- Set timeout for long-running commands (nmap, nuclei, etc.)
- Chain commands with `&&` to stop on first failure
- Use `--json-output` for machine-parseable results

## Failure recovery

- If timeout, increase with `--timeout 300`
- If sandbox not running, run `opspectre sandbox start` first
- If command not found, tool may not be in PATH - use full path
