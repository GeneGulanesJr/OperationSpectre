# Web Application Audit Guide

The web-app-audit skill provides comprehensive security scanning for web applications using industry-standard tools.

## Architecture Integration

### CLI Mode (Traditional)
```bash
# Manual web app auditing
opspectre web-app-audit <target-url>
opspectre web-app-audit -t sqlmap <url>
opspectre web-app-audit -t burp <url>
opspectre web-app-audit -t zap <url>
opspectre web-app-audit -t ffuf <url>
```

## Available Tools

- **Burp Suite** - Professional vulnerability scanner with automated and manual capabilities
- **OWASP ZAP** - Free web application security scanner
- **SQLMap** - Automated SQL injection tool
- **FFUF** - Fast web fuzzer
- **Nuclei** - Template-based vulnerability scanner
- **Wappalyzer** - Technology stack identification

# Technology stack identification
opspectre web-app-audit -t wappalyzer <url>

# Template-based vulnerability scanning
opspectre web-app-audit -t nuclei <url>
```

## Scan Types

### Burp Suite (`-t burp`)
Automated scan using Burp Suite Professional's scanner:
- Sensitive data leakage
- Session fixation
- CSRF attacks
- Cross-site scripting (XSS)
- Directory traversal
- And many more OWASP Top 10 vulnerabilities

### SQLMap (`-t sqlmap`)
Targeted SQL injection detection:
- Time-based blind injection
- Boolean-based blind injection  
- Error-based injection
- Union-based injection
- Stack-based blind injection

### FFUF Fuzzing (`-t ffuf`)
Path and parameter discovery:
- Hidden directories/files
- Virtual paths
- Parameter enumeration
- Sensitive file discovery (`.env`, `.gitconfig`, etc.)

### OWASP ZAP (`-t zap`)
Automated security scanning via OWASP ZAP proxy:
- Full spider and attack scans
- Passive rule checking
- Active scanner rules
- CSRF testing

### Nuclei (`-t nuclei`)
Template-based vulnerability detection:
- CVE matching
- Misconfiguration checks
- Technology version identification
- Exposed sensitive data

## Output Format

All scan results are output to standardized format and saved in `/home/genegulanesjr/Documents/GulanesKorp/OperationSpectre/output/web-app-audit/`:

```
/home/genegulanesjr/Documents/GulanesKorp/OperationSpectre/output/web-app-audit/
├── full-scan-report.md     # Complete scan report
├── burp-results.txt        # Burp Suite results
├── zap-results.xml         # OWASP ZAP XML output  
├── sqlmap-results.txt      # SQLMap output
└── ffuf-output.txt         # FFUF fuzzer results
```

## Remediation Guidance

After scanning, use the `report-generator` skill to:
1. Review findings with remediation steps
2. Generate PDF reports for stakeholders  
3. Export scan metrics and statistics

See `/home/genegulanesjr/Documents/GulanesKorp/OperationSpectre/docs/FULL_ARSENAL_README.md` for complete tool documentation.
