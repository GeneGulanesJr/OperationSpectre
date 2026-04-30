---
name: passive-osint
description: Purely passive reconnaissance using OSINT techniques — Certificate Transparency, Wayback Machine, CommonCrawl, Google dorks, Shodan queries, and GitHub dorking. No direct contact with target. Use when beginning recon or when WAF blocks active scanning.
---

# Passive OSINT Reconnaissance

Purely passive reconnaissance that never touches the target directly. Uses third-party data sources, historical archives, and public records. Essential as a first step before active scanning, and as a fallback when WAFs/rate-limits block active tools.

## Prerequisites

- OperationSpectre sandbox running
- Internet access from container
- Tools: curl, jq, gau, waybackurls (all pre-installed)

## Why Passive First?

1. **No WAF triggers** — passive techniques query third-party sources, not the target
2. **Historical data** — find URLs, subdomains, and pages that may no longer be active
3. **Broader coverage** — aggregate data from multiple sources over years
4. **Fast** — no waiting for rate limits or connection timeouts

## Step 1: Certificate Transparency (crt.sh)

Finds all SSL certificates ever issued for the domain — reveals subdomains that may not resolve via DNS.

```bash
opspectre shell "osint_ct_subdomains <DOMAIN>"
```

**Manual alternative:**
```bash
opspectre shell "curl -s 'https://crt.sh/?q=%25.<DOMAIN>&output=json' | jq -r '.[].name_value' | sort -u"
```

## Step 2: Historical URLs (Wayback Machine + CommonCrawl)

Finds URLs archived over years — reveals old pages, API endpoints, admin panels, and forgotten content.

```bash
opspectre shell "osint_wayback_urls <DOMAIN>"
```

**Individual tools:**
```bash
# Wayback Machine only
opspectre shell "echo <DOMAIN> | waybackurls > /workspace/output/osint/wayback-urls.txt"

# All sources (Wayback + CommonCrawl + AlienVault OTX)
opspectre shell "gau --subs <DOMAIN> > /workspace/output/osint/gau-urls.txt"
```

**Extract juicy endpoints from URL lists:**
```bash
opspectre shell "cat /workspace/output/osint/gau-urls.txt | grep -iE 'admin|api|login|backup|config|debug|test|staging|dev|internal|private|upload|wp-' | sort -u"
```

## Step 3: Google Dork Queries

Generates targeted Google search queries. Execute these manually or automate with an API.

```bash
opspectre shell "osint_google_dorks <DOMAIN>"
```

**Quick manual checks:**
```bash
# Check for exposed files
opspectre shell "curl -s 'https://www.google.com/search?q=site:<DOMAIN>+filetype:pdf' -H 'User-Agent: Mozilla/5.0' | grep -oP 'https?://[^\"<>]+' | head -20"
```

## Step 4: Shodan / Censys Queries

Generates queries for IoT/host search engines. Execute manually at Shodan/Censys web interfaces.

```bash
opspectre shell "osint_shodan_queries <DOMAIN> [IP]"
```

## Step 5: GitHub Dorking

Generates queries for finding leaked secrets, credentials, and config files in GitHub repos.

```bash
opspectre shell "osint_github_dorks <ORG_OR_USERNAME>"
```

## Step 6: SecurityTrails / Historical DNS

View DNS history, historical IPs, and related domains.

```bash
opspectre shell "osint_securitytrails <DOMAIN>"
```

**Manual WHOIS + DNS:**
```bash
opspectre shell "whois <DOMAIN> > /workspace/output/osint/whois.txt"
opspectre shell "dig <DOMAIN> ANY +noall +answer > /workspace/output/osint/dns-records.txt"
```

## Step 7: Email Harvesting

Find email addresses associated with the target.

```bash
opspectre shell "osint_ct_subdomains <DOMAIN> && \
  theHarvester -d <DOMAIN> -b google,bing,linkedin,twitter -l 50 > /workspace/output/osint/emails.txt 2>/dev/null || \
  echo 'Emails from CT subdomains:' && \
  cat /workspace/output/osint/ct-subdomains.txt"
```

## Full Passive Pipeline

Run everything in one shot:

```bash
opspectre run "mkdir -p /workspace/output/osint && \
  osint_full_passive <DOMAIN>"
```

**Or manually:**
```bash
opspectre run "mkdir -p /workspace/output/osint && \
  osint_ct_subdomains <DOMAIN> && \
  osint_wayback_urls <DOMAIN> && \
  osint_google_dorks <DOMAIN> && \
  osint_shodan_queries <DOMAIN> && \
  osint_github_dorks <DOMAIN>"
```

## Chaining with Active Recon

Passive OSINT feeds into active recon:

```bash
# 1. Get CT subdomains + passive URLs
opspectre shell "osint_full_passive <DOMAIN>"

# 2. Merge CT subdomains with subfinder results
opspectre shell "cat /workspace/output/osint/ct-subdomains.txt /workspace/output/recon/subdomains.txt | sort -u > /workspace/output/recon/all-subdomains.txt"

# 3. Probe all subdomains
opspectre shell "httpx -l /workspace/output/recon/all-subdomains.txt -status-code -title -tech-detect -o /workspace/output/recon/live-hosts.txt"

# 4. Screenshot all live hosts
opspectre shell "cat /workspace/output/recon/live-hosts.txt | grep -oE 'https?://[^ ]+' | gowitness file - -P /workspace/output/osint/screenshots/"

# 5. Feed passive URLs into nuclei for vulnerability scanning
opspectre shell "cat /workspace/output/osint/gau-urls.txt | httpx -silent | nuclei -rl 10 -severity high,critical -o /workspace/output/osint/nuclei-passive.txt"
```

## Output Locations

All results under `/workspace/output/osint/`:
- `ct-subdomains.txt` — Certificate Transparency subdomains
- `wayback-urls.txt` — Wayback Machine URLs
- `gau-urls.txt` — All archived URLs (Wayback + CommonCrawl + OTX)
- `dorks.txt` — Google dork queries
- `shodan-queries.txt` — Shodan/Censys queries
- `github-dorks.txt` — GitHub dork queries
- `emails.txt` — Harvested email addresses
- `whois.txt` — WHOIS registration data
- `dns-records.txt` — DNS records
- `screenshots/` — gowitness screenshots of live hosts

## Tips

- Passive OSINT is always safe to run — it never contacts the target
- Run this BEFORE active recon to build a comprehensive target list
- Merge CT subdomains with subfinder results for maximum coverage
- Filter gau URLs for juicy keywords: admin, api, login, backup, config, debug
- Save dork queries — they can be re-run over time for new findings
- GitHub dorking often finds the most critical secrets (API keys, DB creds)
- Use gowitness screenshots to verify what each subdomain actually hosts
