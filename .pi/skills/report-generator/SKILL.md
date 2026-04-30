---
name: report-generator
description: Collects scan results from /workspace/output/ and generates a structured pentest report in markdown and PDF. Use when finishing an engagement and need to summarize findings.
---

# Pentest Report Generator

Collects all scan results from the OperationSpectre sandbox output directory and generates a structured, professional pentest report in both Markdown and PDF formats.

## Prerequisites

- Scans completed and results stored in `/workspace/output/`
- OperationSpectre sandbox running for accessing results
- pandoc + texlive installed (available in container for PDF generation)

## How It Works

This skill guides the agent through collecting, parsing, and organizing all output files into a unified report.

## Step 1: Inventory Available Results

```bash
opspectre shell "find /workspace/output/ -type f -name '*.txt' -o -name '*.json' -o -name '*.xml' -o -name '*.html' | sort"
```

## Step 2: Collect Reconnaissance Data

```bash
opspectre shell "cat /workspace/output/recon/subdomains.txt 2>/dev/null"
opspectre shell "cat /workspace/output/recon/live-hosts.txt 2>/dev/null"
opspectre shell "cat /workspace/output/recon/portscan.nmap 2>/dev/null"
opspectre shell "cat /workspace/output/recon/whois.txt 2>/dev/null"
opspectre shell "cat /workspace/output/osint/ct-subdomains.txt 2>/dev/null"
opspectre shell "cat /workspace/output/osint/gau-urls.txt 2>/dev/null"
opspectre shell "cat /workspace/output/osint/dorks.txt 2>/dev/null"
```

## Step 3: Collect Vulnerability Findings

```bash
opspectre shell "cat /workspace/output/recon/nuclei-findings.txt 2>/dev/null"
opspectre shell "cat /workspace/output/web-audit/nuclei-findings.txt 2>/dev/null"
opspectre shell "cat /workspace/output/web-audit/wpscan.txt 2>/dev/null"
opspectre shell "cat /workspace/output/web-audit/dalfox-xss.txt 2>/dev/null"
opspectre shell "cat /workspace/output/web-audit/wapiti-results.txt 2>/dev/null"
opspectre shell "cat /workspace/output/web-audit/zap-baseline.html 2>/dev/null"
opspectre shell "cat /workspace/output/container-audit/critical.txt 2>/dev/null"
```

## Step 4: Collect WordPress Findings

```bash
opspectre shell "cat /workspace/output/wordpress/wpscan-full.txt 2>/dev/null"
opspectre shell "cat /workspace/output/wordpress/wp-rest-users.txt 2>/dev/null"
opspectre shell "cat /workspace/output/wordpress/wp-sensitive-files.txt 2>/dev/null"
opspectre shell "cat /workspace/output/wordpress/xmlrpc-methods.txt 2>/dev/null"
```

## Step 5: Collect Exploitation Results

```bash
opspectre shell "ls -la /workspace/output/loot/ 2>/dev/null"
opspectre shell "ls -la /workspace/output/exploits/ 2>/dev/null"
```

## Step 6: Collect Secret Findings

```bash
opspectre shell "cat /workspace/output/secrets/trufflehog-fs.json 2>/dev/null"
opspectre shell "cat /workspace/output/secrets/private-keys.txt 2>/dev/null"
```

## Step 7: Generate PDF Report

After writing the markdown report to `/workspace/output/report/report.md`:

### Convert to PDF
```bash
opspectre shell "cd /workspace/output/report && \
  pandoc report.md -o report.pdf \
    --pdf-engine=xelatex \
    -V geometry:margin=1in \
    -V fontsize=11pt \
    -V documentclass=article \
    -V colorlinks=true \
    -V linkcolor=blue \
    -V urlcolor=blue \
    -V toccolor=gray \
    --toc \
    --toc-depth=3 \
    --highlight-style=tango \
    -V header-includes='\\usepackage{fancyhdr}\\pagestyle{fancy}\\fancyhead[L]{CONFIDENTIAL}\\fancyhead[R]{OperationSpectre}' \
    2>&1 && echo 'PDF generated successfully'"
```

### Convert to HTML (alternative)
```bash
opspectre shell "cd /workspace/output/report && \
  pandoc report.md -o report.html \
    --standalone \
    --metadata title='Penetration Test Report' \
    --toc \
    --toc-depth=3 \
    -c https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown.min.css \
    2>&1 && echo 'HTML report generated successfully'"
```

### Convert to DOCX (alternative)
```bash
opspectre shell "cd /workspace/output/report && \
  pandoc report.md -o report.docx \
    --toc \
    --toc-depth=3 \
    --reference-doc=/usr/share/pandoc/data/templates/reference.docx 2>/dev/null || \
  pandoc report.md -o report.docx --toc && echo 'DOCX report generated successfully'"
```

## Report Template

After collecting all data, generate a report using this structure:

```markdown
# Penetration Test Report

## Engagement Details

| Field | Value |
|-------|-------|
| **Client** | [CLIENT NAME] |
| **Target** | [TARGET(S)] |
| **Scope** | [IN-SCOPE ASSETS] |
| **Date** | [START DATE] - [END DATE] |
| **Tester** | OperationSpectre Automated Pentest Platform |
| **Classification** | CONFIDENTIAL |

## Executive Summary

[2-3 paragraph overview of findings, risk posture, and key recommendations]

## Methodology

Testing was conducted following the PTES (Penetration Testing Execution Standard)
methodology using the OperationSpectre sandbox environment.

### Tools Used
- Passive OSINT: crt.sh, gau, waybackurls, Google dorks, Shodan/Censys
- Network Scanning: nmap, naabu
- Web Testing: OWASP ZAP, Burp Suite, ffuf, gobuster, sqlmap, dalfox
- WordPress: wpscan, WP REST API enumeration
- Vulnerability Scanning: nuclei, wapiti
- Visual Recon: gowitness
- Subdomain Takeover: subjack
- JavaScript Analysis: JS-Snooper, jsniper
- Exploitation: Metasploit, hydra, crackmapexec
- Secret Scanning: trufflehog
- Container Security: trivy

## Findings Summary

| # | Finding | Severity | Status | CVSS |
|---|---------|----------|--------|------|
| 1 | [Finding Name] | Critical | Confirmed | 9.8 |
| 2 | [Finding Name] | High | Confirmed | 8.1 |
| 3 | [Finding Name] | Medium | Potential | 6.5 |

### Severity Breakdown

- **Critical**: X findings
- **High**: X findings
- **Medium**: X findings
- **Low**: X findings
- **Informational**: X findings

## Detailed Findings

### [FINDING-001]: [Finding Title]

**Severity:** Critical | **CVSS:** X.X | **Status:** Confirmed

**Description:**
[Detailed description of the vulnerability]

**Impact:**
[Potential business impact]

**Evidence:**
```
[Paste relevant scan output, screenshots referenced]
```

**Remediation:**
[Specific steps to fix]

**References:**
- [CVE or CWE link]

---

[Repeat for each finding]

## Reconnaissance Results

### Network Map
[Ports, services, and OS detection from nmap]

### Subdomains
[Discovered via subfinder + Certificate Transparency]

### Web Assets
[Discovered URLs from gau, katana, waybackurls]

### Technology Stack
[From whatweb, webtech, httpx]

### Screenshots
[Reference gowitness screenshots directory]

### DNS & Domain Info
[DNS records, domain registration details]

## Compliance Mapping (if applicable)

| Finding | HIPAA | PCI-DSS | SOC2 | NIST |
|---------|-------|---------|------|------|
| DB exposed | §164.312(e) | Req 1.3.6 | CC6.1 | SC-7 |
| [Finding] | [Section] | [Req] | [Control] | [Control] |

## Recommendations

### Immediate (Critical/High)
1. [Priority fix 1]
2. [Priority fix 2]

### Short-term (Medium)
1. [Fix within 30 days]

### Long-term (Low/Info)
1. [Improvement suggestions]

## Appendix

### A. Raw Scan Outputs
[Bundled scan files]

### B. Tool Versions
[Burp Suite, nmap, nuclei template versions]

### C. Scope
[Exact in-scope and out-of-scope assets]
```

## Writing the Report

1. Read all scan outputs from `/workspace/output/`
2. Classify each finding by severity (use CVSS scoring)
3. Deduplicate findings across tools
4. Write clear descriptions, impacts, and remediation steps
5. Save the report to `/workspace/output/report/`
6. Convert to PDF using pandoc

```bash
opspectre shell "mkdir -p /workspace/output/report"
```

## Tips

- Always de-duplicate findings (nuclei and ZAP often overlap)
- Prioritize findings that can be chained for greater impact
- Include specific CVEs when available from nuclei/trivy output
- Reference the exact file paths in evidence sections
- Save the final report as `.md` AND `.pdf` (use pandoc for conversion)
- Include gowitness screenshot references for visual evidence
- Map findings to compliance frameworks (HIPAA, PCI-DSS, SOC2, NIST) when relevant
- Include OSINT findings in the recon section
- Note any WAF/rate-limit blocks that prevented deeper testing
