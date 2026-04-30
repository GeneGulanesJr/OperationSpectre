---
name: web-app-audit
description: Full-stack web application security testing using Burp Suite, OWASP ZAP, sqlmap, ffuf, and additional tools from the opspectre sandbox.
location: /home/genegulanesjr/Documents/GulanesKorp/OperationSpectre/.pi/skills/web-app-audit/SKILL.md
---

# web-app-audit — Web Application Security Testing

**What it is**: Full-stack web application security testing using Burp Suite, OWASP ZAP, sqlmap, ffuf, and additional tools from the opspectre sandbox.

**When to use it**: Use when auditing web applications, whether you need a full pentest or targeted vulnerability discovery.

## Usage
```bash
# Basic web audit (full scan)
opspectre web-app-audit <target-url>

# Targeted attack types:
opspectre web-app-audit -t sqlmap <url>      # SQL injection
opspectre web-app-audit -t burp <url>         # Burp Suite scan
opspectre web-app-audit -t zap <url>          # OWASP ZAP scan
```

## Key Features
- Automated vulnerability scanning with multiple tools
- Targeted attack type selection (sqlmap, burp, zap)
- Full report generation with remediation steps

**See the full docs at:** /home/genegulanesjr/Documents/GulanesKorp/OperationSpectre/docs/web-app-audit.md or `opspectre web-app-audit --help` for command details.