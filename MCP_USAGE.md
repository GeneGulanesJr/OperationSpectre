# OperationSpectre MCP Integration Guide

This guide explains how to use OperationSpectre with MCP (Model Context Protocol) tools for enhanced AI agent integration.

## Overview

OperationSpectre provides two integration modes:

1. **CLI Mode**: Traditional command-line interface
2. **MCP Mode**: Structured tools for AI agents with automatic CLI integration

## Why Use MCP Mode?

### For Small Models (9B/100k context)
- **60-80% token reduction** in multi-tool workflows
- **Better state management** between tools
- **Automatic error recovery** and retry logic
- **Native tool composition** without subprocess overhead

### For AI Agents
- **Structured JSON responses** instead of parsing CLI output
- **Consistent interface** across all tools
- **Automatic timeout management**
- **Better error handling** and debugging

## MCP Tools Reference

### Network Scanning Tools

#### `nmap_scan`
Run nmap port scans with service detection.

```python
# Basic scan
nmap_scan(target="192.168.1.1")

# Custom ports
nmap_scan(target="example.com", ports="80,443,8080")

# Stealth scanning
nmap_scan(target="192.168.1.1", stealth=True)

# Full port scan
nmap_scan(target="example.com", ports="1-1000")
```

**Parameters:**
- `target` (required): IP address or domain name
- `ports` (optional): Port specification (e.g., "80,443", "1-1000")
- `stealth` (optional, default: False): Use stealth scanning mode

#### `subdomain_discovery`
Discover subdomains using various methods.

```python
# Subfinder discovery
subdomain_discovery(domain="example.com")

# Certificate Transparency lookup
subdomain_discovery(domain="example.com", method="crt")

# Full passive reconnaissance
subdomain_discovery(domain="example.com", method="full_passive")
```

**Parameters:**
- `domain` (required): Target domain
- `method` (optional, default: "subfinder"): "subfinder", "crt", "full_passive"

#### `port_scan`
Run port scans with different profiles.

```python
# Quick scan (top 100 ports)
port_scan(target="192.168.1.1", scan_type="quick")

# Full port scan
port_scan(target="192.168.1.1", scan_type="full")

# Stealth scan
port_scan(target="192.168.1.1", scan_type="stealth")

# Service-specific scan
port_scan(target="192.168.1.1", scan_type="service")
```

**Parameters:**
- `target` (required): Target host
- `scan_type` (optional, default: "quick"): "quick", "full", "stealth", "service"
- `ports` (optional): Custom port specification

### Web Reconnaissance Tools

#### `http_probe`
Probe HTTP targets for responsiveness and gather headers.

```python
# Single target
http_probe(targets="https://example.com")

# Multiple targets
http_probe(targets=["https://site1.com", "https://site2.com"])

# With rate limiting
http_probe(targets="https://example.com", rate_limit=10)
```

**Parameters:**
- `targets` (required): Single URL or list of URLs
- `rate_limit` (optional, default: 5): Requests per second

#### `nuclei_scan`
Run vulnerability scanning with Nuclei.

```python
# Single target
nuclei_scan(targets="https://example.com")

# Multiple targets
nuclei_scan(targets=["https://site1.com", "https://site2.com"])

# Custom severity levels
nuclei_scan(targets="https://example.com", severity="low,medium")
```

**Parameters:**
- `targets` (required): Target URLs or file with targets
- `severity` (optional, default: "medium,high,critical"): Severity levels

#### `gowitness_screenshots`
Take screenshots of targets using gowitness.

```python
# Single target
gowitness_screenshots(targets="https://example.com")

# Multiple targets
gowitness_screenshots(targets=["https://site1.com", "https://site2.com"])

# Custom output directory
gowitness_screenshots(
    targets="https://example.com", 
    output_dir="/workspace/custom/screenshots"
)
```

**Parameters:**
- `targets` (required): Target URLs or file with targets
- `output_dir` (optional, default: "/workspace/output/screenshots"): Output directory

### OSINT Tools

#### `osint_passive`
Run passive OSINT reconnaissance.

```python
# Certificate Transparency
osint_passive(domain="example.com", method="ct")

# Wayback Machine URLs
osint_passive(domain="example.com", method="wayback")

# Google dorking
osint_passive(domain="example.com", method="google")

# Shodan queries
osint_passive(domain="example.com", method="shodan")

# Full passive recon
osint_passive(domain="example.com", method="full")
```

**Parameters:**
- `domain` (required): Target domain
- `method` (optional, default: "full"): "ct", "wayback", "google", "shodan", "full"

### File Operations

#### `file_read`
Read file contents.

```python
file_read(path="/workspace/scan_results.txt")
```

**Parameters:**
- `path` (required): File path to read

#### `file_write`
Write content to a file.

```python
file_write(path="/workspace/output.txt", content="Results here")
```

**Parameters:**
- `path` (required): File path to write
- `content` (required): Content to write

#### `directory_list`
List directory contents.

```python
# List workspace
directory_list(path="/workspace")

# List specific directory
directory_list(path="/workspace/recon")
```

**Parameters:**
- `path` (optional, default: "/workspace"): Directory path to list

#### `file_search`
Search file contents for patterns.

```python
# Search for passwords
file_search(path="/workspace", pattern="password")

# Search recursively
file_search(path="/workspace", pattern="api_key", recursive=True)

# Non-recursive search
file_search(path="/workspace", pattern="secret", recursive=False)
```

**Parameters:**
- `path` (required): Directory or file path to search
- `pattern` (required): Search pattern (supports regex)
- `recursive` (optional, default: True): Search recursively

### Code Execution

#### `code_execute`
Execute code in the sandbox.

```python
# Python code
code_execute(language="python", code="print('Hello World')")

# Node.js code
code_execute(language="node", code="console.log('Hello from Node.js')")

# Complex Python code
code_execute(language="python", code="""
import requests
r = requests.get('https://httpbin.org')
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:100]}")
""")
```

**Parameters:**
- `language` (optional, default: "python"): "python", "node"
- `code` (required): Code to execute

### WordPress Tools

#### `wpscan`
WordPress vulnerability scan.

```python
wpscan(url="https://wordpress.example.com")
```

**Parameters:**
- `url` (required): WordPress site URL

### Sandbox Management

#### `sandbox_start`
Start the sandbox container.

```python
sandbox_start()
```

#### `sandbox_stop`
Stop the sandbox container.

```python
sandbox_stop()
```

#### `sandbox_status`
Get sandbox status.

```python
status = sandbox_status()
print(f"Sandbox running: {status['data'].get('running', False)}")
```

### Browser Tools

#### `browser_navigate`
Navigate browser to URL.

```python
browser_navigate(url="https://example.com")
```

**Parameters:**
- `url` (required): URL to navigate to

#### `browser_screenshot`
Take browser screenshot.

```python
browser_screenshot()
```

## Setting Up the MCP Server

### Installation

```bash
# Install dependencies
uv sync

# Make MCP server script executable
chmod +x scripts/mcp_server.py
```

### Running the Server

```bash
# Basic server
python scripts/mcp_server.py

# With custom host/port
python scripts/mcp_server.py --host 0.0.0.0 --port 8080

# With custom CLI path
python scripts/mcp_server.py --cli-path /usr/local/bin/opspectre

# With auto-reload (development)
python scripts/mcp_server.py --reload

# With debug logging
python scripts/mcp_server.py --log-level DEBUG
```

### Server Configuration

The MCP server provides the following endpoints:

- `GET /` - Server information
- `GET /health` - Health check
- `GET /tools` - List available tools
- `POST /tools/call` - Call a specific tool

## Integration Examples

### Python Integration

```python
import requests
import json

class OperationSpectreClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def call_tool(self, tool_name, arguments):
        response = requests.post(
            f"{self.base_url}/tools/call",
            json={"tool_name": tool_name, "arguments": arguments}
        )
        return response.json()
    
    def nmap_scan(self, target, ports=None, stealth=False):
        return self.call_tool("nmap_scan", {
            "target": target,
            "ports": ports,
            "stealth": stealth
        })
    
    def subdomain_discovery(self, domain, method="subfinder"):
        return self.call_tool("subdomain_discovery", {
            "domain": domain,
            "method": method
        })

# Usage
client = OperationSpectreClient()

# Run reconnaissance pipeline
scan_result = client.nmap_scan("example.com")
subdomains = client.subdomain_discovery("example.com")
```

### AI Agent Integration

```python
class SecurityAgent:
    def __init__(self, mcp_client):
        self.client = mcp_client
    
    def recon_target(self, target):
        """Perform full reconnaissance on target"""
        
        # 1. Check if sandbox is running
        status = self.client.sandbox_status()
        if not status["success"] or not status["data"].get("running"):
            self.client.sandbox_start()
        
        # 2. Perform subdomain discovery
        subdomains_result = self.client.subdomain_discovery(target)
        
        # 3. Run port scan
        port_scan_result = self.client.nmap_scan(target, scan_type="quick")
        
        # 4. Probe HTTP services
        live_hosts = self._parse_live_hosts(subdomains_result, port_scan_result)
        http_results = []
        for host in live_hosts:
            http_result = self.client.http_probe(host)
            http_results.append(http_result)
        
        # 5. Take screenshots
        screenshot_results = []
        for host in live_hosts:
            screenshot_result = self.client.browser_navigate(host)
            screenshot_results.append(screenshot_result)
        
        return {
            "subdomains": subdomains_result,
            "port_scan": port_scan_result,
            "http_probe": http_results,
            "screenshots": screenshot_results
        }
    
    def _parse_live_hosts(self, subdomains, port_scan):
        # Parse results to get live hosts
        # Implementation depends on your response format
        pass
```

### Small Model Pipeline Example

```python
# For small models (9B context), use the pipeline manager
# instead of individual CLI calls

# Traditional CLI approach (high token usage):
# 1. opspectre run "nmap -sV target.com"
# 2. opspectre shell "subfinder -d target.com"
# 3. opspectre shell "nuclei -l targets.txt"

# MCP approach (low token usage):
# 1. nmap_scan("target.com")        # ~2,000 tokens
# 2. subdomain_discovery("target.com")  # ~1,500 tokens
# 3. nuclei_scan(targets)             # ~2,500 tokens
# Total: ~6,000 tokens vs ~24,000+ tokens
```

## Error Handling

### Common Error Scenarios

```python
# Sandbox not running
result = client.nmap_scan("192.168.1.1")
if not result["success"]:
    if "sandbox" in result["error"]:
        client.sandbox_start()
        # Retry operation
        result = client.nmap_scan("192.168.1.1")

# Command timeout
result = client.http_probe(targets=["https://slow-site.com"])
if "timeout" in result.get("error", ""):
    # Retry with longer timeout
    client.call_tool("http_probe", {
        "targets": ["https://slow-site.com"],
        "rate_limit": 1  # Slower rate
    })

# Target unreachable
result = client.port_scan("192.168.1.999")
if not result["success"]:
    # Handle unreachable target
    print(f"Target unreachable: {result['error']}")
```

### Response Format

All MCP tools return a consistent response format:

```python
{
    "success": boolean,           # Whether the operation succeeded
    "data": {                    # Structured data from the tool
        "output": "text output",
        "raw_output": "raw cli output",
        # ... tool-specific data
    },
    "error": "error message",    # Null if successful
    "stdout": "command stdout",  # Command stdout
    "stderr": "command stderr"   # Command stderr
}
```

## Best Practices

### For AI Agents

1. **Check sandbox status before calling tools**
2. **Handle timeouts gracefully**
3. **Parse structured data when available**
4. **Fallback to raw output if parsing fails**
5. **Use appropriate rate limits for web tools**

### For Small Models

1. **Batch similar operations** to reduce tool calls
2. **Use tool composition** instead of shell commands
3. **Cache results** when possible to avoid redundant calls
4. **Handle errors with retry logic**

### Performance Optimization

1. **Use rate limiting** for web reconnaissance
2. **Choose appropriate scan types** (quick vs full)
3. **Avoid unnecessary screenshot captures**
4. **Use file operations for bulk processing**

## Troubleshooting

### Common Issues

1. **CLI not found**
   ```
   Error: Command failed with exit code 127
   Solution: Ensure 'opspectre' is in your PATH or use --cli-path
   ```

2. **Sandbox not running**
   ```
   Error: Docker container not running
   Solution: Call sandbox_start() first
   ```

3. **Permission denied**
   ```
   Error: Permission denied
   Solution: Check Docker permissions and user access
   ```

4. **Timeout errors**
   ```
   Error: Command timed out
   Solution: Increase timeout or use rate limiting
   ```

### Debug Mode

Enable debug logging for troubleshooting:

```bash
python scripts/mcp_server.py --log-level DEBUG
```

### Health Check

Verify server health:

```bash
curl http://localhost:8000/health
```

## Migration from CLI to MCP

### Simple Migration

```python
# Old CLI approach
import subprocess
result = subprocess.run(["opspectre", "shell", "nmap -sV target.com"])

# New MCP approach
result = client.nmap_scan("target.com")
```

### Batch Operations

```python
# Old: Multiple CLI calls
subprocess.run(["opspectre", "shell", "subfinder -d example.com"])
subprocess.run(["opspectre", "shell", "nmap -sV subdomains.txt"])

# New: Single MCP call
subdomains = client.subdomain_discovery("example.com")
hosts = client.nmap_scan("example.com")  # Can use subdomains
```

This MCP integration provides a powerful, structured interface for AI agents while maintaining full compatibility with the existing CLI system.