#!/bin/bash
# ============================================================
# RATE LIMIT & WAF EVASION HELPERS
# Source this to get rate-limit-aware scanning defaults
# ============================================================
# LOCATION: /opt/playbooks/rate-limit-helpers.sh
# ============================================================

# Default rate-limit settings (conservative to avoid WAF blocks)
export RL_NUCLEI="-rl 15 -c 5 -timeout 15 -retries 2"
export RL_FFUFC="-t 20 -p 0.5 --timeout 10 --rate 15/second"
export RL_HTTPX="-rate-limit 5 -timeout 15 -retries 2"
export RL_KATANA="-d 3 -c 5 -rl 10 -timeout 15"
export RL_GOSSPIDER="-t 5 -c 5 -d 3"
export RL_WAPITI="--max-links-per-page 50 --timeout 15"
export RL_NMAP="-T2 --max-retries 2 --host-timeout 10m"
export RL_SQLMAP="--delay=1 --randomize --timeout=30 --retries=3"

# Random User-Agent picker
random_ua() {
    local ua_file="/opt/opspectre/wordlists/user-agents.txt"
    if [ -f "$ua_file" ]; then
        shuf -n 1 "$ua_file"
    else
        echo "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    fi
}

# Generate a UA argument for curl
ua_arg() {
    echo "-H 'User-Agent: $(random_ua)'"
}

# Rate-limited nuclei wrapper
rl_nuclei() {
    echo "[RL-NUCLEI] Running nuclei with rate-limit defaults..."
    nuclei $RL_NUCLEI "$@"
}

# Rate-limited ffuf wrapper
rl_ffuf() {
    echo "[RL-FFUF] Running ffuf with rate-limit defaults..."
    ffuf $RL_FFUFC "$@"
}

# Proxy-aware scanning
scan_with_proxy() {
    local proxy="$1"
    shift
    echo "[PROXY] Scanning through proxy: $proxy"
    proxychains4 "$@"
}

scan_with_tor() {
    echo "[TOR] Routing through Tor..."
    # Ensure Tor is running
    service tor start 2>/dev/null || true
    sleep 2
    proxychains4 "$@"
}

# Stealth scan helper — combines rate limits + random UA + delays
stealth_nmap() {
    local target="$1"
    local ua=$(random_ua)
    echo "[STEALTH] Running stealth scan against $target..."
    echo "[STEALTH] UA: $ua"
    nmap -sS -T2 -f --data-length 32 \
        --max-retries 1 --host-timeout 15m \
        -oA "/workspace/output/nmap/stealth-$(echo "$target" | tr '.' '-')" \
        "$target"
}

echo "[RATE-LIMIT] Helpers loaded. Rate limits: nuclei=15rps, ffuf=15rps, nmap=T2"
