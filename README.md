# OperationSpectre

> **AI tool kit for security operations built for [pi](https://github.com/badlogic/pi-mono).**  
> A Kali-based Docker sandbox with 50+ pre-installed security tools, orchestration playbooks, and pi skill integration — designed for penetration testing, CTF competitions, and security assessments.

```
pi (AI agent) ←→ OperationSpectre skills/playbooks ←→ Docker sandbox (Kali + tools)
```

## ⚡ Quick Start (First-Time Setup)

> **IMPORTANT: You MUST build and start the Docker sandbox BEFORE running pi.**

### Step 1: Clone & Enter the Project

```bash
git clone https://github.com/your-repo/OperationSpectre
cd OperationSpectre
```

### Step 2: Build the Docker Sandbox (ONE-TIME)

```powershell
docker build --no-cache -f containers/Dockerfile -t opspectre-sandbox:latest .
```

**This takes 10-20 minutes on first build.** The image is ~3GB with 50+ security tools pre-installed.

### Step 3: Start the Container (EACH SESSION)

```powershell
docker compose -f containers/docker-compose.yml up -d
```

**The container runs in the background.** Verify it's running:

```powershell
docker ps | grep opspectre-sandbox
```

### Step 4: Run Pi (AUTO-DETECT)

```bash
pi
```

**Pi will automatically:**
- ✅ Detect the `.pi/skills/` directory in the project
- ✅ Load all 14 security skills
- ✅ Connect to the running sandbox

**You're now ready!** Ask pi to:
- "Run an OWASP Top 10 scan against https://target.com"
- "Enumerate subdomains for example.com"
- "Crack this hash: 5f4dcc3b5aa765d61d8327deb882cf99"

### Stopping the Sandbox

```powershell
docker compose -f containers/docker-compose.yml down
```

---

## 🎯 What It Is

OperationSpectre turns **pi** into a security operations workstation. It provides:

- 🐳 **Docker sandbox** — Kali Linux container with 50+ security tools pre-installed
- 🎯 **Pi skills** — Domain-specific instructions for recon, exploitation, web audits, and CTF
- 📋 **Playbooks** — Automated OWASP Top 10, nmap, OSINT, and pentest workflows

It is **not** an agent itself — it's the toolkit that powers agents.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│  pi (AI Agent)                                      │
│  ┌──────────┐ ┌──────────┐ ┌───────────────────┐   │
│  │ pentest  │ │  owasp   │ │   exploit-dev     │   │
│  │  recon   │ │  audit   │ │   web-app-audit   │   │
│  │  skill   │ │  skill   │ │      skill        │   │
│  └────┬─────┘ └────┬─────┘ └────────┬──────────┘   │
│       │             │                │               │
│       └─────────────┼────────────────┘               │
│                     ▼                                │
│  ┌──────────────────────────────────────────────┐   │
│  │  OperationSpectre Docker Sandbox             │   │
│  │  Kali Linux + 50+ security tools             │   │
│  │  ┌─────────┐ ┌─────────┐ ┌───────────────┐  │   │
│  │  │ nmap    │ │ sqlmap  │ │  pwntools     │  │   │
│  │  │ nuclei  │ │ ffuf    │ │  pycryptodome │  │   │
│  │  │ subfinder│ │ hydra  │ │  hashcat      │  │   │
│  │  │ httpx   │ │ burp    │ │  volatility3  │  │   │
│  │  └─────────┘ └─────────┘ └───────────────┘  │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## 📚 Advanced Usage

### Standalone CLI (Optional)

If you want to use the sandbox without pi:

```bash
uv sync
opspectre init
opspectre run "nmap -sV 192.168.1.1"
```

---

## 🧩 Pi Skills

The real power of OperationSpectre is its **pi skill library** — domain-specific instructions that teach the AI agent how to use each tool effectively.

> **Note:** Skills auto-load when you run `pi` from the OperationSpectre directory. You don't need to manually install them.

### Security Assessment

| Skill | Purpose |
|---|---|
| `pentest-recon` | Full recon pipeline: subfinder → httpx → nmap → nuclei → OSINT |
| `owasp-security-suite` | Comprehensive OWASP Top 10 testing with automated playbooks |
| `web-app-audit` | Full-stack web app security: Burp, ZAP, sqlmap, ffuf |
| `wordpress-audit` | WordPress-specific: wpscan, enumeration, plugin vulns |
| `passive-osint` | Zero-footprint recon: CT logs, Wayback, Google dorks, Shodan |
| `nmap-playbook` | Structured nmap scans: quick, deep, stealth, UDP |

### Exploitation & Cracking

| Skill | Purpose |
|---|---|
| `exploit-dev` | Active exploitation: pwncat-cs, hydra, john, hashcat |
| `secret-scanner` | Find leaked secrets: trufflehog, trivy, grep patterns |
| `container-audit` | Container vulnerability scanning with trivy |

### CTF Competition

| Skill | Purpose |
|---|---|
| `sandbox-tools` | Reference for all 50+ tools in the sandbox |
| `report-generator` | Generate structured pentest reports in markdown/PDF |

### Infrastructure

| Skill | Purpose |
|---|---|
| `docker-toolchain` | Build, test, and update the sandbox image |
| `parallel-pipeline-executor` | Run independent scan steps concurrently (60-80% faster) |
| `opspectre-dev` | Develop and test OperationSpectre itself |

---

## 🛡️ OWASP Top 10 Playbook

Built-in playbook for automated OWASP Top 10 (2021) testing:

```bash
# Inside the sandbox
source /opt/playbooks/owasp-top10-playbook.sh

# Full scan — all 10 categories
owasp_full_scan https://target.com

# Quick scan — fast triage (no sqlmap)
owasp_quick_scan https://target.com

# Individual categories
owasp_a03 https://target.com/login    # Injection
owasp_a10 https://target.com/fetch    # SSRF
```

### Categories Covered

| # | Category | What It Tests |
|---|---|---|
| A01 | Broken Access Control | IDOR, privilege escalation, path traversal, CORS |
| A02 | Cryptographic Failures | TLS ciphers, sensitive data exposure, cookie security |
| A03 | Injection | SQLi, XSS, SSTI, command injection, XXE |
| A04 | Insecure Design | User enumeration, rate limiting, business logic flaws |
| A05 | Security Misconfiguration | Exposed endpoints, debug modes, backup files, default creds |
| A06 | Vulnerable Components | Known CVEs, Log4j, tech fingerprinting |
| A07 | Authentication Failures | Default creds, brute force, account lockout, session management |
| A08 | Software/Data Integrity | JWT manipulation, deserialization, SRI, parameter tampering |
| A09 | Logging Failures | Error-based info leakage, verbose responses, dev comments |
| A10 | SSRF | Internal port scanning, cloud metadata, protocol smuggling |

---

## 🧰 Sandbox Tools

### Network & Recon
nmap, nuclei, subfinder, httpx, naabu, whatweb, theHarvester

### Web Application
sqlmap, ffuf, dalfox, nikto, wpscan, wapiti, gobuster, dirsearch

### Exploitation
pwncat-cs, hydra, john, hashcat

### Forensics & CTF
pwntools, pycryptodome, gmpy2, sympy, z3, RsaCtfTool, volatility3, binwalk, steghide, stegseek, zsteg

### Password Cracking
hashcat, john, wordlists (rockyou.txt, seclists)

### Container & Secrets
trivy, trufflehog, gitleaks

### Infrastructure
Burp Suite, OWASP ZAP, mitmproxy, chromium, gowitness

### Full tool reference
See [`.pi/skills/sandbox-tools/SKILL.md`](.pi/skills/sandbox-tools/SKILL.md)

### Tools Not Included in Current Build

The following tools were dropped from the Debian-slim image (~800 MB):

| Tool | Category | Reason Removed |
|---|---|---|
| **Metasploit** (msfconsole) | Exploitation framework | Heavy (~500 MB); use pwncat-cs + hydra instead |
| **Amass** | Subdomain enumeration | Redundant with subfinder + passive OSINT playbook |
| **Feroxbuster** | Directory brute-forcing | Redundant with ffuf + gobuster |
| **Burp Suite** (headless) | Web proxy/scanner | CDN download may fail; manual install available at /opt/burpsuite/ |

To add any of these back, edit `containers/Dockerfile` and rebuild.
---

## 📁 Project Structure

```
OperationSpectre/
├── .pi/
│   └── skills/              # Pi skill definitions (auto-loaded by pi)
│       ├── pentest-recon/
│       ├── owasp-security-suite/
│       ├── web-app-audit/
│       ├── exploit-dev/
│       ├── passive-osint/
│       ├── nmap-playbook/
│       ├── wordpress-audit/
│       ├── secret-scanner/
│       ├── container-audit/
│       ├── sandbox-tools/
│       ├── docker-toolchain/
│       ├── parallel-pipeline-executor/
│       ├── opspectre-dev/
│       └── report-generator/
├── containers/
│   ├── Dockerfile           # Sandbox image definition
│   ├── Dockerfile.base      # Base Kali image
│   ├── docker-compose.yml   # Container orchestration
│   └── docker-entrypoint.sh # Startup script (venv, DNS, tool server)
├── output/                  # Scan results (mounted from sandbox)
│   ├── reports/
│   ├── scans/
│   ├── loot/
│   ├── exploits/
│   └── owasp/
├── scripts/                 # Pipeline runners & automation
└── src/opspectre/           # Python source (CLI, sandbox)
```

---

## ⚙️ Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OPSPECTRE_IMAGE` | `opspectre-sandbox:latest` | Docker image name |
| `OPSPECTRE_TIMEOUT` | `120` | Command timeout (seconds) |
| `PIPELINE_CONCURRENCY` | `5` | Max parallel workers |
| `PIPELINE_TIMEOUT` | `300` | Pipeline step timeout |
| `TOOL_SERVER_TOKEN` | `changeme` | Auth token for the sandbox tool server |
| `TOOL_SERVER_PORT` | `9100` | Port for the sandbox tool server |
| `OPSPECTRE_SANDBOX_EXECUTION_TIMEOUT` | `120` | Sandbox command execution timeout (seconds) |

---

## 🔒 Sandbox Security

The Docker sandbox is **hardened by default** so that the container (and any agent like pi running inside it) can only access:

- ✅ **Output folder** (`./output` → `/workspace/output`) — read/write for scan results and reports
- ✅ **Internet** — outbound access for scanning targets and downloading resources

Everything else is **blocked**:

| Restriction | Details |
|---|---|
| 🚫 Host network | Bridge network (`172.22.0.0/16`) — cannot see host services, LAN devices, or pi agent on host |
| 🚫 Host filesystem | No host directory mounts (except output with `noexec,nosuid,nodev`) |
| 🚫 Host `/tmp` | Not mounted — cannot access host temp files, sockets, or session data |
| 🚫 Host processes | `SYS_PTRACE` dropped — cannot inspect or attach to host processes |
| 🚫 Network admin | `NET_ADMIN` dropped — cannot modify routes, iptables, or create tunnels |
| 🚫 Privilege escalation | `no-new-privileges:true`, `privileged:false` |
| 🚫 Syscall bypass | Docker's default seccomp profile active (not `unconfined`) |
| 🚫 Root filesystem writes | `read_only:true` — only tmpfs paths (`/tmp`, `/var/run`, `/var/tmp`, `/home/pentester`) are writable |
| 🚫 Fork bombs | `pids_limit:512` |
| 🚫 Resource abuse | `mem_limit:4g`, `cpus:2.0` |
| 🚫 Unnecessary capabilities | `cap_drop: ALL` — only `NET_RAW` and `NET_BIND_SERVICE` re-added |

### How It Works

```
┌───────────────────────────────────────┐
│  Docker Host                          │
│                                       │
│  ┌─────────────────────────────────┐  │
│  │  Bridge: 172.22.0.0/16          │  │
│  │                                 │  │
│  │  ┌───────────────────────────┐  │  │
│  │  │  opspectre container      │  │  │
│  │  │                           │  │  │
│  │  │  ✅ Internet (outbound)   │  │  │
│  │  │  ✅ /workspace/output     │  │  │
│  │  │  ✅ /tmp (tmpfs, 512m)    │  │  │
│  │  │  🚫 Host network         │  │  │
│  │  │  🚫 Host filesystem      │  │  │
│  │  │  🚫 Host processes       │  │  │
│  │  └───────────────────────────┘  │  │
│  │           │                     │  │
│  │           ▼ NAT                 │  │
│  │      Internet access only       │  │
│  └─────────────────────────────────┘  │
│                                       │
│  🚫 Container CANNOT reach here       │
└───────────────────────────────────────┘
```

### Security Checklist

If you modify the compose files, make sure these safeguards stay in place:

- [ ] `network_mode: host` is **never** used — always use a bridge network
- [ ] `seccomp=unconfined` is **never** set — use Docker's default profile
- [ ] `cap_drop: ALL` is always present before any `cap_add`
- [ ] `no-new-privileges:true` is always set
- [ ] `read_only: true` is set with tmpfs for writable paths
- [ ] Volume mounts use `noexec,nosuid,nodev` flags
- [ ] `SYS_PTRACE` and `NET_ADMIN` are **not** in `cap_add`
- [ ] `/tmp` host mount is **never** used
- [ ] Published ports are bound to `127.0.0.1` only (not `0.0.0.0`)

---

## 📄 License

Apache-2.0
