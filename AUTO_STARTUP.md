# 🚀 Auto-Startup Guide for OperationSpectre with MCP Integration

This guide shows how to automatically start both the OperationSpectre sandbox and MCP server together for seamless integration.

## 📋 Prerequisites

1. **Docker** installed and running
2. **OperationSpectre CLI** installed
3. **Python 3.11+** with required dependencies

## 🛠️ Quick Start

### Method 1: Using Docker Compose (Recommended)

```bash
# Start everything with Docker
./scripts/manage.py start

# Stop everything
./scripts/manage.py stop

# Check status
./scripts/manage.py status

# View logs
./scripts/manage.py logs
```

### Method 2: Using Individual Scripts

```bash
# Start OperationSpectre sandbox and MCP server
./scripts/start-full.py

# Stop both services
./scripts/stop-full.py

# Check if running
./scripts/start-full.py --status
```

### Method 3: Direct Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.full.yml up -d

# Stop all services
docker-compose -f docker-compose.full.yml down

# View status
docker-compose -f docker-compose.full.yml ps
```

## 🔧 Configuration Options

### Environment Variables

```bash
# Set custom MCP server port
export PORT=8001
export HOST=0.0.0.0

# Set logging level
export LOG_LEVEL=DEBUG
```

### Custom Ports

```bash
# Start with custom port
./scripts/manage.py start --port 8001 --host 0.0.0.0

# Check status with custom port
./scripts/manage.py status --port 8001
```

## 🐳 Docker Setup

### Build Images

```bash
# Build MCP server image
docker build -f containers/Dockerfile.mcp -t opspectre-mcp .

# Build sandbox image (if not already built)
docker build -f containers/Dockerfile -t opspectre-sandbox .
```

### Network Configuration

The Docker Compose setup creates a dedicated network:

```yaml
networks:
  opspectre-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Volumes

- `./scripts:/workspace/scripts` - Scripts for MCP server
- `/tmp:/tmp/host-shared` - Shared temporary files

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI Agent      │     │   MCP Server    │     │   Docker        │
│   (9B/100k)     │◄───►│   (Port 8000)   │◄───►│   Sandbox       │
│                 │     │                 │     │   (Tools)       │
│                 │     │                 │     │                 │
│ Tools:          │     │ Tools:          │     │                 │
│ - OSINT         │     │ - osint_passive │     │ - nmap          │
│ - Subdomain     │     │ - subdomain_dis│     │ - subfinder     │
│ - Port Scan     │     │   discovery     │     │ - httpx         │
│ - Vulnerability │     │ - http_probe   │     │ - nuclei        │
│ - Screenshot    │     │ - nmap_scan     │     │ - gowitness     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## 🚀 Usage Examples

### 1. Python Integration

```python
from pi_pentest_recon_mcp import run_reconnaissance

# Start services first
# ./scripts/manage.py start

# Run reconnaissance
results = run_reconnaissance("example.com")
print(f"Found {results['summary']['subdomains_found']} subdomains")
```

### 2. Pipeline Runner

```bash
# Start services
./scripts/manage.py start

# Run MCP pipeline
python3 scripts/pipeline_runner.py scripts/pipelines/mcp-recon.yaml --target example.com
```

### 3. Direct MCP API

```bash
# Check MCP server health
curl http://localhost:8000/health

# List available tools
curl http://localhost:8000/tools

# Test a tool
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "osint_passive", "arguments": {"domain": "example.com", "method": "ct"}}'
```

## 📊 Monitoring and Debugging

### Health Checks

```bash
# MCP server health
curl http://localhost:8000/health

# Docker container health
docker-compose -f docker-compose.full.yml ps

# Sandbox status
opspectre sandbox status
```

### Log Monitoring

```bash
# View MCP server logs
./scripts/manage.py logs --service opspectre-mcp --follow

# View sandbox logs
./scripts/manage.py logs --service opspectre-sandbox --follow

# View all logs
./scripts/manage.py logs --follow
```

### Debug Mode

```bash
# Start with debug logging
./scripts/start-full.py --log-level DEBUG

# Start without waiting
./scripts/start-full.py --no-wait
```

## 🔧 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Change port
   ./scripts/manage.py start --port 8001
   ```

2. **Docker Not Running**
   ```bash
   # Start Docker
   sudo systemctl start docker
   
   # Check Docker status
   docker info
   ```

3. **Permission Issues**
   ```bash
   # Fix permissions
   chmod +x scripts/*.py
   chmod +x scripts/manage.py
   ```

4. **MCP Server Not Starting**
   ```bash
   # Check Docker logs
   docker-compose -f docker-compose.full.yml logs opspectre-mcp
   
   # Manual test
   python scripts/mcp_server.py --host localhost --port 8000
   ```

### Force Cleanup

```bash
# Stop and force cleanup
./scripts/manage.py stop --force

# Or manual cleanup
docker-compose -f docker-compose.full.yml down -v
pkill -f mcp_server.py
pkill -f opspectre
```

## 🔄 Service Management

### Development Workflow

```bash
# 1. Start services
./scripts/manage.py start

# 2. Run reconnaissance
python -c "from pi_pentest_recon_mcp import run_reconnaissance; run_reconnaissance('target.com')"

# 3. View results
cat /workspace/output/final_report.txt

# 4. Stop services
./scripts/manage.py stop
```

### Production Workflow

```bash
# 1. Update images
./scripts/manage.py update

# 2. Start services
./scripts/manage.py start

# 3. Monitor
./scripts/manage.py logs --follow

# 4. Stop when done
./scripts/manage.py stop
```

## 📚 Additional Resources

- [MCP Tools Reference](MCP_USAGE.md)
- [Original CLI Documentation](README.md)
- [Pipeline Configuration](.pi/skills/pentest-recon-mcp/pipeline.yaml)
- [Extension Documentation](.pi/skills/pentest-recon-mcp/README.md)

---

**Note**: The auto-startup system provides seamless integration between OperationSpectre sandbox and MCP server, enabling efficient AI-driven reconnaissance with 60-80% token savings for small models.