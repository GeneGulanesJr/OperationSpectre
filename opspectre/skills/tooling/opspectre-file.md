---
name: opspectre-file
description: How to use opspectre file commands for file operations.
---

# opspectre file Playbook

## Common patterns

- Read a file:
  `opspectre file read /workspace/app.py`

- Write a file:
  `opspectre file write /workspace/app.py "content here"`

- Find and replace:
  `opspectre file edit /workspace/app.py "old_func" "new_func"`

- List directory:
  `opspectre file list /workspace`

- Search file contents:
  `opspectre file search "TODO" /workspace`

## Critical correctness rules

- Always read a file before editing to understand context
- Use search to find the exact text before replacing
- Paths are relative to /workspace inside the container
- Write overwrites the entire file - use edit for partial changes

## Failure recovery

- If file not found, check path is correct with `opspectre file list`
- If edit fails (old_text not found), read the file first to get exact text
- For large files, read in sections
