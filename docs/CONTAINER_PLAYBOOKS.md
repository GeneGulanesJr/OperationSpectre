# Container Playbooks - Embedded for All Agents

## Overview
All playbooks are embedded directly in the Docker container. Any AI agent using the container has immediate access without needing to load external files.

## Architecture Integration

### MCP Mode (AI Agents)
```
AI Agent → MCP Server → CLI → Docker Container
    ↓         ↓         ↓      ↓
60-80%    Structured Fast   50+ Tools
Token     JSON      CLI   Playbooks
Saving    Response  Backend Embedded
```

### CLI Mode (Manual)
```
User → CLI → Docker Container
    ↓      ↓      ↓
Manual  Text    50+ Tools
    │      │      │
    │      │      └ Playbooks Embedded
    │      └ Output Parsing
    └ Manual Execution
```

## Burp Suite Playbook

### Location
- Full playbook: `/opt/playbooks/burpsuite-playbook.sh`
- Agent wrapper: `/usr/local/bin/burpsuite-agent`
- Auto-loaded: Yes (via `.bashrc` and `/etc/bash.bashrc`)

### How Any Agent Can Use It

#### Method 1: Simple Agent Wrapper (Recommended)
```bash
# Any agent can run these immediately:
burpsuite-agent start                          # Start Burp
burpsuite-agent scan https://target.com        # Scan target
burpsuite-agent spider https://target.com      # Crawl target
burpsuite-agent stop                           # Stop Burp
```

#### Method 2: Full Playbook Functions
```bash
# After shell login, these functions are available:
burp_headless                                  # Start headless
burp_passive_scan https://target.com           # Passive scan
burp_active_scan https://target.com            # Active scan (with auth)
burp_spider https://target.com                 # Spider/crawl
burp_proxy_url https://target.com              # Fetch via proxy
burp_chain_nmap 192.168.1.1                    # Chain with nmap
burp_help                                      # Show all commands
```

#### Method 3: Direct Java (Advanced)
```bash
java -Xmx2g -Djava.awt.headless=true -jar /opt/burpsuite/burpsuite_community.jar \
    --project-file=/workspace/output/burp-projects/session.burp \
    --config-file=/opt/burpsuite/configs/default.json
```

### Quick Reference Card
```
BURP SUITE QUICK COMMANDS
=========================

START:    burpsuite-agent start
SCAN:     burpsuite-agent scan <url>
SPIDER:   burpsuite-agent spider <url>
PROXY:    burpsuite-agent proxy <url>
STOP:     burpsuite-agent stop
STATUS:   burpsuite-agent status

PORTS:    8080 (proxy), 5900 (VNC), 6080 (noVNC)
FILES:    /workspace/output/burp-projects/
```

## File Locations in Container

### Playbooks
```
/opt/playbooks/
├── scan-helpers.sh              # Shared scan output utilities
├── burpsuite-playbook.sh        # Full Burp Suite playbook
├── owasp-top10-playbook.sh      # OWASP Top 10 testing playbook
├── osint-playbook.sh            # Passive OSINT recon playbook
├── rate-limit-helpers.sh        # Rate-limit & WAF evasion helpers
└── [future playbooks]
```

### Agent Wrappers
```
/usr/local/bin/
├── burpsuite-agent              # Burp Suite agent wrapper
├── msf-run                      # Metasploit wrapper
├── hydra-run                    # Hydra wrapper
├── hashcat-run                  # Hashcat wrapper
└── [other tool wrappers]
```

### Tool Locations
```
/opt/burpsuite/
├── burpsuite_community.jar      # Burp Suite JAR
├── configs/                     # Configuration files
│   ├── default.json            # Default config
│   └── aggressive.json         # Aggressive scan config
└── extensions/                  # Extensions

/workspace/output/
├── burp-projects/               # Burp project files
├── reports/                     # Exported reports
├── loot/                        # Stolen credentials
├── scans/                       # Scan results
└── exploits/                    # Generated exploits
```

## Agent Usage Examples

### Example 1: Quick Passive Scan
```bash
# Agent just runs:
burpsuite-agent scan https://example.com passive

# What happens:
# 1. Starts Burp if not running
# 2. Creates project file
# 3. Sends initial requests through proxy
# 4. Returns project file location
```

### Example 2: Spider + Scan
```bash
# Agent runs:
burpsuite-agent spider https://example.com
burpsuite-agent scan https://example.com active

# Or use playbook functions:
burp_spider https://example.com
burp_active_scan https://example.com
```

### Example 3: Chain with Other Tools
```bash
# Agent runs:
burpsuite-agent chain nmap 192.168.1.1
burpsuite-agent chain nuclei https://example.com

# What happens:
# 1. Runs nmap/nuclei first
# 2. Extracts web ports/vulnerabilities
# 3. Provides guidance for Burp integration
```

## What Makes This Agent-Friendly

1. **No External Files Needed**: Everything is in the container
2. **Auto-Loaded**: Playbook loads on shell login
3. **Simple Commands**: `burpsuite-agent <action> <target>`
4. **Self-Documenting**: `burpsuite-agent help` shows usage
5. **Error Handling**: Clear error messages
6. **Default Configs**: Pre-generated, ready to use
7. **Directory Structure**: Auto-created on container start

## For Future Tools

To add playbooks for other tools:
1. Create playbook script in `containers/`
2. Create agent wrapper in `containers/`
3. Update `Dockerfile` to copy them
4. Add to `.bashrc` for auto-loading

> **Note:** There is one unified `containers/Dockerfile` that includes all tools (full Kali image).
> Older references to `Dockerfile.full` have been consolidated into `Dockerfile`.

Template for new tool playbook:
```bash
#!/bin/bash
# Tool: <tool_name>
# Location: /opt/playbooks/<tool_name>-playbook.sh

# Environment setup
export TOOL_PATH="/path/to/tool"
mkdir -p /workspace/output/<tool_name>

# Core functions
tool_start() { ... }
tool_stop() { ... }
tool_scan() { ... }

# Help
tool_help() {
    echo "Usage: tool-agent <action> <target>"
}

# Auto-load
echo "[<tool_name>] Playbook loaded"
```

## Verification

After container starts, verify playbooks are available:
```bash
# Check Burp playbook
burphelp

# Check agent wrapper
burpsuite-agent help

# Verify functions loaded
type burp_headless
type burp_passive_scan
```

## Notes

- All playbooks are **read-only** in the container
- Output goes to `/workspace/output/` (mounted to Desktop)
- Configs are generated on first use
- Playbooks are **persistent** across container restarts (baked into image)
- Agent wrappers are in PATH, available immediately