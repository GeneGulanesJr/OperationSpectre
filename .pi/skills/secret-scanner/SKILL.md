---
name: secret-scanner
description: Scans codebases, containers, and repositories for leaked secrets, API keys, and credentials using trufflehog, trivy, grep patterns, and theHarvester in the opspectre sandbox. Use when reviewing code for secret leaks or post-exploitation credential harvesting.
---

# Secret Scanner

Finds leaked secrets, API keys, tokens, passwords, and credentials in codebases, containers, and repositories using trufflehog, trivy, and custom pattern matching in the OperationSpectre sandbox.

## Prerequisites

- OperationSpectre sandbox running (`opspectre sandbox start`)
- Target repository cloned into `/workspace/` or accessible path

## Rate-Limit Defaults

Not typically needed for local scanning, but available for remote repo scanning:
```bash
$RL_NUCLEI  # nuclei: -rl 15 -bs 25 -c 5 -timeout 15 -retries 2
$RL_HTTPX   # httpx: -rate-limit 5 -timeout 15 -retries 2
random_ua   # Returns a random User-Agent string
```

## Scanning with Trufflehog

### Scan a Git Repository (Full History)
```bash
opspectre shell "trufflehog git https://github.com/<ORG>/<REPO>.git --json > /workspace/output/secrets/trufflehog-full.json"
```

### Scan a Local Directory
```bash
opspectre shell "trufflehog filesystem /workspace/source/ --json > /workspace/output/secrets/trufflehog-fs.json"
```

### Scan with Specific Rules
```bash
opspectre shell "trufflehog filesystem /workspace/source/ --include-patterns='*.env,*.yaml,*.json,*.conf,*.cfg' --json > /workspace/output/secrets/trufflehog-configs.json"
```

### Scan Git History Only (No Branches)
```bash
opspectre shell "trufflehog git https://github.com/<ORG>/<REPO>.git --no-update --json > /workspace/output/secrets/trufflehog-history.json"
```

### Scan Docker Image for Secrets
```bash
opspectre shell "trufflehog image <IMAGE_NAME> --json > /workspace/output/secrets/trufflehog-image.json"
```

### Scan with Updated Rules
```bash
opspectre shell "trufflehog filesystem /workspace/source/ --update --json > /workspace/output/secrets/trufflehog-updated.json"
```

## Trivy Secret Scanning

### Scan Container Image
```bash
opspectre shell "trivy image <IMAGE_NAME> --scanners secret -o /workspace/output/secrets/trivy-image-secrets.txt"
```

### Scan Filesystem
```bash
opspectre shell "trivy fs /workspace/source/ --scanners secret -o /workspace/output/secrets/trivy-fs-secrets.txt"
```

### Scan Git Repository
```bash
opspectre shell "trivy repo https://github.com/<ORG>/<REPO>.git --scanners secret -o /workspace/output/secrets/trivy-repo-secrets.txt"
```

## Pattern-Based Scanning (grep)

### Common Secret Patterns
```bash
opspectre shell "mkdir -p /workspace/output/secrets"

# AWS Access Keys
opspectre shell "grep -rn 'AKIA[0-9A-Z]{16}' /workspace/source/ > /workspace/output/secrets/aws-keys.txt 2>/dev/null"

# AWS Secret Keys
opspectre shell "grep -rn 'AWS_SECRET_ACCESS_KEY\s*[=:]\s*['\\''\"]\\?[A-Za-z0-9/+=]{40}' /workspace/source/ > /workspace/output/secrets/aws-secret-keys.txt 2>/dev/null"

# GitHub Tokens (classic + fine-grained)
opspectre shell "grep -rn -E 'gh[pousr]_[A-Za-z0-9_]{36,}|github_pat_[A-Za-z0-9_]{82,}' /workspace/source/ > /workspace/output/secrets/github-tokens.txt 2>/dev/null"

# GitLab Tokens
opspectre shell "grep -rn 'glpat-[A-Za-z0-9_-]{20,}' /workspace/source/ > /workspace/output/secrets/gitlab-tokens.txt 2>/dev/null"

# Slack Tokens
opspectre shell "grep -rn 'xox[baprs]-[A-Za-z0-9-]{10,}' /workspace/source/ > /workspace/output/secrets/slack-tokens.txt 2>/dev/null"

# Generic API Keys
opspectre shell "grep -rn -i 'api_key\\s*[=:].*['\\''\"]\\?[A-Za-z0-9]{20,}' /workspace/source/ > /workspace/output/secrets/api-keys.txt 2>/dev/null"

# Private Keys
opspectre shell "grep -rn '-----BEGIN.*PRIVATE KEY-----' /workspace/source/ > /workspace/output/secrets/private-keys.txt 2>/dev/null"

# Passwords in Config
opspectre shell "grep -rn -i 'password\\s*[=:].*['\\''\"]\\?[A-Za-z0-9@#$%^&*]{8,}' /workspace/source/ > /workspace/output/secrets/passwords.txt 2>/dev/null"

# Connection Strings
opspectre shell "grep -rn -i 'mongodb\\+srv://\\|postgres://\\|mysql://\\|redis://.*:.*@' /workspace/source/ > /workspace/output/secrets/connection-strings.txt 2>/dev/null"

# JWT Secrets
opspectre shell "grep -rn -i 'jwt_secret\\|JWT_SECRET\\|token_secret\\|TOKEN_SECRET' /workspace/source/ > /workspace/output/secrets/jwt-secrets.txt 2>/dev/null"

# Stripe API Keys
opspectre shell "grep -rn -E 'sk_live_[A-Za-z0-9]{24,}|pk_live_[A-Za-z0-9]{24,}' /workspace/source/ > /workspace/output/secrets/stripe-keys.txt 2>/dev/null"

# SendGrid API Keys
opspectre shell "grep -rn 'SG\\.[A-Za-z0-9_-]{22}\\.[A-Za-z0-9_-]{43}' /workspace/source/ > /workspace/output/secrets/sendgrid-keys.txt 2>/dev/null"

# Twilio Account SID
opspectre shell "grep -rn 'AC[a-f0-9]{32}' /workspace/source/ > /workspace/output/secrets/twilio-keys.txt 2>/dev/null"

# Azure Credentials
opspectre shell "grep -rn -E 'DEFAULTS\\s*=\\s*\\{[^}]*client_id[^}]*\\}|azure.*client_secret' /workspace/source/ > /workspace/output/secrets/azure-creds.txt 2>/dev/null"

# Google Cloud Service Account Keys
opspectre shell "grep -rn 'type.*service_account' /workspace/source/ > /workspace/output/secrets/gcp-sa-keys.txt 2>/dev/null"

# npm/pip tokens
opspectre shell "grep -rn -E '//registry\.npmjs\.org/:_authToken=|//npm\.pkg\.github\.com/:_authToken=' /workspace/source/ > /workspace/output/secrets/npm-tokens.txt 2>/dev/null"
```

## Ripgrep Deep Scan

```bash
# Search for entropy-rich strings (potential secrets)
opspectre shell "rg -i 'secret|token|key|password|credential|auth' /workspace/source/ -g '!node_modules' -g '!.git' > /workspace/output/secrets/keyword-scan.txt"

# Search env files specifically
opspectre shell "find /workspace/source/ -name '.env*' -exec cat {} \\; > /workspace/output/secrets/env-dump.txt 2>/dev/null"

# Search for hardcoded IPs
opspectre shell "rg '\\b([0-9]{1,3}\\.){3}[0-9]{1,3}\\b' /workspace/source/ -g '!node_modules' > /workspace/output/secrets/hardcoded-ips.txt"

# Search for hardcoded domains/URLs with credentials
opspectre shell "rg -E 'https?://[^:]+:[^@]+@' /workspace/source/ -g '!node_modules' > /workspace/output/secrets/cred-urls.txt"

# Search for base64 encoded secrets
opspectre shell "rg -E 'eyJ[A-Za-z0-9+/=]{20,}' /workspace/source/ -g '!node_modules' > /workspace/output/secrets/base64-strings.txt"
```

## Email Harvesting (theHarvester)

Find email addresses and subdomains associated with a target domain:

```bash
# Full harvest from multiple sources
opspectre shell "theHarvester -d <DOMAIN> -b google,bing,linkedin,twitter,github -l 100 > /workspace/output/secrets/theharvester.txt 2>/dev/null"

# GitHub only
opspectre shell "theHarvester -d <DOMAIN> -b github -l 50 >> /workspace/output/secrets/theharvester.txt 2>/dev/null"

# Extract just emails
opspectre shell "grep -oE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' /workspace/output/secrets/theharvester.txt | sort -u > /workspace/output/secrets/emails.txt"
```

## GitHub Secret Scanning (GitHub Dorking)

### Generate GitHub Dork Queries
```bash
opspectre shell "osint_github_dorks <ORG_OR_USERNAME>"
```

### Manual GitHub Dorks
```bash
# Search for .env files
opspectre shell "curl -s 'https://api.github.com/search/code?q=filename:.env+org:<ORG>' -H 'Accept: application/vnd.github.v3+json' 2>/dev/null | python3 -m json.tool > /workspace/output/secrets/github-env-files.json"

# Search for API keys in code
opspectre shell "curl -s 'https://api.github.com/search/code?q=api_key+org:<ORG>' -H 'Accept: application/vnd.github.v3+json' 2>/dev/null | python3 -m json.tool > /workspace/output/secrets/github-api-keys.json"

# Search for credentials in repos
opspectre shell "curl -s 'https://api.github.com/search/code?q=password+extension:yml+org:<ORG>' -H 'Accept: application/vnd.github.v3+json' 2>/dev/null | python3 -m json.tool > /workspace/output/secrets/github-yml-passwords.json"
```

## JWT Token Analysis

```bash
# Decode and analyze a JWT token
opspectre shell "jwt_tool <JWT_TOKEN> > /workspace/output/secrets/jwt-analysis.txt"

# Crack JWT secret
opspectre shell "jwt_tool <JWT_TOKEN> -C -d /usr/share/wordlists/rockyou.txt > /workspace/output/secrets/jwt-crack.txt"
```

## Post-Exploitation Credential Harvesting

### Extract Passwords from Config Files
```bash
opspectre shell "find /workspace/loot/ -type f \\( -name '*.conf' -o -name '*.cfg' -o -name '*.yml' -o -name '*.yaml' -o -name '*.ini' -o -name '*.properties' -o -name '*.xml' -o -name '*.json' \\) -exec grep -l -i 'password\\|secret\\|token\\|key' {} \\; 2>/dev/null > /workspace/output/secrets/loot-configs-with-passwords.txt"
```

### Extract from Database Dumps
```bash
opspectre shell "grep -rn -i 'password\\|passwd\\|pwd' /workspace/loot/*.sql 2>/dev/null | head -50 > /workspace/output/secrets/db-passwords.txt"
```

### Check for Credential Files
```bash
opspectre shell "find /workspace/loot/ -type f \\( -name '*.txt' -o -name '*.csv' -o -name '*.xlsx' \\) -exec file {} \\; | grep -i 'text\\|csv' | awk '{print \$1}' | xargs grep -l -i 'password\\|email\\|username\\|login' 2>/dev/null > /workspace/output/secrets/loot-cred-files.txt"
```

## Output Locations

All results under `/workspace/output/secrets/`:
- `trufflehog-full.json` — trufflehog full history scan
- `trufflehog-fs.json` — trufflehog filesystem scan
- `trufflehog-image.json` — trufflehog image scan
- `trivy-image-secrets.txt` / `trivy-fs-secrets.txt` — trivy secret scan
- `aws-keys.txt` / `aws-secret-keys.txt` — AWS access/secret keys
- `github-tokens.txt` — GitHub token matches
- `gitlab-tokens.txt` — GitLab token matches
- `slack-tokens.txt` — Slack token matches
- `stripe-keys.txt` — Stripe live keys
- `sendgrid-keys.txt` — SendGrid API keys
- `twilio-keys.txt` — Twilio account SIDs
- `azure-creds.txt` — Azure credentials
- `gcp-sa-keys.txt` — Google Cloud service account keys
- `npm-tokens.txt` — npm/pip registry tokens
- `api-keys.txt` — generic API key matches
- `private-keys.txt` — private key file matches
- `passwords.txt` — password in config matches
- `connection-strings.txt` — database connection strings
- `jwt-secrets.txt` — JWT signing secrets
- `cred-urls.txt` — URLs with embedded credentials
- `base64-strings.txt` — base64-encoded strings
- `keyword-scan.txt` — keyword-based search results
- `env-dump.txt` — contents of all .env files
- `theharvester.txt` — email/subdomain harvest results
- `emails.txt` — extracted email addresses
- `github-env-files.json` — GitHub .env file search
- `jwt-analysis.txt` / `jwt-crack.txt` — JWT analysis

## Quick Full Scan

```bash
opspectre run "mkdir -p /workspace/output/secrets && \
  trufflehog filesystem /workspace/source/ --json > /workspace/output/secrets/trufflehog.json && \
  trivy fs /workspace/source/ --scanners secret -o /workspace/output/secrets/trivy-secrets.txt 2>/dev/null && \
  rg -i 'secret|token|key|password|credential|auth' /workspace/source/ -g '!node_modules' -g '!.git' > /workspace/output/secrets/keyword-scan.txt && \
  grep -rn '-----BEGIN.*PRIVATE KEY-----' /workspace/source/ > /workspace/output/secrets/private-keys.txt 2>/dev/null && \
  find /workspace/source/ -name '.env*' -exec cat {} \\; > /workspace/output/secrets/env-dump.txt 2>/dev/null"
```

## Chaining with Other Skills

| After secret-scanner... | Use this skill | Why |
|--------------------------|---------------|-----|
| Found DB credentials | `exploit-dev` | Attempt database login |
| Found API keys | `web-app-audit` | Test API endpoints with found keys |
| Found container secrets | `container-audit` | Cross-reference with image scan |
| Found WordPress creds | `wordpress-audit` | Test WP login |
| Collected all findings | `report-generator` | Include secrets in final report |

## Tips

- Exclude known safe directories: `-g '!node_modules' -g '!.git' -g '!vendor' -g '!__pycache__'`
- For GitHub repos, use the `git` scanner to catch secrets in history (even if deleted)
- Cross-reference trufflehog findings with keyword grep to reduce false positives
- Always verify findings before reporting — some patterns have high false positive rates
- trufflehog + trivy together provide the best coverage (different rule sets)
- Check `.env.example` files too — they often contain real secrets that were copied from `.env`
- Search for base64-encoded strings and decode them (many devs "hide" secrets this way)
- After exploitation, always harvest configs and DB dumps for additional credentials
- Use GitHub dorking for OSINT — finds secrets in public repos linked to the target
- Combine with `theHarvester` for email → password reuse attacks
- For container images, scan both with trufflehog and trivy (different secret patterns)
