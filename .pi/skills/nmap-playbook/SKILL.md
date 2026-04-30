---
name: nmap-playbook
description: Runs structured nmap scans (quick, deep, stealth, UDP) via opspectre sandbox and parses results into actionable findings. Use when performing network reconnaissance.
---

# Nmap Scan Playbook

Structured network scanning using nmap through the OperationSpectre sandbox. Includes predefined scan profiles and result parsing guidance.

## Prerequisites

- OperationSpectre sandbox running (`opspectre sandbox start`)
- Target IP(s), range, or CIDR block
- Authorization to scan the target network

## Scan Profiles

### 1. Quick Scan (Discovery)

Fast top-100 port scan with service detection. Best for initial reconnaissance.

```bash
opspectre shell "nmap -sV -T4 -F <TARGET> -oA /workspace/output/nmap/quick-scan"
```

**What it does:** Scans top 100 ports, detects services, aggressive timing.

---

### 2. Full Port Scan (Comprehensive)

Scans all 65,535 ports with service and OS detection. Slower but thorough.

```bash
opspectre shell "nmap -sV -sC -O -T4 -p- <TARGET> -oA /workspace/output/nmap/full-scan"
```

**What it does:** All ports, service version, default scripts, OS fingerprinting.

---

### 3. Stealth Scan (SYN Scan)

Half-open SYN scan that's less likely to be logged. Good for avoiding detection.

```bash
opspectre shell "nmap -sS -sV -T2 -p- <TARGET> -oA /workspace/output/nmap/stealth-scan"
```

**What it does:** SYN scan, slow timing (T2), all ports with service detection.

**Additional stealth options:**
```bash
# Fragment packets
opspectre shell "nmap -sS -sV -f -T2 <TARGET> -oA /workspace/output/nmap/stealth-frag-scan"

# Decoy scan
opspectre shell "nmap -sS -sV -D RND:10 <TARGET> -oA /workspace/output/nmap/stealth-decoy-scan"

# Spoof source port
opspectre shell "nmap -sS -sV --source-port 53 <TARGET> -oA /workspace/output/nmap/stealth-sport-scan"
```

---

### 4. UDP Scan

Scans common UDP ports. Essential for discovering DNS, SNMP, and other UDP services.

```bash
opspectre shell "nmap -sU --top-ports 100 -sV <TARGET> -oA /workspace/output/nmap/udp-scan"
```

**All common UDP ports:**
```bash
opspectre shell "nmap -sU -p 53,67,68,69,123,161,162,500,514,1194,1812,1813,4500,51820 <TARGET> -sV -oA /workspace/output/nmap/udp-targeted-scan"
```

---

### 5. Vulnerability Scan (NSE Scripts)

Runs vulnerability detection scripts against discovered services.

```bash
opspectre shell "nmap -sV --script vuln <TARGET> -oA /workspace/output/nmap/vuln-scan"
```

**Category-specific NSE scans:**
```bash
# SMB vulnerabilities
opspectre shell "nmap -sV --script smb-vuln* -p 139,445 <TARGET> -oA /workspace/output/nmap/smb-vuln-scan"

# HTTP vulnerabilities
opspectre shell "nmap -sV --script http-vuln* -p 80,443,8080 <TARGET> -oA /workspace/output/nmap/http-vuln-scan"

# SSL/TLS vulnerabilities
opspectre shell "nmap -sV --script ssl-enum-ciphers -p 443 <TARGET> -oA /workspace/output/nmap/ssl-scan"

# Authentication brute force (quick check)
opspectre shell "nmap -sV --script ftp-brute,ssh-brute,smtp-brute <TARGET> -oA /workspace/output/nmap/brute-scan"

# Discovery scripts
opspectre shell "nmap -sV --script discovery <TARGET> -oA /workspace/output/nmap/discovery-scan"

# DNS enumeration
opspectre shell "nmap -sV --script dns-zone-transfer,dns-cache-snoop -p 53 <TARGET> -oA /workspace/output/nmap/dns-scan"
```

---

### 6. Service-Specific Deep Scans

```bash
# Web services deep scan
opspectre shell "nmap -sV --script http-enum,http-headers,http-title,http-methods -p 80,443,8080,8443 <TARGET> -oA /workspace/output/nmap/web-deep-scan"

# Database services
opspectre shell "nmap -sV --script mysql-info,oracle-info,pgsql-info,mssql-info -p 3306,1521,5432,1433 <TARGET> -oA /workspace/output/nmap/db-scan"

# SNMP enumeration
opspectre shell "nmap -sV --script snmp-info,snmp-interfaces,snmp-sysdescr -p 161 <TARGET> -oA /workspace/output/nmap/snmp-scan"

# RPC enumeration
opspectre shell "nmap -sV --script rpcinfo -p 111 <TARGET> -oA /workspace/output/nmap/rpc-scan"
```

---

### 7. Ping Sweep (Host Discovery)

Find live hosts on a network before port scanning.

```bash
opspectre shell "nmap -sn <CIDR_RANGE> -oA /workspace/output/nmap/ping-sweep"
```

Example:
```bash
opspectre shell "nmap -sn 192.168.1.0/24 -oA /workspace/output/nmap/ping-sweep"
```

### 8. ARP Scan (Local Network)

Fast host discovery on local subnets using ARP.

```bash
opspectre shell "nmap -PR <CIDR_RANGE> -oA /workspace/output/nmap/arp-scan"
```

---

## Chaining Scans

### Full Network Assessment Pipeline
```bash
opspectre run "mkdir -p /workspace/output/nmap && \
  nmap -sn 192.168.1.0/24 -oA /workspace/output/nmap/01-ping-sweep && \
  nmap -sV -sC -T4 -F -iL /workspace/output/nmap/01-ping-sweep.gnuplot -oA /workspace/output/nmap/02-quick-scan && \
  nmap -sV --script vuln -p 80,443,445,22,21,3306 <TARGET> -oA /workspace/output/nmap/03-vuln-scan && \
  nmap -sU --top-ports 20 -sV <TARGET> -oA /workspace/output/nmap/04-udp-scan"
```

## Parsing Results

### Extract Open Ports
```bash
opspectre shell "grep 'open' /workspace/output/nmap/full-scan.gnmap"
```

### Extract Services Only
```bash
opspectre shell "grep -E '^[0-9]+/tcp.*open' /workspace/output/nmap/full-scan.gnmap"
```

### Extract with XML (structured)
```bash
opspectre shell "xmllint --xpath '//port[state=\"open\"]' /workspace/output/nmap/full-scan.xml 2>/dev/null"
```

### Summary of All Scans
```bash
opspectre shell "for f in /workspace/output/nmap/*.nmap; do echo \"=== \$f ===\"; cat \$f | grep -E 'open|Nmap scan'; echo; done"
```

## Output Locations

All results under `/workspace/output/nmap/`:
- `*-scan.nmap` — normal output (human readable)
- `*-scan.gnmap` — greppable output
- `*-scan.xml` — XML output (machine readable)

Use `-oA` prefix for all three formats simultaneously.

## Timing Templates

| Template | Pattern | Use Case |
|----------|---------|----------|
| `-T0` | Paranoid | IDS evasion, very slow |
| `-T1` | Sneaky | IDS evasion, slow |
| `-T2` | Polite | Reduced bandwidth |
| `-T3` | Normal | Default |
| `-T4` | Aggressive | Fast, reliable networks |
| `-T5` | Insane | Very fast, may miss ports |

## Rate-Limited Targets

When targets have WAFs or rate limiting (common on production sites):

```bash
# Use stealth helper (auto-loaded in container):
stealth_nmap <TARGET>

# Or manually:
nmap -sS -T2 -f --data-length 32 --max-retries 1 --host-timeout 15m <TARGET>
```

For vuln scans on rate-limited targets:
```bash
nmap -sV --script vuln -p 80,443 <TARGET> --host-timeout 5m -oA /workspace/output/nmap/vuln-scan
```

## Tips

- Always use `-oA <prefix>` for all three output formats
- Run `ping-sweep` first to identify live hosts before deep scanning
- Combine `-sV` with `--script vuln` for automated vulnerability detection
- Use `-A` for a shortcut to `-sV -sC -O --traceroute`
- For IDS evasion: `-f` (fragment), `-D RND:10` (decoys), `--source-port 53`
- For rate-limited targets: use `stealth_nmap` or `-T2 --max-retries 1 --host-timeout`
- Add `--data-length 32` to avoid signature-based detection
- Pipe nmap XML into other tools: `nmap -oX - target | nuclei -`
