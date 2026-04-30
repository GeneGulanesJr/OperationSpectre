---
name: opspectre-dev
description: Helps develop and test the OperationSpectre CLI itself. Knows the project structure, runs tests with pytest, and manages the Docker build pipeline.
---

# OperationSpectre Development Helper

Assists with developing, testing, and debugging the OperationSpectre CLI toolbox. Knows the full project structure, two-stage Docker build, skill system, playbook architecture, and testing pipeline.

## Project Structure

```
OperationSpectre/
├── pyproject.toml          # Project config, dependencies (uv/pip)
├── Makefile                # Build tasks and shortcuts
├── README.md               # User documentation
├── PLAN.md                 # Architecture and roadmap
├── QUICK_START.md          # Getting started guide
├── LICENSE
├── uv.lock                 # Dependency lock file
├── src/opspectre/              # Main package source
│   ├── __init__.py
│   ├── cli/                # CLI command handlers
│   ├── core/               # Core sandbox/engine logic
│   ├── commands/           # Command implementations
│   └── ...
├── containers/             # Docker configuration
│   ├── Dockerfile.base     # Heavy Kali base (apt, wordlists, metasploit)
│   ├── Dockerfile          # App layer (playbooks, Go/Python/npm tools)
│   ├── docker-compose.yml  # Runtime config (DNS, volumes, ports)
│   ├── docker-entrypoint.sh # Runtime init (DNS fix, playbook loading)
│   ├── osint-playbook.sh   # Passive OSINT functions
│   ├── rate-limit-helpers.sh # Rate-limit & stealth helpers
│   ├── owasp-top10-playbook.sh # OWASP Top 10 scan pipeline
│   ├── burpsuite-playbook.sh   # Burp Suite headless agent
│   ├── scan-helpers.sh     # General scan utility functions
│   └── wrappers/           # Agent wrapper scripts
├── scripts/                # Utility scripts
│   ├── build.sh            # Docker build with caching
│   ├── start-opspectre.sh  # Startup helper
│   └── test-full-arsenal.sh # Full integration test
├── tests/                  # Test suite
│   └── ...
├── .pi/                    # Pi agent configuration
│   ├── settings.json       # Pi settings
│   └── skills/             # Agent skill definitions
│       ├── container-audit/SKILL.md
│       ├── docker-toolchain/SKILL.md
│       ├── exploit-dev/SKILL.md
│       ├── nmap-playbook/SKILL.md
│       ├── opspectre-dev/SKILL.md
│       ├── passive-osint/SKILL.md
│       ├── pentest-recon/SKILL.md
│       ├── report-generator/SKILL.md
│       ├── secret-scanner/SKILL.md
│       ├── web-app-audit/SKILL.md
│       └── wordpress-audit/SKILL.md
├── opspectre-tools.md      # Full tool inventory
├── CONTAINER_PLAYBOOKS.md  # Playbook documentation
├── FULL_ARSENAL_README.md  # Full arsenal tools documentation
├── BURP_SUITE_VERIFICATION.md # Burp Suite setup verification
└── QUICK_START.md          # Getting started guide
```

## Common Development Tasks

### Setup Development Environment
```bash
# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### Run Tests
```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ -v --cov=opspectre --cov-report=html

# Run specific test file
uv run pytest tests/test_specific.py -v

# Run specific test
uv run pytest tests/test_specific.py::test_function_name -v
```

### Run the Full Arsenal Test
```bash
bash scripts/test-full-arsenal.sh
```

### Build & Start the Container
```bash
# Build the Docker image (app layer only — fast)
./scripts/build.sh app

# Build base + app (slow, for apt changes)
./scripts/build.sh

# Build with no cache
./scripts/build.sh --no-cache

# Start sandbox
opspectre sandbox start

# Check status
opspectre sandbox status

# Stop sandbox
opspectre sandbox stop

# Restart with new image
opspectre sandbox stop && sleep 2 && opspectre sandbox start
```

### Quick CLI Testing
```bash
# Test a shell command
opspectre shell "echo hello"

# Test bash-specific features (playbooks use bash)
opspectre shell "bash -c 'source /opt/playbooks/rate-limit-helpers.sh && random_ua'"

# Test file operations
opspectre file read /workspace/
opspectre file list /workspace/

# Test code execution
opspectre code python -c "print('test')"

# Run init
opspectre init
```

## Skill System

Skills are markdown files in `.pi/skills/*/SKILL.md` that provide specialized instructions for the AI agent.

### Current Skills
| Skill | Purpose | Updated |
|-------|---------|---------|
| `container-audit` | Trivy container scanning + best practices | ✅ |
| `docker-toolchain` | Docker image building, tool management | ✅ |
| `exploit-dev` | Metasploit, hydra, crackmapexec, evil-winrm | ✅ |
| `nmap-playbook` | Structured nmap scan profiles | ✅ |
| `opspectre-dev` | CLI development and testing | ✅ |
| `passive-osint` | crt.sh, gau, waybackurls, Google/Shodan dorks | ✅ |
| `pentest-recon` | Full recon pipeline (OSINT → subdomains → vuln scan) | ✅ |
| `report-generator` | Markdown → PDF/HTML/DOCX report generation | ✅ |
| `secret-scanner` | Trufflehog + pattern-based secret scanning | ✅ |
| `web-app-audit` | Full OWASP Top 10 web testing pipeline | ✅ |
| `wordpress-audit` | WordPress-specific security testing | ✅ |

### Adding a New Skill

1. Create directory: `.pi/skills/<skill-name>/`
2. Create `SKILL.md` with frontmatter:
```yaml
---
name: skill-name
description: Short description of when to use this skill.
---
```
3. Add structured content with prerequisites, commands, output locations, and tips
4. Cross-reference related skills (see existing skills for examples)
5. Test by running `opspectre shell` commands from the skill

## Playbook Architecture

Playbooks are bash scripts in `/opt/playbooks/` that provide reusable functions:

| Playbook | Source File | Key Functions |
|----------|------------|---------------|
| Rate-limit helpers | `containers/rate-limit-helpers.sh` | `random_ua`, `rl_nuclei`, `rl_ffuf`, `stealth_nmap`, `scan_with_tor` |
| OSINT | `containers/osint-playbook.sh` | `osint_ct_subdomains`, `osint_wayback_urls`, `osint_google_dorks`, `osint_shodan_queries`, `osint_github_dorks`, `osint_full_passive` |
| OWASP Top 10 | `containers/owasp-top10-playbook.sh` | Full automated scan pipeline |
| Burp Suite | `containers/burpsuite-playbook.sh` | `burpsuite-agent`, `burp_headless`, `burp_passive` |
| Scan helpers | `containers/scan-helpers.sh` | General scan utility functions |

**Important**: `opspectre shell` uses `/bin/sh`, not bash. To use playbook functions:
```bash
opspectre shell "bash -c 'source /opt/playbooks/rate-limit-helpers.sh && random_ua'"
```

## Makefile Targets

Check available targets:
```bash
make
```

Common targets typically include:
```bash
make test          # Run test suite
make build         # Build Docker image
make clean         # Clean build artifacts
make lint          # Run linters
make format        # Format code
```

## Code Style

- Python 3.x with type hints
- Use `uv` for dependency management
- Follow PEP 8 conventions
- Tests use pytest framework
- CLI built with (check pyproject.toml for framework — likely click/typer)

## Key Config Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Dependencies, scripts, tool config |
| `Makefile` | Build automation |
| `containers/Dockerfile` | Sandbox app layer image |
| `containers/Dockerfile.base` | Sandbox base image |
| `containers/docker-compose.yml` | Runtime config (DNS, volumes) |
| `containers/docker-entrypoint.sh` | Runtime init (DNS fix, playbooks) |
| `scripts/build.sh` | Docker build with caching |
| `scripts/test-full-arsenal.sh` | Full integration test |

## Debugging Tips

- Check container logs: `docker logs opspectre-default`
- Check container status: `opspectre sandbox status`
- Enter container directly: `docker exec -it opspectre-default bash`
- Use `opspectre shell "command"` to test individual commands
- Check `/workspace/output/` for test artifacts
- For bash-specific issues: `opspectre shell "bash -c '...'"` (shell uses `/bin/sh`)
- DNS issues: check `/etc/resolv.conf` — should be `8.8.8.8`, not `127.0.0.53`
- Tool missing after rebuild: stop + restart container (`opspectre sandbox stop && opspectre sandbox start`)

## Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Main project documentation |
| `PLAN.md` | Architecture and roadmap |
| `QUICK_START.md` | Getting started guide |
| `opspectre-tools.md` | Full tool inventory |
| `CONTAINER_PLAYBOOKS.md` | Container playbook documentation |
| `FULL_ARSENAL_README.md` | Full arsenal tools documentation |
| `BURP_SUITE_VERIFICATION.md` | Burp Suite setup verification |

## Adding New CLI Commands

1. Add command handler in `src/opspectre/commands/`
2. Register in the CLI router in `src/opspectre/cli/`
3. Add tests in `tests/`
4. Update `README.md` and `PLAN.md`
5. Run tests: `uv run pytest tests/ -v`

## Adding a New Tool to the Sandbox

See the `docker-toolchain` skill for the full step-by-step process. Quick reference:

1. Add to `containers/Dockerfile` (Go/Python/npm) or `containers/Dockerfile.base` (apt)
2. Rebuild: `./scripts/build.sh app` (or `./scripts/build.sh` for apt)
3. Restart: `opspectre sandbox stop && opspectre sandbox start`
4. Verify: `opspectre shell "<tool> --version"`
5. Update `opspectre-tools.md`, `CONTAINER_PLAYBOOKS.md`, relevant `SKILL.md` files
6. Optionally create playbook functions in `/opt/playbooks/`
