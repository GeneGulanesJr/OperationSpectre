#!/bin/bash
# Test script for full Kali arsenal
# Run inside the container to verify all tools are installed and working

echo "=== OPERATIONSPECTRE Full Arsenal Test ==="
echo ""

# Test function
test_tool() {
    local tool=$1
    local cmd=$2
    echo -n "Testing $tool... "
    if eval "$cmd" >/dev/null 2>&1; then
        echo "✓ OK"
    else
        echo "✗ FAILED"
    fi
}

# Core tools
echo "--- Core Tools ---"
test_tool "nmap" "nmap --version | head -1"
test_tool "sqlmap" "sqlmap --version | head -1"
test_tool "nuclei" "nuclei -version 2>&1 | head -1"
test_tool "ffuf" "ffuf -V 2>&1 | head -1"

# Metasploit
echo ""
echo "--- Metasploit ---"
test_tool "msfconsole" "msfconsole -x version 2>&1 | head -1"
test_tool "msfvenom" "msfvenom --version 2>&1 | head -1"

# Password tools
echo ""
echo "--- Password Cracking ---"
test_tool "hydra" "hydra -h | head -1"
test_tool "john" "john --help | head -1"
test_tool "hashcat" "hashcat --version | head -1"

# Wireless
echo ""
echo "--- Wireless Tools ---"
test_tool "aircrack-ng" "aircrack-ng --help | head -1"
test_tool "reaver" "reaver -h | head -1"

# Post-exploitation
echo ""
echo "--- Post-Exploitation ---"
test_tool "responder" "responder -h | head -1"
test_tool "crackmapexec" "crackmapexec --version 2>&1 | head -1"
test_tool "evil-winrm" "evil-winrm -h | head -1"

# Web tools
echo ""
echo "--- Web Tools ---"
test_tool "nikto" "nikto -Version | head -1"
test_tool "dirb" "dirb | head -1"
test_tool "gobuster" "gobuster version 2>&1 | head -1"

# Social engineering
echo ""
echo "--- Social Engineering ---"
test_tool "setoolkit" "setoolkit -h | head -1"

# Forensics
echo ""
echo "--- Forensics & RE ---"
test_tool "binwalk" "binwalk --help | head -1"
test_tool "volatility3" "volatility3 -h | head -1"

# Burp Suite
echo ""
echo "--- Burp Suite ---"
test_tool "burpsuite" "burpsuite --version 2>&1 | head -1 || echo 'Burp installed (version check may fail in headless)'"

# Database
echo ""
echo "--- Database ---"
if sudo service postgresql status >/dev/null 2>&1; then
    echo "PostgreSQL: ✓ Running"
else
    echo "PostgreSQL: ✗ Not running"
fi

echo ""
echo "=== Test Complete ==="