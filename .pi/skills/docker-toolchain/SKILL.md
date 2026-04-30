---
name: docker-toolchain
description: Builds, tests, and updates the OperationSpectre Docker image. Manages the container playbook system. Use when modifying Dockerfile or adding new tools to the sandbox.
---

# Docker Toolchain Management

Manages the OperationSpectre sandbox Docker image — building, updating, adding tools, and maintaining the playbook system. Includes DNS fixes, rate-limit helpers, proxychains, and all new tools added during toolchain evolution.

## Prerequisites

- Docker installed and running on the host
- Docker BuildKit enabled (default in Docker 23+, or set `DOCKER_BUILDKIT=1`)
- Access to the `containers/` directory in the project

## Project Docker Structure (Two-Stage Build)

The image is split into a **heavy base** (rarely rebuilt) and a **fast app layer** (rebuilt often):

```
containers/
├── Dockerfile.base    # Heavy Kali base (apt packages, wordlists, metasploit, certs)
├── Dockerfile         # App layer (playbooks, Go/Python/npm tools, wrappers, app code)
├── docker-compose.yml # Container runtime config (DNS, volumes, ports)
├── docker-entrypoint.sh  # Runtime init (DNS fix, playbooks, permissions)
├── osint-playbook.sh     # Passive OSINT functions
├── rate-limit-helpers.sh # Rate-limit & stealth helper functions
├── owasp-top10-playbook.sh  # OWASP Top 10 automated scan pipeline
├── burpsuite-playbook.sh    # Burp Suite headless agent
├── scan-helpers.sh         # General scan utility functions
└── wrappers/            # Agent wrapper scripts
```

| Image | What's in it | Rebuild frequency | Build time |
|-------|-------------|-------------------|------------|
| `opspectre-base` | Kali metapackages, all apt tools, wordlists, Burp, MSF DB, certs, security tools | Rarely (monthly or when adding apt packages) | 15-30 min |
| `opspectre-full` | Playbooks, Go/Python/npm tools, wrappers, app code | Often (daily dev) | 2-5 min |

### Container Layout
```
/opt/playbooks/               # Full playbook scripts (auto-sourced in bash)
/usr/local/bin/               # Agent wrappers (burpsuite-agent, msf-run, hydra-run, hashcat-run)
/root/go/bin/                 # Go tools (gowitness, gau, waybackurls, subjack, dalfox, nuclei)
/root/.local/bin/             # pipx-installed Python tools (webtech)
/etc/bash.bashrc              # Auto-loads playbooks on interactive shell login
/etc/proxychains/proxychains.conf  # Proxy rotation config (proxychains4)
/etc/resolv.conf              # Runtime DNS fix (entrypoint replaces stub resolver)
/opt/opspectre/wordlists/     # Custom wordlists (user-agents.txt)
/opt/opspectre/tools/         # Custom tool scripts (JS-Snooper, jsniper)
/usr/share/seclists/          # SecLists wordlist collection
/usr/share/wordlists/         # Standard wordlists (dirb, dirbuster, rockyou)
/workspace/output/            # Mounted output directory
```

## Key Infrastructure Fixes

### DNS Fix
The entrypoint script auto-replaces Docker's broken `127.0.0.53` stub resolver:
- **docker-compose.yml**: Sets `dns: [8.8.8.8, 1.1.1.1, 9.9.9.9]`
- **docker-entrypoint.sh**: Overwrites `/etc/resolv.conf` if it contains `127.0.0.53`

### Rate-Limit Helpers
Auto-loaded functions for WAF-aware scanning:
```bash
source /opt/playbooks/rate-limit-helpers.sh

$RL_NUCLEI   # nuclei: -rl 15 -bs 25 -c 5 -timeout 15 -retries 2
$RL_FFUFC    # ffuf: -t 20 -p 0.5 --timeout 10 --rate 15/second
$RL_KATANA   # katana: -rl 10 -c 5
$RL_HTTPX    # httpx: -rate-limit 5 -timeout 15 -retries 2
random_ua    # Returns random User-Agent from wordlist
rl_nuclei    # nuclei wrapper with rate limits
rl_ffuf      # ffuf wrapper with rate limits
stealth_nmap # Slow nmap with fragmentation & decoys
scan_with_tor # Route command through Tor
```

### Proxychains (Proxy Rotation)
```bash
proxychains4 <command>  # Route through configured proxy chain
```

## Common Tasks

### Build the Images

```bash
# Full build (base + app) with persistent cache
./scripts/build.sh

# Rebuild ONLY the app layer (fast — ~2-5 min)
./scripts/build.sh app

# Rebuild ONLY the base layer
./scripts/build.sh base

# Full clean build (no cache)
./scripts/build.sh --no-cache

# Build and push base to registry
OPSPECTRE_REGISTRY=ghcr.io/org/opspectre-base ./scripts/build.sh --push
```

### Legacy Docker Commands

```bash
# Build base only
docker build -f containers/Dockerfile.base -t opspectre-base:latest .

# Build app layer (requires base)
docker build -f containers/Dockerfile -t opspectre-full:latest .

# Build with no cache
docker build --no-cache -f containers/Dockerfile.base -t opspectre-base:latest .
```

### Start / Stop / Status

```bash
opspectre sandbox start     # Start sandbox container
opspectre sandbox stop      # Stop sandbox container
opspectre sandbox status    # Check container status

# Stop and restart with new image
opspectre sandbox stop && sleep 2 && opspectre sandbox start
```

### Test the Image
```bash
# Verify core tools
opspectre shell "nmap --version | head -1"
opspectre shell "nuclei -version 2>&1 | head -1"
opspectre shell "trivy --version | head -1"

# Verify new tools (Go)
opspectre shell "gowitness version 2>&1 | head -1"
opspectre shell "dalfox version 2>&1 | head -1"
opspectre shell "echo test | gau 2>&1 | head -1"
opspectre shell "echo test | waybackurls 2>&1 | head -1"
opspectre shell "subjack -help 2>&1 | head -1"

# Verify new tools (Python/pipx)
opspectre shell "webtech --help 2>&1 | head -1"
opspectre shell "wpscan --version 2>&1 | head -1"

# Verify reporting
opspectre shell "pandoc --version | head -1"

# Verify infrastructure
opspectre shell "proxychains4 --help 2>&1 | head -1"
opspectre shell "grep 'nameserver 8.8.8.8' /etc/resolv.conf"
opspectre shell "wc -l /opt/opspectre/wordlists/user-agents.txt"

# Verify playbooks (must use bash — opspectre shell uses /bin/sh)
opspectre shell "bash -c 'source /opt/playbooks/rate-limit-helpers.sh && type random_ua'"
opspectre shell "bash -c 'source /opt/playbooks/osint-playbook.sh && type osint_full_passive'"
```

### Run the Full Arsenal Test
```bash
bash scripts/test-full-arsenal.sh
```

## Adding a New Tool

### Where to add it?

| Tool type | Which Dockerfile? | Why? |
|-----------|-------------------|------|
| `apt-get install` | `Dockerfile.base` | It's a heavy apt dependency; only rebuilt rarely |
| `pipx install` | `Dockerfile` (app) | Fast rebuild, cached |
| `go install` | `Dockerfile` (app) | Fast rebuild, cached |
| `npm install -g` | `Dockerfile` (app) | Fast rebuild, cached |
| `pip install` | `Dockerfile` (app) | Fast rebuild, cached |
| Python app dependency | `pyproject.toml` | Auto-installed in app layer |

### Step 1: Add to Dockerfile

**Apt tools** — add to `containers/Dockerfile.base`:
```dockerfile
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y --no-install-recommends new-tool
```

**Go tools** — add to `containers/Dockerfile` (app layer), pin version:
```dockerfile
RUN --mount=type=cache,target=/root/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go install -v github.com/org/tool@v1.2.3
```

**Python tools** — add to `containers/Dockerfile` (app layer):
```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.local/pipx \
    pipx install new-tool
```

### Step 2: Create Agent Wrapper (Optional)

Create a wrapper script in `containers/wrappers/`:

```bash
#!/bin/bash
# Agent wrapper for new-tool
# Installs to: /usr/local/bin/new-tool-run

TOOL_PATH="$(which new-tool)"
OUTPUT_DIR="/workspace/output/new-tool"
mkdir -p "$OUTPUT_DIR"

case "${1:-help}" in
    scan)
        new-tool scan "$2" -o "$OUTPUT_DIR/$2-scan.txt"
        ;;
    help|--help|-h)
        echo "Usage: new-tool-run <action> <target>"
        echo "Actions: scan, help"
        ;;
    *)
        new-tool "$@"
        ;;
esac
```

### Step 3: Create Playbook (Optional)

Create `/opt/playbooks/new-tool-playbook.sh` with advanced functions:

```bash
#!/bin/bash
# Tool: new-tool
# Location: /opt/playbooks/new-tool-playbook.sh

export TOOL_PATH="/usr/local/bin/new-tool"
mkdir -p /workspace/output/new-tool

tool_scan() {
    echo "[new-tool] Starting scan: $1"
    new-tool scan "$1" -o "/workspace/output/new-tool/scan-$(date +%s).txt"
}

tool_help() {
    echo "new-tool playbook commands:"
    echo "  tool_scan <target>   Run scan"
}

echo "[new-tool] Playbook loaded"
```

### Step 4: Auto-load in bashrc

Add to the PLAYBOOKS section in `containers/Dockerfile` (app layer):
```dockerfile
COPY new-tool-playbook.sh /opt/playbooks/new-tool-playbook.sh
RUN chmod +x /opt/playbooks/new-tool-playbook.sh && \
    echo 'source /opt/playbooks/new-tool-playbook.sh' >> /etc/bash.bashrc
```

### Step 5: Update Documentation

Update these files:
- `opspectre-tools.md` — add tool to the inventory table
- `CONTAINER_PLAYBOOKS.md` — add playbook documentation
- `README.md` — if the tool is user-facing
- Update relevant skill SKILL.md files (e.g., `web-app-audit`, `pentest-recon`)

### Step 6: Rebuild & Test

```bash
# If it's an apt tool, rebuild base:
./scripts/build.sh base && ./scripts/build.sh app

# If it's a Go/Python/npm tool, just rebuild app:
./scripts/build.sh app

# Stop and restart with new image:
opspectre sandbox stop && sleep 2 && opspectre sandbox start

# Verify:
opspectre shell "new-tool --version"
```

## Managing Output Directories

The container uses a standard output structure:
```
/workspace/output/
├── recon/           # Reconnaissance results (subdomains, port scans, live hosts)
├── osint/           # Passive OSINT (CT subdomains, wayback URLs, dorks)
├── web-audit/       # Web application audit results
├── wordpress/       # WordPress-specific audit results
├── container-audit/ # Container scan results
├── secrets/         # Secret scanning results
├── exploits/        # Exploitation results
├── loot/            # Captured credentials
├── nmap/            # Standalone nmap scans
├── scans/           # General scan results
├── burp-projects/   # Burp Suite project files
├── reports/         # Generated reports (markdown, PDF, HTML, DOCX)
└── <tool-name>/     # Per-tool output directories
```

## Build Caching

### How it works

- **apt cache mounts**: `/var/cache/apt` and `/var/lib/apt` are cached across builds using BuildKit `--mount=type=cache`
- **Go module cache**: `/root/go/pkg/mod` and `/root/.cache/go-build` are cached
- **pip/npm cache**: `/root/.cache/pip`, `/root/.local/pipx`, `/root/.npm` are cached
- **Git clone cache**: `/tmp/git-clones` preserves cloned repos between builds
- **Buildx layer cache**: `.docker-cache/` persists full layer cache across `docker buildx` runs

### Clearing cache

```bash
# Clear all build caches
rm -rf .docker-cache/

# Clear only Go module cache
docker builder prune --filter "label=stage=go-tools"

# Clear everything
docker builder prune -a
```

## Known Issues & Workarounds

| Issue | Cause | Fix |
|-------|-------|-----|
| DNS resolution fails | Docker stub resolver `127.0.0.53` | Entrypoint auto-fixes; also set `dns:` in compose |
| `dirsearch` broken | Python 3.13 removed `pkg_resources` | Removed; use `gobuster` or `ffuf` |
| `nuclei -update-templates` fails | nuclei v3.x changed flag name | Use `nuclei -ut` (v3) with fallback to v2 flag |
| Playbooks not loaded | `opspectre shell` uses `/bin/sh` | Use `bash -c 'source ...'` explicitly |
| WAF blocks all scans | Aggressive timing/default UAs | Use `$RL_*` vars, `random_ua`, `stealth_nmap`, `scan_with_tor` |

## Docker Best Practices (Applied)

- ✅ Two-stage build (base + app) for fast iteration
- ✅ BuildKit cache mounts on all RUN layers
- ✅ `--no-install-recommends` on all apt installs
- ✅ No `apt-get upgrade` (avoids rebuilding the world)
- ✅ Pinned Go tool versions
- ✅ `.dockerignore` to minimize build context
- ✅ Cleanup layer at end of base image
- ✅ Persistent buildx cache via `scripts/build.sh`
- ✅ Application code in the last layer (most volatile = last to change)
- ✅ DNS fix in entrypoint (handles Docker stub resolver bug)
- ✅ External DNS servers in docker-compose.yml
- ✅ Proxychains for proxy rotation support
- ✅ Rate-limit helpers for WAF-aware scanning
