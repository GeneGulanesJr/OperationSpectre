#!/bin/bash
# ============================================================
# BURP SUITE AGENT WRAPPER
# ============================================================
# Simple commands for AI agents to use Burp Suite
# Every agent in the container can use these immediately
# ============================================================

set -e

# Load shared scan helpers
source /opt/playbooks/scan-helpers.sh

BURP_JAR="/opt/burpsuite/burpsuite_community.jar"
BURP_PROJECTS="/workspace/output/burp-projects"
BURP_REPORTS="/workspace/output/reports"
BURP_CONFIGS="/opt/burpsuite/configs"

mkdir -p "$BURP_PROJECTS" "$BURP_REPORTS" "$BURP_CONFIGS"

# Generate default config if missing
if [ ! -f "$BURP_CONFIGS/default.json" ]; then
    cat > "$BURP_CONFIGS/default.json" << 'EOF'
{"project_options":{"connections":{"timeouts":{"normal":30}},"http":{"redirections":{"follow_redirections":true}}}}
EOF
fi

case "${1:-help}" in
    # === START/STOP ===
    start)
        PROJECT="${2:-$BURP_PROJECTS/session_$(date +%Y%m%d_%H%M%S).burp}"
        CONFIG="${3:-$BURP_CONFIGS/default.json}"
        
        echo "[BURP] Starting headless mode..."
        echo "[BURP] Project: $PROJECT"
        echo "[BURP] Proxy: http://0.0.0.0:8080"
        
        java -Xmx2g -Djava.awt.headless=true -jar "$BURP_JAR" \
            --project-file="$PROJECT" \
            --config-file="$CONFIG" &
        
        echo $! > /tmp/burp.pid
        sleep 3
        echo "[BURP] Started (PID: $(cat /tmp/burp.pid))"
        ;;
    
    stop)
        if [ -f /tmp/burp.pid ]; then
            kill $(cat /tmp/burp.pid) 2>/dev/null
            rm /tmp/burp.pid
            echo "[BURP] Stopped"
        else
            pkill -f burpsuite_community.jar && echo "[BURP] Stopped" || echo "[BURP] Not running"
        fi
        ;;
    
    status)
        if pgrep -f burpsuite_community.jar > /dev/null; then
            echo "RUNNING:PID=$(pgrep -f burpsuite_community.jar)"
        else
            echo "STOPPED"
        fi
        ;;
    
    # === SCANNING ===
    scan)
        # burpsuite-agent scan <url> [type:passive|active]
        URL="$2"
        TYPE="${3:-passive}"
        
        if [ -z "$URL" ]; then
            echo "ERROR: URL required"
            echo "Usage: burpsuite-agent scan <url> [passive|active]"
            exit 1
        fi
        
        SCAN_OUTPUT=$(scan_dir "BurpSuite-${TYPE}" "$URL")
        PROJECT="$SCAN_OUTPUT/session.burp"
        
        # Start Burp if not running
        if ! pgrep -f burpsuite_community.jar > /dev/null; then
            java -Xmx2g -Djava.awt.headless=true -jar "$BURP_JAR" \
                --project-file="$PROJECT" &
            echo $! > /tmp/burp.pid
            sleep 5
        fi
        
        echo "[BURP] $TYPE scan of: $URL"
        echo "[BURP] Project: $PROJECT"
        
        # Send initial requests through proxy
        curl -x http://127.0.0.1:8080 -sk -o /dev/null "$URL" 2>/dev/null || true
        curl -x http://127.0.0.1:8080 -sk -o /dev/null "$URL/robots.txt" 2>/dev/null || true
        curl -x http://127.0.0.1:8080 -sk -o /dev/null "$URL/sitemap.xml" 2>/dev/null || true
        
        echo "[BURP] Scan initiated. Check project file for results."
        echo "[BURP] Project: $PROJECT"
        ;;
    
    # === PROXY ===
    proxy)
        # burpsuite-agent proxy <url>
        URL="$2"
        
        if [ -z "$URL" ]; then
            echo "ERROR: URL required"
            exit 1
        fi
        
        echo "[BURP] Fetching via proxy: $URL"
        curl -x http://127.0.0.1:8080 -v "$URL"
        ;;
    
    # === SPIDER/CRAWL ===
    spider)
        URL="$2"
        
        if [ -z "$URL" ]; then
            echo "ERROR: URL required"
            exit 1
        fi
        
        SCAN_OUTPUT=$(scan_dir "BurpSuite-Spider" "$URL")
        PROJECT="$SCAN_OUTPUT/session.burp"
        
        # Start Burp if not running
        if ! pgrep -f burpsuite_community.jar > /dev/null; then
            java -Xmx2g -Djava.awt.headless=true -jar "$BURP_JAR" \
                --project-file="$PROJECT" &
            echo $! > /tmp/burp.pid
            sleep 5
        fi
        
        echo "[BURP] Spidering: $URL"
        
        # Crawl through proxy
        for path in "" "/robots.txt" "/sitemap.xml" "/.well-known/security.txt"; do
            curl -x http://127.0.0.1:8080 -sk -o /dev/null "${URL}${path}" 2>/dev/null || true
        done
        
        echo "[BURP] Spider complete. Project: $PROJECT"
        ;;
    
    # === CONFIG ===
    config)
        # burpsuite-agent config <type:default|aggressive|passive>
        TYPE="${2:-default}"
        OUTPUT="$BURP_CONFIGS/${TYPE}.json"
        
        case "$TYPE" in
            aggressive)
                cat > "$OUTPUT" << 'EOF'
{"project_options":{"scanner":{"thorough":{"move_detection_slider":"EXTREMELY_THOROUGH"}}}}
EOF
                ;;
            passive)
                cat > "$OUTPUT" << 'EOF'
{"project_options":{"scanner":{"live_scanning":{"live_audit_paused":true}}}}
EOF
                ;;
            *)
                cat > "$OUTPUT" << 'EOF'
{"project_options":{"connections":{"timeouts":{"normal":30}},"http":{"redirections":{"follow_redirections":true}}}}
EOF
                ;;
        esac
        
        echo "[BURP] Config created: $OUTPUT"
        ;;
    
    # === CHAIN WITH OTHER TOOLS ===
    chain)
        # burpsuite-agent chain <tool> <target>
        TOOL="$2"
        TARGET="$3"
        
        case "$TOOL" in
            nmap)
                echo "[BURP] Chaining with nmap: $TARGET"
                nmap -sV -p 80,443,8080,8443,8888,9090 "$TARGET" -oG - | grep -E "^[0-9]" | while read line; do
                    PORT=$(echo "$line" | cut -d'/' -f1)
                    echo "[BURP] Found port $PORT - add http://$TARGET:$PORT to Burp scope"
                done
                ;;
            nuclei)
                echo "[BURP] Chaining with nuclei: $TARGET"
                nuclei -u "$TARGET" -severity critical,high,medium -rl 15 -c 5 -timeout 15 -o "$BURP_REPORTS/nuclei_$(date +%Y%m%d).txt"
                echo "[BURP] Nuclei results: $BURP_REPORTS/nuclei_$(date +%Y%m%d).txt"
                ;;
            *)
                echo "Supported tools: nmap, nuclei"
                ;;
        esac
        ;;
    
    # === INTRUDER ===
    intruder)
        # burpsuite-agent intruder <setup|brute|config>
        ACTION="${2:-help}"
        case "$ACTION" in
            setup)
                mkdir -p /opt/burpsuite/payloads
                cat > /opt/burpsuite/payloads/usernames.txt << 'EOF'
admin
administrator
root
user
test
guest
EOF
                cat > /opt/burpsuite/payloads/passwords.txt << 'EOF'
password
123456
admin
root
test
guest
password123
letmein
changeme
EOF
                echo "[BURP] Intruder payloads created in /opt/burpsuite/payloads/"
                ;;
            brute)
                URL="$3"
                USER_PARAM="$4"
                PASS_PARAM="$5"
                if [ -z "$URL" ] || [ -z "$USER_PARAM" ] || [ -z "$PASS_PARAM" ]; then
                    echo "Usage: burpsuite-agent intruder brute <url> <user_param> <pass_param>"
                    exit 1
                fi
                echo "[BURP] Brute force setup for $URL"
                echo "[BURP] Username param: $USER_PARAM"
                echo "[BURP] Password param: $PASS_PARAM"
                echo "[BURP] Payloads: /opt/burpsuite/payloads/passwords.txt"
                ;;
            *)
                echo "Intruder commands:"
                echo "  burpsuite-agent intruder setup  - Create payload lists"
                echo "  burpsuite-agent intruder brute <url> <user_param> <pass_param>"
                ;;
        esac
        ;;
    
    # === DECODE ===
    decode)
        TYPE="$2"
        DATA="$3"
        case "$TYPE" in
            base64-d) echo "$DATA" | base64 -d ;;
            base64-e) echo -n "$DATA" | base64 ;;
            url-d) python3 -c "import urllib.parse; print(urllib.parse.unquote('$DATA'))" ;;
            url-e) python3 -c "import urllib.parse; print(urllib.parse.quote('$DATA'))" ;;
            hex-d) echo "$DATA" | xxd -r -p ;;
            hex-e) echo -n "$DATA" | xxd -p ;;
            md5) echo -n "$DATA" | md5sum | cut -d' ' -f1 ;;
            sha256) echo -n "$DATA" | sha256sum | cut -d' ' -f1 ;;
            jwt) 
                HEADER=$(echo "$DATA" | cut -d'.' -f1)
                PAYLOAD=$(echo "$DATA" | cut -d'.' -f2)
                echo "Header:"; echo "$HEADER" | base64 -d 2>/dev/null | python3 -m json.tool
                echo "Payload:"; echo "$PAYLOAD" | base64 -d 2>/dev/null | python3 -m json.tool
                ;;
            *)
                echo "Decode types: base64-d, base64-e, url-d, url-e, hex-d, hex-e, md5, sha256, jwt"
                echo "Usage: burpsuite-agent decode <type> <data>"
                ;;
        esac
        ;;
    
    # === SCOPE ===
    scope)
        URL="$2"
        if [ -z "$URL" ]; then
            echo "Usage: burpsuite-agent scope <url>"
            exit 1
        fi
        DOMAIN=$(echo "$URL" | sed -E 's|https?://([^/]+).*|\1|')
        echo "[BURP] Scope regex for $DOMAIN:"
        echo "  ^https?://[^/]*${DOMAIN}(/.*)?$"
        echo ""
        echo "[BURP] Add this in Target -> Scope -> Include in scope"
        ;;
    
    # === SECRETS ===
    secrets)
        echo "[BURP] Search patterns for sensitive data:"
        echo ""
        echo "API Keys: api[_-]?key, api[_-]?secret, access[_-]?token"
        echo "Credentials: password, passwd, secret"
        echo "Tokens: bearer, authorization, jwt, token"
        echo "Internal: localhost, 127.0.0.1, 192.168.*, 10.*"
        echo ""
        echo "Use in Proxy -> HTTP history search (regex mode)"
        ;;
    
    # === CA CERT ===
    ca-cert)
        echo "[BURP] CA Certificate: /app/certs/ca.crt"
        echo "[BURP] To use with curl:"
        echo "  curl --cacert /app/certs/ca.crt -x http://127.0.0.1:8080 https://target.com"
        echo ""
        echo "[BURP] To download Burp's own CA:"
        echo "  1. Start Burp: burpsuite-agent start"
        echo "  2. Visit: http://127.0.0.1:8080"
        echo "  3. Click 'CA Certificate' to download"
        ;;
    
    # === HELP ===
    help|*)
        cat << 'EOF'
BURP SUITE AGENT WRAPPER
=========================

START/STOP:
  start [project.burp] [config.json]  - Start Burp headless
  stop                                - Stop Burp
  status                              - Check if running

SCANNING:
  scan <url> [passive|active]         - Scan target
  spider <url>                        - Crawl target
  proxy <url>                         - Fetch via Burp proxy

INTRUDER:
  intruder setup                      - Create payload lists
  intruder brute <url> <user> <pass>  - Brute force setup

DECODER:
  decode <type> <data>                - Encode/decode data
    Types: base64-d, base64-e, url-d, url-e, hex-d, hex-e, md5, sha256, jwt

SCOPE & SEARCH:
  scope <url>                         - Get scope regex for target
  secrets                             - Show search patterns for sensitive data
  ca-cert                             - CA certificate info

CHAIN:
  chain <nmap|nuclei> <target>        - Chain with other tools
  config <default|aggressive|passive> - Generate config

EXAMPLES:
  burpsuite-agent start
  burpsuite-agent scan https://example.com passive
  burpsuite-agent decode jwt eyJhbGciOi...
  burpsuite-agent scope https://example.com
  burpsuite-agent intruder setup
  burpsuite-agent stop

PORTS:
  8080 - Burp Proxy
  5900 - VNC (GUI mode)
  6080 - noVNC (web VNC)

FILES:
  /workspace/output/burp-projects/  - Project files
  /opt/burpsuite/configs/           - Config files
  /opt/burpsuite/payloads/          - Intruder payloads

NOTES:
  - Always start Burp before scanning
  - Use 'passive' for authorized testing
  - Use 'active' ONLY with authorization
EOF
        ;;
esac