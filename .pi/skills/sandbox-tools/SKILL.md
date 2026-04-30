---
name: sandbox-tools
description: Reference for all tools, playbooks, and workflows available inside the OperationSpectre Docker sandbox. Load this when running security commands in the sandbox container.
---

# OperationSpectre Sandbox — Tool Reference

When the sandbox extension is connected, all bash/read/write/edit operations execute inside the `opspectre-full` Docker container (Kali-based). This is your consolidated reference for everything available.

## Container Layout

```
/opt/playbooks/               # Auto-sourced playbook scripts
/usr/local/bin/               # Agent wrapper scripts (msf-run, hydra-run, etc.)
/root/go/bin/                 # Go security tools
/root/.local/bin/             # Python tools (pipx)
/usr/share/seclists/          # SecLists wordlist collection
/usr/share/wordlists/         # Standard wordlists (rockyou.txt, dirb, dirbuster)
/opt/opspectre/wordlists/     # Custom wordlists (user-agents.txt)
/opt/opspectre/tools/         # Custom tools (JS-Snooper, jsniper, jwt_tool, RsaCtfTool)
/workspace/output/            # All scan output goes here
```

## Output Directory Convention

**Always save output under `/workspace/output/`:**

```
/workspace/output/
├── recon/            # Subdomains, port scans, live hosts, screenshots
├── osint/            # Passive OSINT results
├── web-audit/        # Web application audit findings
├── wordpress/        # WordPress-specific results
├── container-audit/  # Container scan results
├── secrets/          # Secret scanning findings
├── exploits/         # Exploitation results, captured creds
├── nmap/             # Standalone nmap scans
├── scans/            # General scan results
├── burp-projects/    # Burp Suite project files
├── reports/          # Generated reports (MD, PDF, HTML)
└── loot/             # Captured credentials and hashes
```

Pre-create directories before use: `mkdir -p /workspace/output/<category>`

## Network Reconnaissance

### nmap
```bash
# Quick scan (top 100 ports)
nmap -sV -sC -T4 -F <TARGET> -oA /workspace/output/nmap/quick

# Full port scan
nmap -sV -sC -T4 -p- <TARGET> -oA /workspace/output/nmap/full

# UDP scan
nmap -sU -sV --top-ports 100 <TARGET> -oA /workspace/output/nmap/udp

# Stealth scan (fragmented + decoys)
stealth_nmap <TARGET>   # From rate-limit-helpers playbook
```

### subfinder — Subdomain discovery
```bash
subfinder -d <DOMAIN> -o /workspace/output/recon/subdomains.txt
```

### httpx — HTTP probing
```bash
cat /workspace/output/recon/subdomains.txt | httpx -status-code -title -tech-detect -rate-limit 5 -timeout 15 -o /workspace/output/recon/live-hosts.txt
```

### naabu — Port scanning (fast)
```bash
naabu -host <TARGET> -o /workspace/output/recon/naabu-ports.txt
```

### gowitness — Visual recon (screenshots)
```bash
cat /workspace/output/recon/live-hosts.txt | grep -oE 'https?://[^ ]+' | gowitness file - -P /workspace/output/recon/screenshots/
```

## Vulnerability Scanning

### nuclei — Template-based vulnerability scanner
```bash
# Scan with rate limiting
nuclei -l /workspace/output/recon/live-hosts.txt -o /workspace/output/scans/nuclei-findings.txt -severity medium,high,critical -rl 15 -bs 25 -c 5 -timeout 15

# Using rate-limit helper
source /opt/playbooks/rate-limit-helpers.sh && rl_nuclei -l /workspace/output/recon/live-hosts.txt -o /workspace/output/scans/nuclei.txt
```

### nikto — Web server scanner
```bash
nikto -h <URL> -o /workspace/output/scans/nikto.txt
```

## Web Application Testing

### ffuf — Fuzzing (directories, params, vhosts)
```bash
# Directory brute-force with rate limiting
ffuf -u <URL>/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt -t 20 -p 0.5 --timeout 10 --rate 15/second -o /workspace/output/web-audit/ffuf-dirs.json

# Using rate-limit helper
source /opt/playbooks/rate-limit-helpers.sh && rl_ffuf <URL>
```

### sqlmap — SQL injection
```bash
sqlmap -u "<URL>?param=value" --batch --random-agent -o /workspace/output/web-audit/sqlmap/
```

### dalfox — XSS scanner
```bash
dalfox url <URL> -o /workspace/output/web-audit/dalfox-xss.txt
```

### katana — Web crawler
```bash
echo <URL> | katana -rl 10 -c 5 -d 3 -o /workspace/output/web-audit/crawled-urls.txt
```

### burpsuite — Headless scanning
```bash
burpsuite-headless -t <URL> -o /workspace/output/web-audit/burp-findings.txt
```

## WordPress Testing

### wpscan
```bash
wpscan --url <URL> --enumerate u,vp,vt --random-user-agent --disable-tls-checks -o /workspace/output/wordpress/wpscan.txt
```

## Container & Infrastructure Security

### trivy — Container/filesystem/config scanner
```bash
# Image scanning
trivy image <IMAGE> --severity HIGH,CRITICAL -o /workspace/output/container-audit/critical.txt

# Secret scanning
trivy image <IMAGE> --scanners secret -o /workspace/output/container-audit/secrets.txt

# Filesystem scanning
trivy fs /path/to/code -o /workspace/output/container-audit/fs-scan.txt

# Config scanning (Dockerfile, compose, K8s)
trivy config /path/to/config -o /workspace/output/container-audit/config-scan.txt
```

## Exploitation

### Metasploit
```bash
# Non-interactive via wrapper
msf-run "use exploit/multi/handler; set PAYLOAD windows/meterpreter/reverse_tcp; set LHOST <IP>; set LPORT 4444; exploit"

# Interactive
msfconsole -q
```

### hydra — Credential brute-forcing
```bash
hydra-run "ssh://<IP> -l root -P /usr/share/wordlists/rockyou.txt -t 4"
# Or directly:
hydra -l admin -P /usr/share/wordlists/rockyou.txt <IP> http-post-form '/login:user=^USER^&pass=^PASS^:F=incorrect' -o /workspace/output/exploits/hydra.txt
```

### crackmapexec — Network pentesting
```bash
cme-run "smb <IP> -u admin -p 'password' --shares"
cme-run "smb <IP> -u admin -p 'password' -x 'whoami'"
```

### evil-winrm — WinRM shell
```bash
evil-winrm-run "-i <IP> -u admin -p 'password'"
```

### john — Password cracker
```bash
john-run "/workspace/output/exploits/hashes.txt --wordlist=/usr/share/wordlists/rockyou.txt"
```

### hashcat — GPU password cracker
```bash
hashcat-run "-m 1000 /workspace/output/exploits/ntlm.txt /usr/share/wordlists/rockyou.txt"
```

## Passive OSINT

### Playbook functions (source first)
```bash
source /opt/playbooks/osint-playbook.sh

osint_full_passive <DOMAIN>        # Full passive OSINT pipeline
osint_ct_subdomains <DOMAIN>       # Certificate Transparency subdomains
osint_google_dorks <DOMAIN>        # Google dorking
osint_shodan_queries <DOMAIN>      # Shodan queries
osint_github_dorks <ORG>           # GitHub dorking
```

### Standalone OSINT tools
```bash
# URL discovery
echo <DOMAIN> | gau -o /workspace/output/osint/gau-urls.txt
echo <DOMAIN> | waybackurls -o /workspace/output/osint/wayback-urls.txt

# Web fingerprinting
whatweb <URL> -o /workspace/output/osint/whatweb.txt
```

## Secret Scanning

### trufflehog
```bash
trufflehog git <REPO_URL> --json > /workspace/output/secrets/trufflehog.json
trufflehog filesystem /path/to/code --json > /workspace/output/secrets/trufflehog-fs.json
trufflehog image <IMAGE> --json > /workspace/output/secrets/trufflehog-image.json
```

### theHarvester — Email & OSINT
```bash
theHarvester -d <DOMAIN> -b google,bing,linkedin -l 100 > /workspace/output/osint/theharvester.txt
```

## Rate-Limit & Stealth Helpers

Always source the playbook first:
```bash
source /opt/playbooks/rate-limit-helpers.sh
```

| Variable / Function | Use |
|---------------------|-----|
| `$RL_NUCLEI` | nuclei rate-limit flags: `-rl 15 -bs 25 -c 5 -timeout 15 -retries 2` |
| `$RL_FFUFC` | ffuf rate-limit flags: `-t 20 -p 0.5 --timeout 10 --rate 15/second` |
| `$RL_KATANA` | katana rate-limit flags: `-rl 10 -c 5` |
| `$RL_HTTPX` | httpx rate-limit flags: `-rate-limit 5 -timeout 15 -retries 2` |
| `random_ua` | Returns a random User-Agent string |
| `rl_nuclei` | nuclei wrapper with rate limits built in |
| `rl_ffuf` | ffuf wrapper with rate limits built in |
| `stealth_nmap` | Slow nmap with fragmentation & decoys |
| `scan_with_tor` | Route a command through Tor |

## Agent Wrapper Scripts

Available at `/usr/local/bin/`:

| Wrapper | Tool | Usage |
|---------|------|-------|
| `msf-run` | Metasploit | `msf-run "use exploit/...; set RHOSTS x.x.x.x; exploit"` |
| `hydra-run` | Hydra | `hydra-run "ssh://x.x.x.x -l root -P rockyou.txt"` |
| `hashcat-run` | Hashcat | `hashcat-run "-m 1000 hashes.txt rockyou.txt"` |
| `john-run` | John the Ripper | `john-run "hashes.txt --wordlist=rockyou.txt"` |
| `cme-run` | CrackMapExec | `cme-run "smb x.x.x.x -u admin -p pass"` |
| `evil-winrm-run` | Evil-WinRM | `evil-winrm-run "-i x.x.x.x -u admin -p pass"` |
| `responder-run` | Responder | `responder-run "-I eth0"` |
| `aircrack-run` | Aircrack-ng | `aircrack-run "capture.cap -w rockyou.txt"` |
| `pwn-run` | pwntools | `pwn-run "exploit.py"` |
| `vol-run` | Volatility | `vol-run "-f memory.dmp windows.pslist"` |
| `steg-run` | Steghide | `steg-run "extract -sf image.jpg"` |
| `z3-run` | Z3 SMT solver | `z3-run "constraints.smt2"` |

## Reporting

### pandoc — Report generation
```bash
# Markdown → PDF
pandoc /workspace/output/report/report.md -o /workspace/output/report/report.pdf --pdf-engine=xelatex --toc

# Markdown → HTML
pandoc /workspace/output/report/report.md -o /workspace/output/report/report.html --standalone --toc
```

## Wordlists

| Location | Contents |
|----------|----------|
| `/usr/share/wordlists/rockyou.txt` | Default password list (14M passwords) |
| `/usr/share/seclists/Discovery/Web-Content/` | Web content wordlists |
| `/usr/share/seclists/Passwords/` | Password lists |
| `/usr/share/seclists/Usernames/` | Username lists |
| `/usr/share/seclists/Fuzzing/` | Fuzzing payloads |
| `/usr/share/dirb/` | dirb wordlists |
| `/usr/share/dirbuster/` | dirbuster wordlists |
| `/opt/opspectre/wordlists/user-agents.txt` | User-Agent strings |

## Tips

- **Always create output directories first**: `mkdir -p /workspace/output/<category>`
- **Use rate-limiting**: WAFs will block aggressive scans. Use `$RL_*` variables.
- **Use `-oA` with nmap**: Saves in all formats (normal, XML, grepable).
- **Check tool versions**: `nmap --version`, `nuclei -version`, etc.
- **Playbooks auto-load in interactive bash**: But use `bash -c 'source /opt/playbooks/...'` from non-interactive contexts.
- **Proxychains**: `proxychains4 <command>` to route through configured proxy chain.
- **DNS is pre-configured**: Uses 8.8.8.8, 1.1.1.1, 9.9.9.9 (Docker stub resolver is auto-fixed).
