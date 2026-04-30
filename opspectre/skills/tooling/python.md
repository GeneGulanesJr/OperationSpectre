---
name: python
description: Python execution patterns - venv, pip, pytest, script execution.
---

# Python Playbook

## Common patterns

- Create venv:
  `opspectre shell "cd /workspace && python3 -m venv .venv"`

- Install deps:
  `opspectre shell "cd /workspace && .venv/bin/pip install -r requirements.txt"`

- Run script:
  `opspectre code python /workspace/script.py`

- Run tests:
  `opspectre shell "cd /workspace && .venv/bin/python -m pytest -v"`

- Install single package:
  `opspectre shell "cd /workspace && .venv/bin/pip install requests"`

## Critical correctness rules

- Always use venv, never system python
- Activate venv before pip install
- Use absolute paths in sandbox

## Failure recovery

- If pip fails, try `pip install --no-cache-dir`
- If import error, check venv is activated
- If pytest fails, run with `-s` for stdout
