# OPERATIONSPECTRE Sandbox Tools

## Architecture Overview

### CLI Mode (Traditional)
```
User → CLI → Docker Container → 50+ Tools
    ↓      ↓      ↓           ↓
Manual  Text   Fast        Full Kali Arsenal
                CLI        Playbooks Embedded
``` 

### MCP Mode (AI Agents)
```
AI Agent → MCP Server → CLI → Docker Container → 50+ Tools
    ↓         ↓         ↓      ↓              ↓
60-80%    Structured Fast   50+ Tools        Full Kali Arsenal
Token     JSON      CLI   Pre-installed    Playbooks Embedded
Saving    Response  Backend Tools          MCP Integration
```

## Security & Pentest Tools

| Tool | Category | MCP Mode | CLI Mode | Description |
|------|----------|----------|----------|-------------|
| nmap | Network Scanner | ✅ | ✅ | Port scanning, service detection, OS fingerprinting |
| nping | Network Probing | ✅ | ✅ | Advanced packet generation and analysis |
| naabu | Port Scanner | ✅ | ✅ | Fast port scanner by ProjectDiscovery |
| nuclei | Vulnerability Scanner | ✅ | ✅ | Template-based vulnerability scanner |
| subfinder | Reconnaissance | ✅ | ✅ | Subdomain discovery tool |
| httpx | HTTP Probing | ✅ | ✅ | HTTP toolkit for probing web servers |
| sqlmap | SQL Injection | ✅ | ✅ | Automated SQL injection detection and exploitation |
| sqlmapapi | SQL Injection API | ✅ | ✅ | SQLMap API server for automation |
| ffuf | Fuzzer | ✅ | ✅ | Fast web fuzzer for directory/file discovery |
| wapiti | Web Scanner | ✅ | ✅ | Web application vulnerability scanner |
| owasp-zap | Web Scanner | ✅ | ✅ | OWASP ZAP - full web app security scanner |
| mitmproxy | Proxy | ✅ | ✅ | HTTP/HTTPS proxy for traffic inspection |
| mitmdump | Proxy | ✅ | ✅ | Command-line mitmproxy |
| mitmweb | Proxy | ✅ | ✅ | Web interface for mitmproxy |
| trivy | Container Scanner | ✅ | ✅ | Vulnerability scanner for containers/images |
| trufflehog | Secret Scanner | ✅ | ✅ | Find secrets in code repos |
| whois | Reconnaissance | ✅ | ✅ | Domain registration lookup |
| dig | DNS | ✅ | ✅ | DNS lookup utility |
| nslookup | DNS | ✅ | ✅ | DNS query tool |
| ncat | Networking | ✅ | ✅ | Netcat with SSL support |
| curl | HTTP | ✅ | ✅ | Transfer data from URLs |
| wget | HTTP | ✅ | ✅ | Download files from web |
| openssl | Cryptography | ✅ | ✅ | SSL/TLS toolkit |
| dirsearch | Web Scanner | ✅ | ✅ | Web path scanner |
| wafw00f | WAF Detection | Web Application Firewall detection |
| arjun | Reconnaissance | HTTP parameter discovery |
| jwt_tool | JWT Analysis | JWT token analysis tool |
| gospider | Web Spider | Fast web spider |
| katana | Web Crawler | Web crawler by ProjectDiscovery |
| vulnx | Vulnerability Scanner | Vulnerability scanner |
| interactsh-client | OOB Testing | OOB interaction server |
| bandit | Static Analysis | Python code security analyzer |
| semgrep | Static Analysis | Static analysis tool |
| caido-cli | Proxy | CLI proxy management |
| gau | OSINT | GetAllUrls — Wayback + CommonCrawl + OTX |
| waybackurls | OSINT | Fetch URLs from Wayback Machine |
| gowitness | Visual Recon | Web screenshot tool with reporting |
| subjack | Subdomain Takeover | Subdomain takeover detection |
| dalfox | XSS Scanner | Advanced XSS scanning tool |
| webtech | Fingerprinting | Web technology fingerprinting |
| whatweb | Fingerprinting | Web technology identification |

### Full Arsenal Tools (included in Dockerfile)

| Tool | Category | Description |
|------|----------|-------------|
| metasploit-framework | Exploitation | Full exploitation framework |
| burpsuite | Web Security | Web application security testing |
| hydra | Passwords | Brute force authentication cracker |
| john | Passwords | John the Ripper password cracker |
| hashcat | Passwords | GPU-accelerated password cracker |
| aircrack-ng | Wireless | WiFi security auditing suite |
| gobuster | Web | Directory/DNS/VHost busting tool |
| dirb | Web | Web content scanner |
| nikto | Web | Web server vulnerability scanner |
| responder | Post-Exploitation | LLMNR/NBT-NS/MDNS poisoner |
| enum4linux | Enumeration | Linux/Samba enumeration tool |
| crackmapexec | Post-Exploitation | Network pentesting tool |
| evil-winrm | Post-Exploitation | Windows Remote Management shell |

## Programming & Scripting

| Tool | Language/Runtime |
|------|-----------------|
| python3 | Python 3 |
| pip/pip3 | Python package manager |
| node/nodejs | JavaScript runtime |
| npm/npx | Node package manager |
| go/gofmt | Go language |
| java | Java runtime (OpenJDK) |
| perl | Perl language |
| bash | Shell scripting |
| jq | JSON processor |
| make/gmake | Build automation |
| gcc/g++ | C/C++ compiler |
| gdb | GNU debugger |

## Python Libraries

| Package | Purpose |
|---------|---------|
| beautifulsoup4 | HTML parsing |
| requests | HTTP requests |
| httpx | Async HTTP client |
| playwright | Browser automation |
| PyJWT | JWT token handling |
| cryptography | Crypto primitives |
| lxml | XML/HTML parsing |
| pillow | Image processing |
| tree-sitter | Code parsing |
| aiohttp | Async HTTP client/server |
| fastapi | Modern web framework |
| PyYAML | YAML parsing |
| pydantic | Data validation |
| jinja2 | Template engine |
| rich | Rich text formatting |
| orjson | Fast JSON serialization |

## Other Useful Tools

| Tool | Description |
|------|-------------|
| tmux | Terminal multiplexer |
| git | Version control |
| rg (ripgrep) | Fast text search |
| jq | JSON processing |
| parallel | Parallel execution |
| htop | Process viewer |
| vim/nano | Text editors |

## Tool Locations

| Path | Tools |
|------|-------|
| `/usr/bin` | nmap, nping, naabu, nuclei, subfinder, httpx, sqlmap, ffuf, wapiti, owasp-zap, mitmproxy, trivy, trufflehog, curl, wget, openssl |
| `/home/pentester/.local/bin` | arjun, bandit, semgrep, wafw00f, jwt_tool, webtech |
| `/root/.local/bin` | arjun, bandit, semgrep, wafw00f, webtech |
| `/home/pentester/go/bin` | gospider, httpx, interactsh-client, katana, vulnx |
| `/root/go/bin` | gospider, httpx, interactsh-client, katana, vulnx, gau, waybackurls, gowitness, subjack, dalfox, nuclei |
| `/usr/local/bin` | caido-cli, trivy, trufflehog |
