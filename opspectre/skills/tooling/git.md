---
name: git
description: Git workflows for sandboxed repos - clone, branch, commit patterns.
---

# Git Playbook

## Common patterns

- Clone into sandbox:
  `opspectre shell "cd /workspace && git clone <url> repo"`

- Create feature branch:
  `opspectre shell "cd /workspace/repo && git checkout -b feature/name"`

- Stage and commit:
  `opspectre shell "cd /workspace/repo && git add -A && git commit -m 'message'"`

- Check status:
  `opspectre shell "cd /workspace/repo && git status"`

- View diff:
  `opspectre shell "cd /workspace/repo && git diff"`

## Critical correctness rules

- Always cd into repo dir before git commands
- Use `--depth 1` for large repos to save time
- Set user.name and user.email in sandbox before committing

## Failure recovery

- If clone fails, check network with `opspectre shell "curl -I <url>"`
- If auth fails, check credentials or use token in URL
