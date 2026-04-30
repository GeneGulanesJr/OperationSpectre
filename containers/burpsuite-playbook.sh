#!/bin/bash
# ============================================================
# BURP SUITE PLAYBOOK FOR AI AGENTS
# ============================================================
# This script provides all knowledge needed to use Burp Suite
# Community Edition proficiently from a headless Docker container.
#
# LOCATION: /opt/playbooks/burpsuite-playbook.sh
# USAGE: source /opt/playbooks/burpsuite-playbook.sh
# ============================================================

# Load shared scan helpers
source /opt/playbooks/scan-helpers.sh

# ============================================================
# SECTION 0: CONSTANTS
# ============================================================

# Port numbers
readonly BURP_PROXY_PORT=8080       # Burp Suite default proxy port
readonly VNC_PORT=5900              # VNC server port for GUI mode
readonly NOVNC_PORT=6080            # noVNC web interface port

# Timing constants
readonly BURP_STARTUP_DELAY=5      # Seconds to wait for Burp to start
readonly PROCESS_STOP_DELAY=1      # Seconds to wait after killing process

# Output formatting
readonly DEBUG_JAVA_LINES=3        # Lines of java version to display
readonly DEBUG_MEMORY_LINES=2      # Lines of memory info to display

# Nmap scan ports
readonly NMAP_WEB_PORTS="80,443,8080,8443"

# ============================================================
# SECTION 1: ENVIRONMENT SETUP
# ============================================================

# Burp Suite paths
export BURP_JAR="/opt/burpsuite/burpsuite_community.jar"
export BURP_PROJECTS_DIR="/workspace/output/burp-projects"
export BURP_CONFIGS_DIR="/opt/burpsuite/configs"
export BURP_REPORTS_DIR="/workspace/output/reports"
export BURP_EXTENSIONS_DIR="/opt/burpsuite/extensions"

# Java settings for headless operation
export BURP_JAVA_OPTS="-Xmx2g -Djava.awt.headless=true -XX:+UseG1GC -XX:MaxGCPauseMillis=200"
export BURP_JAVA_OPTS_GUI="-Xmx2g -Djava.net.preferIPv4Stack=true"

# Create required directories
mkdir -p "$BURP_PROJECTS_DIR" "$BURP_CONFIGS_DIR" "$BURP_REPORTS_DIR" "$BURP_EXTENSIONS_DIR"

# ============================================================
# SECTION 2: CORE COMMANDS
# ============================================================

# Start Burp Suite in headless mode (for automation)
burp_headless() {
    local project_file="${1:-$BURP_PROJECTS_DIR/autosave.burp}"
    local config_file="${2:-$BURP_CONFIGS_DIR/default.json}"
    
    echo "[BURP] Starting headless mode..."
    echo "[BURP] Project: $project_file"
    echo "[BURP] Config: $config_file"
    
    java $BURP_JAVA_OPTS -jar "$BURP_JAR" \
        --project-file="$project_file" \
        --config-file="$config_file" &
    
    local pid=$!
    echo "[BURP] Started with PID: $pid"
    echo $pid > /tmp/burp.pid
}

# Start Burp Suite in GUI mode (requires VNC)
burp_gui() {
    echo "[BURP] Starting GUI mode (use VNC to connect)..."
    
    # Start Xvfb if not running
    if ! pgrep -f "Xvfb :99" > /dev/null; then
        Xvfb :99 -screen 0 1920x1080x24 &
        sleep 1
    fi
    
    # Start VNC if not running
    if ! pgrep -f "x11vnc" > /dev/null; then
        x11vnc -display :99 -forever -nopw -listen 0.0.0.0 -rfbport ${VNC_PORT} &
        sleep 1
    fi
    
    DISPLAY=:99 java $BURP_JAVA_OPTS_GUI -jar "$BURP_JAR" &
    
    echo "[BURP] GUI started. Connect via VNC on port ${VNC_PORT}"
    echo "[BURP] Or use noVNC at http://localhost:${NOVNC_PORT}/vnc.html"
}

# Stop Burp Suite
burp_stop() {
    if [ -f /tmp/burp.pid ]; then
        local pid=$(cat /tmp/burp.pid)
        kill $pid 2>/dev/null && echo "[BURP] Stopped (PID: $pid)"
        rm /tmp/burp.pid
    else
        pkill -f "burpsuite_community.jar" && echo "[BURP] Stopped"
    fi
}

# Check if Burp is running
burp_status() {
    if pgrep -f "burpsuite_community.jar" > /dev/null; then
        echo "[BURP] Running (PID: $(pgrep -f 'burpsuite_community.jar'))"
        return 0
    else
        echo "[BURP] Not running"
        return 1
    fi
}

# ============================================================
# SECTION 3: CONFIGURATION TEMPLATES
# ============================================================

# Generate default configuration file
burp_generate_config() {
    local output_file="${1:-$BURP_CONFIGS_DIR/default.json}"
    
    cat > "$output_file" << 'EOF'
{
  "project_options": {
    "connections": {
      "platform_authentication": {},
      "upstream_proxy": {},
      "socks_proxy": {},
      "timeouts": {
        "normal": 30,
        "open_handshake_timeout": 10
      }
    },
    "http": {
      "http2": {
        "enable_http2": true
      },
      "redirections": {
        "follow_redirections": true,
        "protocol_enforcement": true
      }
    },
    "ssl": {
      "tls_negotiation": {
        "enable_alpn": true,
        "protocols": ["TLSv1.3", "TLSv1.2", "TLSv1.1"]
      }
    },
    "sessions": {
      "session_handling_rules": []
    }
  },
  "user_options": {
    "connections": {
      "http": {
        "http_proxy": {},
        "https_proxy": {}
      }
    },
    "display": {
      "character_sets": {
        "default_charset": "UTF-8"
      }
    }
  }
}
EOF
    
    echo "[BURP] Config generated: $output_file"
}

# Generate aggressive scan config
burp_generate_aggressive_config() {
    local output_file="${1:-$BURP_CONFIGS_DIR/aggressive.json}"
    
    cat > "$output_file" << 'EOF'
{
  "project_options": {
    "scanner": {
      "thorough": {
        "move_detection_slider": "EXTREMELY_THOROUGH"
      },
      "issues_reported": {
        "all_issues": true
      }
    }
  }
}
EOF
    
    echo "[BURP] Aggressive config generated: $output_file"
}

# ============================================================
# SECTION 4: WORKFLOW FUNCTIONS
# ============================================================

# Passive scan only (no requests, just analyzes traffic)
burp_passive_scan() {
    local target_url="$1"
    local scan_output=$(scan_dir "BurpSuite-Passive" "$target_url")
    local project_file="${2:-$scan_output/session.burp}"
    local config_file="${3:-$BURP_CONFIGS_DIR/default.json}"
    
    if [ -z "$target_url" ]; then
        echo "Usage: burp_passive_scan <target_url> [project_file] [config_file]"
        return 1
    fi
    
    echo "[BURP] Starting passive scan of: $target_url"
    
    # Create minimal config for passive only
    local passive_config="/tmp/burp_passive_$$.json"
    cat > "$passive_config" << EOF
{
  "project_options": {
    "scanner": {
      "live_scanning": {
        "live_audit_paused": true
      }
    }
  }
}
EOF
    
    java $BURP_JAVA_OPTS -jar "$BURP_JAR" \
        --project-file="$project_file" \
        --config-file="$passive_config" &
    
    local pid=$!
    echo "[BURP] Passive scanner PID: $pid"
    echo $pid > /tmp/burp_passive.pid
    
    # Give Burp time to start
    sleep ${BURP_STARTUP_DELAY}
    
    # Send some requests through Burp proxy (default port ${BURP_PROXY_PORT})
    echo "[BURP] Sending requests through proxy..."
    curl -x http://127.0.0.1:${BURP_PROXY_PORT} -s -o /dev/null "$target_url" 2>/dev/null
    curl -x http://127.0.0.1:${BURP_PROXY_PORT} -s -o /dev/null "$target_url/robots.txt" 2>/dev/null
    curl -x http://127.0.0.1:${BURP_PROXY_PORT} -s -o /dev/null "$target_url/sitemap.xml" 2>/dev/null
    
    echo "[BURP] Passive scan running. Results in: $scan_output"
}

# Active scan (sends payloads - USE WITH AUTHORIZATION ONLY)
burp_active_scan() {
    local target_url="$1"
    local scan_output=$(scan_dir "BurpSuite-Active" "$target_url")
    local project_file="${2:-$scan_output/session.burp}"
    
    if [ -z "$target_url" ]; then
        echo "Usage: burp_active_scan <target_url> [project_file]"
        echo "WARNING: Active scanning sends attack payloads. Only use with authorization!"
        return 1
    fi
    
    echo "[BURP] Starting ACTIVE scan of: $target_url"
    echo "[BURP] Project file: $project_file"
    echo "[BURP] NOTE: This will send attack payloads to the target!"
    
    # Create active scan config
    local active_config="/tmp/burp_active_$$.json"
    cat > "$active_config" << 'EOF'
{
  "project_options": {
    "scanner": {
      "live_scanning": {
        "live_audit_paused": false
      },
      "thorough": {
        "move_detection_slider": "NORMAL"
      }
    }
  }
}
EOF
    
    java $BURP_JAVA_OPTS -jar "$BURP_JAR" \
        --project-file="$project_file" \
        --config-file="$active_config" &
    
    local pid=$!
    echo "[BURP] Active scanner PID: $pid"
    
    sleep ${BURP_STARTUP_DELAY}
    echo "[BURP] Active scan initiated. Monitor via proxy interface."
}

# Spider/crawl a target
burp_spider() {
    local target_url="$1"
    local scan_output=$(scan_dir "BurpSuite-Spider" "$target_url")
    local project_file="${2:-$scan_output/session.burp}"
    
    if [ -z "$target_url" ]; then
        echo "Usage: burp_spider <target_url> [project_file]"
        return 1
    fi
    
    echo "[BURP] Starting spider on: $target_url"
    
    java $BURP_JAVA_OPTS -jar "$BURP_JAR" \
        --project-file="$project_file" \
        --config-file="$BURP_CONFIGS_DIR/default.json" &
    
    local pid=$!
    echo "[BURP] Spider PID: $pid"
    
    sleep ${BURP_STARTUP_DELAY}
    
    # Use Burp's proxy to crawl
    echo "[BURP] Crawling target via proxy..."
    curl -x http://127.0.0.1:${BURP_PROXY_PORT} -s -o /dev/null "$target_url" 2>/dev/null
    
    echo "[BURP] Spider initiated. Results in: $project_file"
}

# ============================================================
# SECTION 5: INTEGRATION FUNCTIONS
# ============================================================

# Generate HTML report from project file
burp_export_report() {
    local project_file="$1"
    local target_url="${2:-}"
    local scan_output=""
    if [ -n "$target_url" ]; then
        scan_output=$(scan_dir "BurpSuite-Report" "$target_url")
    fi
    local report_file="${3:-${scan_output:-$BURP_REPORTS_DIR}/burp_report_$(date +%Y%m%d_%H%M%S).html}"
    
    if [ -z "$project_file" ] || [ ! -f "$project_file" ]; then
        echo "Usage: burp_export_report <project_file> [output_file]"
        return 1
    fi
    
    echo "[BURP] Exporting HTML report..."
    echo "[BURP] Project: $project_file"
    echo "[BURP] Report: $report_file"
    
    # NOTE: Report export is only available via GUI or API in Professional Edition
    # For Community Edition, we can extract data via proxy logs
    echo "[BURP] For Community Edition, check proxy history in project file"
}

# Use Burp as a proxy for other tools
burp_proxy_url() {
    local url="$1"
    
    if [ -z "$url" ]; then
        echo "Usage: burp_proxy_url <url>"
        return 1
    fi
    
    echo "[BURP] Fetching via Burp proxy: $url"
    curl -x http://127.0.0.1:${BURP_PROXY_PORT} -v "$url"
}

# Chain with other tools
burp_chain_nmap() {
    local target="$1"
    
    if [ -z "$target" ]; then
        echo "Usage: burp_chain_nmap <target>"
        return 1
    fi
    
    echo "[BURP] Running nmap + Burp chain scan..."
    
    # Run nmap first
    local nmap_output="/tmp/burp_nmap_$$.xml"
    nmap -sV -p ${NMAP_WEB_PORTS} -oX "$nmap_output" "$target"
    
    echo "[BURP] Nmap complete. Results: $nmap_output"
    echo "[BURP] Extracting web ports for Burp..."
    
    # Extract web ports from nmap
    grep -oP 'portid="\K[0-9]+' "$nmap_output" | while read port; do
        echo "[BURP] Found port: $port - Adding to Burp scope"
        # In full implementation, would add to Burp via API
    done
}

# ============================================================
# SECTION 6: EXTENSION MANAGEMENT
# ============================================================

# List installed extensions
burp_list_extensions() {
    echo "[BURP] Installed extensions:"
    ls -la "$BURP_EXTENSIONS_DIR/" 2>/dev/null || echo "  No extensions installed"
}

# Install BApp Store extension (manual download)
burp_install_extension() {
    local ext_url="$1"
    local ext_name="${2:-$(basename "$ext_url")}"
    
    if [ -z "$ext_url" ]; then
        echo "Usage: burp_install_extension <extension_url> [name]"
        return 1
    fi
    
    echo "[BURP] Downloading extension: $ext_name"
    wget -q -O "$BURP_EXTENSIONS_DIR/$ext_name" "$ext_url"
    echo "[BURP] Extension saved to: $BURP_EXTENSIONS_DIR/$ext_name"
    echo "[BURP] Load via Burp GUI or --enable-extensions flag"
}

# ============================================================
# SECTION 7: INTRUDER - PAYLOAD ATTACKS
# ============================================================

# Setup intruder payloads directory
burp_setup_intruder() {
    mkdir -p /opt/burpsuite/payloads
    
    # Create common payload lists
    cat > /opt/burpsuite/payloads/usernames.txt << 'EOF'
admin
administrator
root
user
test
guest
support
operator
manager
demo
EOF

    cat > /opt/burpsuite/payloads/passwords-common.txt << 'EOF'
password
123456
admin
root
test
guest
password123
letmein
welcome
changeme
EOF

    # Link SecLists payloads
    ln -sf /usr/share/seclists/Fuzzing /opt/burpsuite/payloads/fuzzing 2>/dev/null
    ln -sf /usr/share/seclists/Usernames /opt/burpsuite/payloads/usernames-seclists 2>/dev/null
    ln -sf /usr/share/seclists/Passwords /opt/burpsuite/payloads/passwords-seclists 2>/dev/null
    
    echo "[BURP] Intruder payloads ready in /opt/burpsuite/payloads/"
    echo "[BURP] Use with Intruder tab -> Payloads -> Load"
}

# Generate intruder positions config
burp_intruder_config() {
    local target_url="$1"
    local attack_type="${2:-sniper}"  # sniper, battering_ram, pitchfork, cluster_bomb
    
    echo "[BURP] Intruder Attack Types:"
    echo "  sniper       - Single payload set, iterate through positions"
    echo "  battering_ram - Same payload in all positions"
    echo "  pitchfork    - One payload set per position (parallel)"
    echo "  cluster_bomb  - All combinations of payloads"
    echo ""
    echo "[BURP] To use Intruder:"
    echo "  1. Send request to Intruder (right-click in Proxy history)"
    echo "  2. Clear § markers, add § around target positions"
    echo "  3. Select attack type: $attack_type"
    echo "  4. Load payloads from /opt/burpsuite/payloads/"
    echo "  5. Start attack"
}

# Quick brute force helper
burp_brute_force() {
    local target_url="$1"
    local username_param="$2"
    local password_param="$3"
    local username="${4:-admin}"
    
    if [ -z "$target_url" ] || [ -z "$username_param" ] || [ -z "$password_param" ]; then
        echo "Usage: burp_brute_force <url> <username_param> <password_param> [username]"
        echo "Example: burp_brute_force https://site.com/login username password admin"
        return 1
    fi
    
    echo "[BURP] Brute Force Setup"
    echo "[BURP] Target: $target_url"
    echo "[BURP] Username param: $username_param (fixed: $username)"
    echo "[BURP] Password param: $password_param (variable)"
    echo ""
    echo "[BURP] Steps:"
    echo "  1. Capture login request in Proxy"
    echo "  2. Send to Intruder"
    echo "  3. Clear all § markers"
    echo "  4. Add § around password value"
    echo "  5. Set attack type: pitchfork"
    echo "  6. Payload set 1: $username"
    echo "  7. Payload set 2: Load /opt/burpsuite/payloads/passwords-common.txt"
    echo "  8. Start attack"
    echo "  9. Look for different response length/status"
}

# ============================================================
# SECTION 8: SCOPE & TARGET CONFIGURATION
# ============================================================

# Define target scope
burp_set_scope() {
    local target_url="$1"
    
    if [ -z "$target_url" ]; then
        echo "Usage: burp_set_scope <target_url>"
        echo "Example: burp_set_scope https://example.com"
        return 1
    fi
    
    # Extract domain for scope
    local domain=$(echo "$target_url" | sed -E 's|https?://([^/]+).*|\1|')
    
    echo "[BURP] Setting scope for: $domain"
    echo "[BURP] To set scope in Burp:"
    echo "  1. Go to Target -> Scope"
    echo "  2. Add to scope: $target_url"
    echo "  3. Use 'Include in scope' with: ^https?://[^/]*${domain}(/.*)?$"
    echo "  4. This captures all paths under $domain"
    echo ""
    echo "[BURP] Filter proxy history to scope only:"
    echo "  - Click filter bar in Proxy -> HTTP history"
    echo "  - Check 'Show only in-scope items'"
}

# Multiple targets scope
burp_set_multi_scope() {
    local targets_file="$1"
    
    if [ -z "$targets_file" ] || [ ! -f "$targets_file" ]; then
        echo "Usage: burp_set_multi_scope <targets_file>"
        echo "File should have one URL per line"
        return 1
    fi
    
    echo "[BURP] Scope targets from file: $targets_file"
    echo ""
    while read -r url; do
        echo "  - $url"
    done < "$targets_file"
    echo ""
    echo "[BURP] Add each to scope in Target -> Scope"
}

# ============================================================
# SECTION 9: DECODER & UTILITIES
# ============================================================

# Decoder functions (can be used without Burp)
burp_decode() {
    local type="$1"
    local data="$2"
    
    case "$type" in
        base64-decode)
            echo "$data" | base64 -d 2>/dev/null
            ;;
        base64-encode)
            echo -n "$data" | base64
            ;;
        url-decode)
            python3 -c "import urllib.parse; print(urllib.parse.unquote('$data'))"
            ;;
        url-encode)
            python3 -c "import urllib.parse; print(urllib.parse.quote('$data'))"
            ;;
        html-decode)
            python3 -c "import html; print(html.unescape('$data'))"
            ;;
        html-encode)
            python3 -c "import html; print(html.escape('$data'))"
            ;;
        hex-decode)
            echo "$data" | xxd -r -p
            ;;
        hex-encode)
            echo -n "$data" | xxd -p
            ;;
        md5)
            echo -n "$data" | md5sum | cut -d' ' -f1
            ;;
        sha1)
            echo -n "$data" | sha1sum | cut -d' ' -f1
            ;;
        sha256)
            echo -n "$data" | sha256sum | cut -d' ' -f1
            ;;
        *)
            echo "[BURP] Decoder types:"
            echo "  base64-decode, base64-encode"
            echo "  url-decode, url-encode"
            echo "  html-decode, html-encode"
            echo "  hex-decode, hex-encode"
            echo "  md5, sha1, sha256"
            return 1
            ;;
    esac
}

# JWT decoder
burp_decode_jwt() {
    local token="$1"
    
    if [ -z "$token" ]; then
        echo "Usage: burp_decode_jwt <jwt_token>"
        return 1
    fi
    
    echo "[BURP] Decoding JWT..."
    
    # Split JWT
    local header=$(echo "$token" | cut -d'.' -f1)
    local payload=$(echo "$token" | cut -d'.' -f2)
    local signature=$(echo "$token" | cut -d'.' -f3)
    
    echo ""
    echo "Header:"
    echo "$header" | base64 -d 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "$header"
    echo ""
    echo "Payload:"
    echo "$payload" | base64 -d 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "$payload"
    echo ""
    echo "Signature: $signature (verify with jwt_tool)"
}

# ============================================================
# SECTION 10: SEARCH & ANALYSIS
# ============================================================

# Search proxy history
burp_search() {
    local search_term="$1"
    local project_file="$2"
    
    if [ -z "$search_term" ]; then
        echo "Usage: burp_search <term> [project_file]"
        return 1
    fi
    
    echo "[BURP] Searching for: $search_term"
    echo "[BURP] In Burp GUI:"
    echo "  1. Go to Proxy -> HTTP history"
    echo "  2. Use search bar (Ctrl+F)"
    echo "  3. Search for: $search_term"
    echo "  4. Check 'Request' and 'Response'"
    echo ""
    echo "[BURP] Also check:"
    echo "  - Target -> Site map"
    echo "  - Dashboard -> Issue activity"
}

# Find sensitive data patterns
burp_find_secrets() {
    echo "[BURP] Common patterns to search in proxy history:"
    echo ""
    echo "API Keys:"
    echo "  - api[_-]?key"
    echo "  - api[_-]?secret"
    echo "  - access[_-]?token"
    echo ""
    echo "Credentials:"
    echo "  - password"
    echo "  - passwd"
    echo "  - pwd"
    echo "  - secret"
    echo ""
    echo "Tokens:"
    echo "  - bearer"
    echo "  - authorization"
    echo "  - jwt"
    echo "  - token"
    echo ""
    echo "Internal:"
    echo "  - localhost"
    echo "  - 127\\.0\\.0\\.1"
    echo "  - 192\\.168\\."
    echo "  - 10\\."
    echo "  - internal"
    echo "  - admin"
    echo ""
    echo "[BURP] Use these regex patterns in Proxy search"
}

# ============================================================
# SECTION 11: CA CERTIFICATE FOR HTTPS
# ============================================================

# Install Burp CA cert for HTTPS interception
burp_install_ca() {
    echo "[BURP] Installing Burp CA Certificate"
    echo ""
    echo "Method 1 - Download from Burp:"
    echo "  1. Start Burp: burpsuite-agent start"
    echo "  2. Visit http://127.0.0.1:${BURP_PROXY_PORT} in browser"
    echo "  3. Click 'CA Certificate' (top right)"
    echo "  4. Save as /workspace/output/burp-ca.der"
    echo ""
    echo "Method 2 - Use pre-generated cert:"
    
    # Copy our CA cert for Burp to use
    if [ -f "/app/certs/ca.crt" ]; then
        cp /app/certs/ca.crt /opt/burpsuite/ca.crt 2>/dev/null
        echo "  Copied CA cert to /opt/burpsuite/ca.crt"
    fi
    
    echo ""
    echo "To install in browser/system:"
    echo "  - Chrome: Settings -> Security -> Manage certificates"
    echo "  - Firefox: Settings -> Certificates -> Import"
    echo "  - System: update-ca-certificates"
    echo ""
    echo "[BURP] For CLI tools (curl, python):"
    echo "  export REQUESTS_CA_BUNDLE=/path/to/burp-ca.crt"
    echo "  curl --cacert /path/to/burp-ca.crt https://target.com"
}

# ============================================================
# SECTION 12: TROUBLESHOOTING
# ============================================================

burp_debug() {
    echo "=== Burp Suite Debug Info ==="
    echo "Java Version:"
    java -version 2>&1 | head -${DEBUG_JAVA_LINES}
    echo ""
    echo "Burp JAR: $BURP_JAR"
    echo "Exists: $(test -f "$BURP_JAR" && echo 'YES' || echo 'NO')"
    echo ""
    echo "Process Status:"
    pgrep -af "burpsuite" || echo "Not running"
    echo ""
    echo "Port ${BURP_PROXY_PORT} Status:"
    netstat -tlnp 2>/dev/null | grep ${BURP_PROXY_PORT} || ss -tlnp | grep ${BURP_PROXY_PORT} || echo "Not listening"
    echo ""
    echo "Disk Space:"
    df -h /workspace | tail -1
    echo ""
    echo "Memory:"
    free -h | head -${DEBUG_MEMORY_LINES}
}

# Fix common issues
burp_fix() {
    echo "[BURP] Running diagnostics..."
    
    # Kill existing instances
    pkill -f "burpsuite_community.jar" 2>/dev/null
    sleep ${PROCESS_STOP_DELAY}
    
    # Clear temp files
    rm -f /tmp/burp*.pid 2>/dev/null
    rm -f /tmp/burp_passive_*.json 2>/dev/null
    rm -f /tmp/burp_active_*.json 2>/dev/null
    rm -f /tmp/burp_nmap_*.xml 2>/dev/null
    
    # Restart Xvfb if needed
    if ! pgrep -f "Xvfb :99" > /dev/null; then
        Xvfb :99 -screen 0 1920x1080x24 &
        sleep 1
    fi
    
    echo "[BURP] Cleanup complete. Ready to start fresh."
}

# ============================================================
# SECTION 13: QUICK REFERENCE
# ============================================================

burp_help() {
    cat << 'EOF'
=== BURP SUITE PLAYBOOK - QUICK REFERENCE ===

STARTUP:
  burp_headless [project.burp] [config.json]  - Start headless mode
  burp_gui                                     - Start GUI mode (VNC)
  burp_stop                                    - Stop Burp Suite
  burp_status                                  - Check if running

SCANNING:
  burp_passive_scan <url>                      - Passive scan only
  burp_active_scan <url>                       - Active scan (with auth!)
  burp_spider <url>                            - Crawl/spider target

PROXY:
  burp_proxy_url <url>                         - Fetch URL via Burp proxy
  curl -x http://127.0.0.1:${BURP_PROXY_PORT} <url>         - Use Burp as proxy

CONFIG:
  burp_generate_config [output.json]           - Generate default config
  burp_generate_aggressive_config [output.json]- Generate aggressive config

EXTENSIONS:
  burp_list_extensions                         - List installed extensions
  burp_install_extension <url> [name]          - Install extension

TOOLS:
  burp_chain_nmap <target>                     - Chain nmap with Burp
  burp_export_report <project.burp>            - Export HTML report

TROUBLESHOOTING:
  burp_debug                                   - Show debug info
  burp_fix                                     - Fix common issues

PORTS:
  ${BURP_PROXY_PORT}  - Burp Proxy (default)
  1337  - Burp Collaborator (if enabled)
  ${VNC_PORT}  - VNC (GUI mode)
  ${NOVNC_PORT}  - noVNC (web VNC)

FILES:
  /opt/burpsuite/burpsuite_community.jar       - Burp JAR
  /opt/burpsuite/configs/                      - Config files
  /workspace/output/burp-projects/             - Project files
  /workspace/output/reports/                   - Exported reports

NOTES:
  - Community Edition: Manual testing + passive scan
  - Professional Edition: Automated scanning via API
  - Always get authorization before active scanning
  - Use proxy (port ${BURP_PROXY_PORT}) to capture traffic
EOF
}

# ============================================================
# SECTION 14: ALIASES FOR QUICK ACCESS
# ============================================================

alias burp='burp_headless'
alias burpgui='burp_gui'
alias burpstop='burp_stop'
alias burpstatus='burp_status'
alias burpscan='burp_active_scan'
alias burpspy='burp_passive_scan'
alias burpspider='burp_spider'
alias burpproxy='burp_proxy_url'
alias burpreport='burp_export_report'
alias burphelp='burp_help'

# ============================================================
# SECTION 15: AUTO-INITIALIZATION
# ============================================================

# Generate default configs if they don't exist
if [ ! -f "$BURP_CONFIGS_DIR/default.json" ]; then
    burp_generate_config > /dev/null 2>&1
fi

if [ ! -f "$BURP_CONFIGS_DIR/aggressive.json" ]; then
    burp_generate_aggressive_config > /dev/null 2>&1
fi

echo "[BURP] Playbook loaded. Type 'burphelp' for commands."