# OPERATIONSPECTRE - Project Plan

## What It Is
OPERATIONSPECTRE is a **CLI toolbox** that provides a clean interface to run
commands, edit files, browse the web, and execute code inside a Docker sandbox.

It has no LLM calls, no agent loop, no decision-making. It's just tools — you
call it, it runs the thing, returns the output.

## Dual Architecture Mode

### CLI Mode (Traditional)
```
User: needs to run nmap in a sandbox
User: runs `opspectre shell "nmap -sV target.com"`
OPSPECTRE: executes in Docker container, returns output
User: parses and presents results
```

### MCP Mode (AI Agents)
```
AI Agent: needs to run reconnaissance
AI Agent: calls nmap_scan(target="target.com")
MCP Server: executes CLI command in Docker container
AI Agent: receives structured JSON response
```

## Architecture

```
┌─────────────────────────────┐
│       CLI (user input)      │
│  opspectre <command> <args> │
└──────────┬──────────────────┘
           │
┌──────────▼──────────────────┐
│     Command Router          │
│  shell / file / code /      │
│  browser / sandbox          │
└──────────┬──────────────────┘
           │
┌──────────▼──────────────────┐
│     Docker Sandbox          │
│  (tool-rich container)      │
│  nmap, python, node, git,   │
│  curl, playwright, etc.     │
└─────────────────────────────┘
```

## CLI Commands

```bash
# Sandbox lifecycle
opspectre sandbox start              # Start Docker container
opspectre sandbox stop               # Stop and remove container
opspectre sandbox status             # Check if running

# Shell commands
opspectre shell <command>            # Run shell command in sandbox
opspectre run <command>              # Run command (auto-starts sandbox if needed, auto-cleanup after)

# File operations
opspectre file read <path>                    # Read file contents
opspectre file write <path> <content>         # Write to file
opspectre file edit <path> <old> <new>        # Find and replace in file
opspectre file list <dir>                     # List directory contents (default: /workspace)
opspectre file search <pattern> [path]        # Search file contents (ripgrep)

# Code execution
opspectre code python <file>          # Run Python script in sandbox
opspectre code node <file>            # Run Node.js script in sandbox

# Browser automation (playwright)
opspectre browser navigate <url>      # Open URL
opspectre browser snapshot            # Get page accessibility tree (placeholder)
opspectre browser screenshot          # Take screenshot (placeholder)

# Run history
opspectre runs list                   # List all previous runs
opspectre runs show <run-name>        # Show summary of a run

# Config
opspectre config set <key> <value>    # Set a config value
opspectre config get <key>            # Get a config value
opspectre init                        # Full setup: check Docker, pull image, start sandbox
```

## Directory Structure

```
OperationSpectre/
├── .gitignore
├── .pre-commit-config.yaml
├── LICENSE
├── Makefile
├── README.md
├── PLAN.md
├── QUICK_START.md
├── pyproject.toml
├── uv.lock
├── BURP_SUITE_VERIFICATION.md       # Burp Suite agent verification guide
├── CONTAINER_PLAYBOOKS.md           # Container playbook documentation
├── FULL_ARSENAL_README.md           # Full arsenal overview
├── opspectre-tools.md               # Available sandbox tools documentation
├── opspectre/
│   ├── __init__.py
│   ├── main.py                      # CLI entry point (argparse)
│   ├── config.py                    # Config save/load (~/.opspectre/cli-config.json)
│   ├── sandbox/
│   │   ├── __init__.py
│   │   ├── docker_runtime.py        # Docker container management
│   │   └── tool_server.py           # In-container FastAPI tool server
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── shell.py                 # Shell command execution
│   │   ├── file.py                  # File read/write/edit/search
│   │   ├── code.py                  # Python/Node code execution
│   │   ├── browser.py               # Playwright browser automation
│   │   └── sandbox.py               # Sandbox lifecycle
│   ├── reporting/
│   │   ├── __init__.py
│   │   └── run_manager.py           # List/show run directories
│   └── skills/
│       ├── __init__.py
│       └── tooling/                 # Per-tool usage playbooks
│           ├── opspectre-shell.md
│           ├── opspectre-file.md
│           ├── git.md
│           └── python.md
├── containers/
│   ├── Dockerfile                   # Full Kali Linux with all tools
│   ├── docker-compose.yml
│   ├── docker-entrypoint.sh
│   ├── burpsuite-agent.sh           # Burp Suite agent launcher
│   ├── burpsuite-playbook.sh        # Burp Suite playbook runner
│   ├── burpsuite-wrapper.sh         # Burp Suite wrapper script
│   ├── scan-helpers.sh              # Scan utility functions
│   ├── owasp-top10-playbook.sh      # OWASP Top 10 playbook runner
│   ├── msf-database.yml             # Metasploit database config
│   ├── data/
│   │   └── shared/                  # Shared data between containers
│   └── wrappers/                    # Per-tool wrapper scripts
│       ├── aircrack-run
│       ├── cme-run
│       ├── evil-winrm-run
│       ├── hashcat-run
│       ├── hydra-run
│       ├── john-run
│       ├── msf-run
│       └── responder-run
├── output/                          # Output directories for tool results
│   ├── exploits/
│   ├── logs/
│   ├── loot/
│   ├── reports/
│   ├── scans/
│   └── sessions/
├── scripts/
│   ├── start-opspectre.sh
│   └── test-full-arsenal.sh
└── tests/
    ├── __init__.py
    ├── test_config.py
    └── test_commands/
        └── __init__.py
```

## pyproject.toml (Dependencies)

```toml
[project]
name = "opspectre"
version = "0.1.0"
description = "CLI toolbox for sandboxed tool execution"
requires-python = ">=3.12"
dependencies = [
  "docker>=7.1.0",
  "rich",
  "requests>=2.32.0",
  "pydantic>=2.11.3",
  "httpx>=0.28.0",
]

[project.optional-dependencies]
sandbox = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.34.0",
  "python-multipart>=0.0.20",
  "playwright>=1.40.0",
]

[project.scripts]
opspectre = "opspectre.main:main"
```

## Environment Variables

```bash
OPSPECTRE_IMAGE="opspectre-full:latest"  # Docker image name
OPSPECTRE_TIMEOUT="120"                   # Command timeout (seconds)
OPSPECTRE_OUTPUT_LIMIT="1048576"          # Max output size in bytes (1MB default)
```

## Config System

Config is saved to `~/.opspectre/cli-config.json`.

```json
{
  "env": {
    "OPSPECTRE_IMAGE": "opspectre-full:latest",
    "OPSPECTRE_TIMEOUT": "120"
  }
}
```

Config is loaded on startup. CLI flags override env vars, which override config file.
`opspectre config set KEY VALUE` and `opspectre config get KEY` for management.

## Tool Server (In-Container)

FastAPI server running inside the Docker container.

- **Auth**: Bearer token generated per container start (random 32-char token)
- **Port**: Random available port on host, mapped to fixed port in container
- **Endpoints**:
  - `POST /execute` - Run shell command, return stdout/stderr/exit_code
  - `POST /file/read` - Read file from container
  - `POST /file/write` - Write file to container
  - `POST /file/edit` - Find and replace in file
  - `GET /health` - Health check
- **Timeout**: Per-request timeout (default 120s, configurable)
- **Output limit**: Responses truncated if over limit (default 1MB)

## Workspace

Inside the container, all work happens in `/workspace`:
- Cloned repos go to `/workspace/repo`
- Created files go to `/workspace/`
- Artifacts are copied from `/workspace/` to `opspectre_runs/<run>/artifacts/`

CLI commands use `/workspace` as the default working directory.

## Error Handling

- **Docker not installed**: Check on `opspectre sandbox start`, print helpful error
- **Docker not running**: Check connection, print error with instructions
- **Container crashes**: Detect on next command, offer to restart
- **Command timeout**: Kill process, return partial output + timeout error
- **Command cancellation**: Ctrl+C sends SIGTERM to container process
- **Output overflow**: Truncate output, add "... (truncated, N bytes)" suffix
- **Port conflict**: Retry with different random port
- **No sandbox running**: Auto-start sandbox on first command if not running

## Concurrency

- One sandbox container per run (named `opspectre-<run-id>`)
- Multiple opspectre instances can run simultaneously (different containers)
- Each gets its own random port and token
- Container named uniquely to avoid conflicts

## Sandbox Container

Two Dockerfiles are provided:

- **Dockerfile** - Full Kali Linux with all security tools (~15GB)

The point is: every tool should be available. Whether it's nmap for checking if a
service is running, python for scripting, nuclei for scanning, or playwright for
browser automation — everything should be there.

See [opspectre-tools.md](opspectre-tools.md) for the full tool list.

## Reporting

Run history is tracked in `opspectre_runs/` directories. Each run directory
can contain a `summary.json` and `artifacts/` subdirectory.

> **Note**: Full per-command logging (`commands.jsonl`) and automatic summary
generation are planned but not yet implemented. Currently, run directories are
created externally and `opspectre runs list/show` reads their summaries.

### Planned Run Directory Structure

```
opspectre_runs/<run-name>_<timestamp>/
├── commands.jsonl              # Every command executed + output + exit code
├── artifacts/                  # Files created during the run
└── summary.json                # Final summary when run completes
```

### Planned summary.json Format

```json
{
  "run_name": "build-api-20260409",
  "status": "completed",
  "started_at": "...",
  "finished_at": "...",
  "duration_seconds": 300,
  "commands_run": 15,
  "commands_succeeded": 13,
  "commands_failed": 2,
  "artifacts": ["app.py", "test_results.txt"],
  "errors": []
}
```

### Available CLI Commands

```bash
opspectre runs list                   # List all previous runs
opspectre runs show <run-name>        # Show summary of a run
```

## Implementation Phases

### Phase 1: Scaffold ✅
- [x] Set up project structure (folders, config files, Makefile)
- [x] Set up pyproject.toml with minimal deps
- [x] Create .gitignore
- [x] Create .pre-commit-config.yaml (ruff, mypy, bandit)
- [x] Create LICENSE (Apache-2.0)

### Phase 2: Docker Sandbox ✅
- [x] Create Dockerfiles (standard + full Kali image)
- [x] Create docker-entrypoint.sh
- [x] Implement docker_runtime.py (container start/stop/status, port finding, token auth)
- [x] Implement tool_server.py (FastAPI endpoints: /execute, /file/*, /health)
- [x] Implement config.py (save/load ~/.opspectre/cli-config.json)

### Phase 3: CLI Commands + Reporting ✅
- [x] main.py - Argparse with subcommands (sandbox, shell, file, code, browser, runs, config)
- [x] sandbox.py - start/stop/status
- [x] shell.py - Run shell commands, capture stdout/stderr, handle timeouts
- [x] file.py - read/write/edit/list/search
- [x] code.py - Python/Node execution
- [x] browser.py - Playwright navigate (snapshot/screenshot are placeholders)
- [x] run_manager.py - List/show run directories

### Phase 4: Tooling Playbooks 🔄
- [x] Create playbook format (Markdown with sections)
- [x] Write CLI command playbooks (opspectre-shell, opspectre-file)
- [x] Write sandbox tool playbooks (git, python)
- [ ] Write additional tool playbooks (curl, playwright, ripgrep, node)

### Phase 5: Polish & Tests 🔄
- [x] Error handling and timeouts
- [x] README with usage examples
- [ ] Tests
- [ ] Wire up reporting (command logging, summary generation) to CLI commands

## Playbook Categories

Four types of playbooks, each covering a different layer:

### 1. Tooling (how to use a specific tool)
```
skills/tooling/python.md           - venv, pip, pytest, script execution
skills/tooling/git.md              - clone, branch, commit, push patterns
skills/tooling/opspectre-shell.md  - shell command patterns
skills/tooling/opspectre-file.md   - file operation patterns
```

### 2. Frameworks (how to work with a specific framework)
- Planned: `skills/frameworks/` — fastapi, nextjs, express, django, flask

### 3. Tasks (how to approach a type of work)
- Planned: `skills/tasks/` — build-api, build-cli, code-review, debugging, data-analysis

### 4. Workflows (end-to-end multi-step recipes)
- Planned: `skills/workflows/` — clone-and-fix, scaffold-and-build, test-and-iterate

## Playbook Format

Each playbook is a markdown file with sections. Covers usage patterns for tools.

```yaml
---
name: python
description: Python execution patterns - venv setup, pip install, running scripts, pytest.
---

# Python Playbook

Common patterns:
- Create venv:
  `opspectre shell "python -m venv /workspace/.venv"`
- Install deps:
  `opspectre shell "/workspace/.venv/bin/pip install -r requirements.txt"`
- Run script:
  `opspectre code python /workspace/script.py`
- Run tests:
  `opspectre shell "cd /workspace && .venv/bin/python -m pytest -v"`

Critical correctness rules:
- Always use venv, never system python
- Activate venv before pip install
- Use absolute paths in sandbox

Failure recovery:
- If pip fails, try `pip install --no-cache-dir`
- If import error, check venv is activated
- If pytest fails, run with `-s` for stdout
```

Each playbook has:
- **Canonical syntax** - the basic command pattern
- **Common patterns** - copy-paste ready commands
- **Critical correctness rules** - what to always do / never do
- **Failure recovery** - what to try when things break

## Example Usage Flow

```bash
# Full setup (check Docker, pull image, start sandbox)
opspectre init

# Or just start the sandbox
opspectre sandbox start

# Run a command (auto-starts sandbox if needed, auto-cleanup after)
opspectre run "nmap -sV target.com"

# Run tests
opspectre shell "cd repo && python -m pytest"

# Fix a file
opspectre file edit repo/src/app.py "old_func" "new_func"

# Run the fixed code
opspectre code python repo/src/app.py

# Browse a web page
opspectre browser navigate "https://example.com"
opspectre browser snapshot

# Done
opspectre sandbox stop
```
