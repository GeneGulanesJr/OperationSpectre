#!/bin/bash
# ============================================================
# OSINT PLAYBOOK — Passive Reconnaissance
# Purely passive techniques that don't trigger WAFs
# ============================================================
# LOCATION: /opt/playbooks/osint-playbook.sh
# USAGE: source /opt/playbooks/osint-playbook.sh
# ============================================================

source /opt/playbooks/scan-helpers.sh

export OSINT_OUTPUT_DIR="/workspace/output/osint"
mkdir -p "$OSINT_OUTPUT_DIR"

# ============================================================
# CERTIFICATE TRANSPARENCY (crt.sh)
# ============================================================
osint_ct_subdomains() {
    local domain="$1"
    if [ -z "$domain" ]; then
        echo "[OSINT-CT] Usage: osint_ct_subdomains <domain>"
        return 1
    fi
    local outdir=$(scan_dir "OSINT-CT" "https://$domain")
    mkdir -p "$outdir"
    local outfile="$outdir/ct-subdomains.txt"

    echo "[OSINT-CT] Querying crt.sh for $domain..."
    curl -s "https://crt.sh/?q=%25.$domain&output=json" 2>/dev/null | \
        jq -r '.[].name_value' 2>/dev/null | \
        sort -u > "$outfile"

    # Clean up wildcard entries
    sed -i 's/^\*\.//' "$outfile"
    sort -u -o "$outfile"

    echo "[OSINT-CT] Found $(wc -l < "$outfile") subdomains via Certificate Transparency"
    echo "[OSINT-CT] Results: $outfile"
}

# ============================================================
# WAYBACK MACHINE / COMMONCRAWL (gau + waybackurls)
# ============================================================
osint_wayback_urls() {
    local domain="$1"
    if [ -z "$domain" ]; then
        echo "[OSINT-WAYBACK] Usage: osint_wayback_urls <domain>"
        return 1
    fi
    local outdir=$(scan_dir "OSINT-Wayback" "https://$domain")
    mkdir -p "$outdir"

    echo "[OSINT-WAYBACK] Collecting URLs from Wayback Machine & CommonCrawl..."

    # waybackurls
    echo "$domain" | waybackurls 2>/dev/null > "$outdir/waybackurls.txt" || true

    # gau (GetAllUrls) — Wayback + CommonCrawl + AlienVault
    gau --subs "$domain" 2>/dev/null > "$outdir/gau-urls.txt" || true

    # Merge and deduplicate
    cat "$outdir/waybackurls.txt" "$outdir/gau-urls.txt" 2>/dev/null | \
        sort -u > "$outdir/all-urls.txt"

    echo "[OSINT-WAYBACK] Found $(wc -l < "$outdir/all-urls.txt") unique URLs"
    echo "[OSINT-WAYBACK] Results: $outdir"
}

# ============================================================
# GOOGLE DORKING (requires manual review)
# ============================================================
osint_google_dorks() {
    local domain="$1"
    if [ -z "$domain" ]; then
        echo "[OSINT-GOOGLE] Usage: osint_google_dorks <domain>"
        return 1
    fi
    local outdir=$(scan_dir "OSINT-Google" "https://$domain")
    mkdir -p "$outdir"
    local outfile="$outdir/dorks.txt"

    echo "[OSINT-GOOGLE] Generating Google dork queries for $domain..."

    cat > "$outfile" << DORKS
# Google Dorks for $domain
# Execute these manually at https://google.com

# Sensitive files
site:$domain filetype:pdf
site:$domain filetype:doc
site:$domain filetype:xls
site:$domain filetype:txt
site:$domain filetype:log
site:$domain filetype:sql
site:$domain filetype:conf
site:$domain filetype:bak
site:$domain filetype:env

# Directories
site:$domain intitle:"index of"
site:$domain inurl:/admin/
site:$domain inurl:/backup/
site:$domain inurl:/config/
site:$domain inurl:/.git
site:$domain inurl:/.env
site:$domain inurl:/wp-admin

# Login/portal pages
site:$domain inurl:login
site:$domain inurl:portal
site:$domain inurl:dashboard
site:$domain inurl:admin

# Exposed documents
site:$domain intitle:"confidential"
site:$domain intitle:"internal"
site:$domain intitle:"password"
site:$domain inurl:"api_key"
site:$domain inurl:"secret"

# Error pages (info disclosure)
site:$domain "sql syntax" "error"
site:$domain "stack trace"
site:$domain "debug"
site:$domain "Warning:" "mysql"

# Technology fingerprinting
site:$domain "powered by" "wordpress"
site:$domain "powered by" "apache"
site:$domain inurl:"wp-content"
DORKS

    echo "[OSINT-GOOGLE] Generated $(grep -c '^site:' "$outfile") dork queries"
    echo "[OSINT-GOOGLE] Results: $outfile"
}

# ============================================================
# SHODAN / CENSYS QUERY GENERATOR
# ============================================================
osint_shodan_queries() {
    local domain="$1"
    local ip="${2:-}"
    if [ -z "$domain" ]; then
        echo "[OSINT-SHODAN] Usage: osint_shodan_queries <domain> [ip]"
        return 1
    fi
    local outdir=$(scan_dir "OSINT-Shodan" "https://$domain")
    mkdir -p "$outdir"
    local outfile="$outdir/shodan-queries.txt"

    echo "[OSINT-SHODAN] Generating Shodan/Censys queries for $domain..."

    cat > "$outfile" << QUERIES
# Shodan Queries for $domain
# Execute at: https://www.shodan.io/search?query=

hostname:$domain
ssl.cert.subject.cn:$domain
http.title:"$domain"
org:"$domain"
net:$domain

# Censys Queries for $domain
# Execute at: https://search.censys.io/search?resource=hosts&sort=RELEVANCE&per_page=25&virtual_hosts=EXCLUDE&q=

services.tls.certificate.parsed.names: $domain
dns.names: $domain
http.response.headers.server: "$domain"
QUERIES

    echo "[OSINT-SHODAN] Results: $outfile"
}

# ============================================================
# SECURITY TRAILS / HISTORICAL DNS
# ============================================================
osint_securitytrails() {
    local domain="$1"
    if [ -z "$domain" ]; then
        echo "[OSINT-TRAILS] Usage: osint_securitytrails <domain>"
        return 1
    fi
    echo "[OSINT-TRAILS] SecurityTrails API lookup for $domain..."
    echo "[OSINT-TRAILS] Visit: https://securitytrails.com/domain/$domain/dns"
    echo "[OSINT-TRAILS] Or use API: curl -s 'https://api.securitytrails.com/v1/domain/$domain/dns/history'"
}

# ============================================================
# GITHUB DORKING
# ============================================================
osint_github_dorks() {
    local org="$1"
    if [ -z "$org" ]; then
        echo "[OSINT-GITHUB] Usage: osint_github_dorks <org_or_user>"
        return 1
    fi
    local outdir=$(scan_dir "OSINT-GitHub" "https://github.com/$org")
    mkdir -p "$outdir"
    local outfile="$outdir/github-dorks.txt"

    cat > "$outfile" << GITHUBDORKS
# GitHub Dorks for $org
# Execute at: https://github.com/search?q=<query>

# API keys & secrets
org:$org password
org:$org api_key
org:$org secret_key
org:$org aws_access_key
org:$org private_key
org:$org .env
org:$org database_url
org:$org mongodb
org:$org postgres
org:$org jdbc

# Config files
org:$org filename:.env
org:$org filename:wp-config.php
org:$org filename:config.php
org:$org filename:id_rsa
org:$org filename:.htpasswd
org:$org filename:credentials
org:$org filename:nginx.conf

# Infrastructure
org:$org filename:docker-compose
org:$org filename:terraform
org:$org filename:kubernetes
GITHUBDORKS

    echo "[OSINT-GITHUB] Generated $(grep -c '^org:' "$outfile") GitHub dork queries"
    echo "[OSINT-GITHUB] Results: $outfile"
}

# ============================================================
# FULL PASSIVE RECON PIPELINE
# ============================================================
osint_full_passive() {
    local domain="$1"
    if [ -z "$domain" ]; then
        echo "[OSINT] Usage: osint_full_passive <domain>"
        return 1
    fi
    echo "[OSINT] ============================================"
    echo "[OSINT] FULL PASSIVE RECONNAISSANCE"
    echo "[OSINT] Target: $domain"
    echo "[OSINT] ============================================"

    osint_ct_subdomains "$domain"
    osint_wayback_urls "$domain"
    osint_google_dorks "$domain"
    osint_shodan_queries "$domain" "${2:-}"
    osint_github_dorks "$domain"

    echo "[OSINT] ============================================"
    echo "[OSINT] PASSIVE RECON COMPLETE"
    echo "[OSINT] Results: $OSINT_OUTPUT_DIR"
    echo "[OSINT] ============================================"
}

# ============================================================
# QUICK REFERENCE
# ============================================================
osint_help() {
    cat << 'HELPMSG'
=== OSINT PASSIVE RECON PLAYBOOK ===

FULL PIPELINE:
  osint_full_passive <domain>              - Run all passive recon
  osint_full_passive <domain> <ip>         - With IP for Shodan

INDIVIDUAL:
  osint_ct_subdomains <domain>             - Certificate Transparency lookup
  osint_wayback_urls <domain>              - Wayback Machine + CommonCrawl URLs
  osint_google_dorks <domain>              - Generate Google dork queries
  osint_shodan_queries <domain> [ip]       - Shodan/Censys query generator
  osint_github_dorks <org>                 - GitHub secret dorking queries
  osint_securitytrails <domain>            - SecurityTrails DNS history

SCREENSHOT RECON:
  gowitness file <url-list.txt>            - Screenshot list of URLs
  gowitness scan single -u <url>           - Screenshot single URL
  gowitness report                         - Generate HTML report

EXAMPLES:
  osint_full_passive example.com
  osint_ct_subdomains example.com
  osint_wayback_urls example.com

FILES:
  $OSINT_OUTPUT_DIR/   - All OSINT results
HELPMSG
}

# ALIASES
alias osint='osint_full_passive'
alias osinthelp='osint_help'
alias ct-subs='osint_ct_subdomains'
alias wayback='osint_wayback_urls'
alias gdorks='osint_google_dorks'

echo "[OSINT] Playbook loaded. Type 'osinthelp' for commands."
