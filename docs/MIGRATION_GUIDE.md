# OperationSpectre Migration Guide

This guide helps you migrate from the old tool server system to the new MCP integration.

## Overview

The new MCP integration provides significant improvements:
- **60-80% token savings** for small models (9B/100k context)
- **Structured JSON responses** for better AI integration
- **One-command startup** for both MCP server and sandbox
- **Enhanced error handling** and recovery
- **Better monitoring** and logging

## Quick Migration

### Step 1: Stop Old Services
```bash
# Stop any existing containers
cd containers
docker-compose down

# Kill any old MCP server processes
pkill -f "tool_server.py" 2>/dev/null || true
```

### Step 2: Start New System
```bash
# Start everything with one command
./scripts/manage.py start

# Check status
./scripts/manage.py status
```

### Step 3: Verify Setup
```bash
# Test MCP server health
curl http://localhost:8000/health

# List available tools
curl http://localhost:8000/tools

# Test sandbox status
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "sandbox_status", "arguments": {}}'
```

## Migration Details

### Port Changes

| Old Port | New Port | Service |
|----------|----------|---------|
| 48081 | 8000 | MCP Server |
| 48082 | 8001 | MCP Server (alt) |
| 48083 | 8002 | MCP Server (alt) |

### Command Changes

#### Old Commands (Deprecated)
```bash
# Old tool server API
curl -H "Authorization: Bearer $TOOL_SERVER_TOKEN" \
     http://localhost:48081/execute \
     -d '{"command": "nmap -sV 192.168.1.1"}'

# Old start script
./scripts/start-opspectre.sh
```

#### New Commands
```bash
# New MCP server
curl http://localhost:8000/health

# New MCP tools
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "nmap_scan", "arguments": {"target": "192.168.1.1"}}'

# New management
./scripts/manage.py start
```

### Docker Configuration Changes

#### Old docker-compose.yml
```yaml
version: '3.8'
services:
  opspectre-full:
    build: .
    ports:
      - "5900:5900"  # VNC
      - "6080:6080"  # noVNC
      - "48081:48081"  # Old tool server
```

#### New docker-compose.full.yml
```yaml
version: '3.8'
services:
  opspectre-sandbox:
    build: .
    ports:
      - "5900:5900"  # VNC
      - "6080:6080"  # noVNC
  
  opspectre-mcp:
    build: 
      context: .
      dockerfile: containers/Dockerfile.mcp
    ports:
      - "8000:8000"  # MCP server
```

## AI Agent Migration

### Old Integration (Deprecated)
```python
# Old way - using tool server
import requests

response = requests.post(
    "http://localhost:48081/execute",
    headers={"Authorization": f"Bearer {token}"},
    json={"command": "nmap -sV target.com"}
)
result = response.json()
```

### New Integration (MCP)
```python
# New way - using MCP tools
from pi_pentest_recon_mcp import MCPReconExtension

extension = MCPReconExtension()
result = extension.nmap_scan(target="target.com")
```

### Small Model Pipeline Migration

#### Old Pipeline
```bash
# Old way - high token usage
python3 scripts/pipeline_runner.py scripts/pipelines/traditional-recon.yaml --target example.com
# ~24,000 tokens per step
```

#### New Pipeline
```bash
# New way - 60-80% token savings
python3 scripts/pipeline_runner.py scripts/pipelines/mcp-recon.yaml --target example.com
# ~6,000-8,000 tokens total
```

## Environment Variables

### Old Environment Variables
```bash
export TOOL_SERVER_TOKEN="your-token"
export TOOL_SERVER_URL="http://localhost:48081"
```

### New Environment Variables
```bash
export MCP_SERVER_URL="http://localhost:8000"
export MCP_SERVER_PORT="8000"
export OPSPECTRE_IMAGE="opspectre-full:latest"
```

## Feature Comparison

| Feature | Old System | New MCP System |
|---------|-----------|---------------|
| Token Usage | High (~24,000/step) | Low (~6,000-8,000 total) |
| Response Format | Raw CLI text | Structured JSON |
| Error Handling | Basic | Advanced with retry logic |
| Monitoring | Basic | Comprehensive health checks |
| Startup | Multiple commands | One command |
| AI Integration | Manual | Built-in MCP support |
| Port Management | Fixed ports | Dynamic port assignment |

## Migration Scripts

### Auto-Migration Script
```bash
#!/bin/bash
# scripts/migrate.sh

echo "Starting OperationSpectre migration..."

# Stop old services
echo "Stopping old services..."
docker-compose down 2>/dev/null || true
pkill -f "tool_server.py" 2>/dev/null || true

# Start new system
echo "Starting new MCP system..."
./scripts/manage.py start

# Verify migration
echo "Verifying migration..."
sleep 5

if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Migration successful!"
    echo "MCP server is running on port 8000"
    echo "Use './scripts/manage.py status' to check services"
else
    echo "❌ Migration failed!"
    echo "Check logs with: ./scripts/manage.py logs"
    exit 1
fi
```

### Test Migration
```bash
#!/bin/bash
# scripts/test_migration.sh

echo "Testing migration..."

# Test MCP server
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo "✅ MCP server health check passed"
else
    echo "❌ MCP server health check failed"
    exit 1
fi

# Test tools endpoint
if curl -s http://localhost:8000/tools | grep -q "nmap_scan"; then
    echo "✅ Tools endpoint working"
else
    echo "❌ Tools endpoint failed"
    exit 1
fi

# Test sandbox
if curl -s http://localhost:8000/tools/call \
   -H "Content-Type: application/json" \
   -d '{"tool_name": "sandbox_status", "arguments": {}}' | \
   grep -q "Sandbox is running"; then
    echo "✅ Sandbox integration working"
else
    echo "❌ Sandbox integration failed"
    exit 1
fi

echo "🎉 All tests passed! Migration is complete."
```

## Troubleshooting Migration Issues

### Issue: Port Already in Use
```bash
# Check what's using the port
lsof -i :8000

# Start with different port
./scripts/manage.py start --port 8001
```

### Issue: Docker Container Not Starting
```bash
# Check Docker status
docker info

# Check container logs
docker logs opspectre-sandbox

# Restart Docker service
sudo systemctl restart docker
```

### Issue: MCP Server Not Responding
```bash
# Check MCP server logs
./scripts/manage.py logs --service opspectre-mcp --follow

# Test with curl
curl http://localhost:8000/health

# Restart MCP server
./scripts/manage.py restart
```

### Issue: Python Import Error
```bash
# Install dependencies
pip install requests fastapi uvicorn

# Check Python path
export PYTHONPATH=/path/to/OperationSpectre:$PYTHONPATH
```

## Rollback Plan

If you need to rollback to the old system:

1. Stop new services:
```bash
./scripts/manage.py stop
```

2. Start old system:
```bash
cd containers
docker-compose up -d
```

3. Use old API:
```bash
curl -H "Authorization: Bearer $TOOL_SERVER_TOKEN" \
     http://localhost:48081/execute \
     -d '{"command": "nmap -sV target.com"}'
```

## Next Steps After Migration

1. **Read Documentation**: Review `README.md` and `MCP_USAGE.md`
2. **Test AI Integration**: Try `pentest-recon-mcp` skill
3. **Explore Features**: Use `./scripts/manage.py --help` for all commands
4. **Monitor Performance**: Compare token usage with old system
5. **Report Issues**: Document any problems encountered

## Support

If you encounter issues during migration:
1. Check logs: `./scripts/manage.py logs`
2. Review troubleshooting section
3. Test with provided migration scripts
4. Check GitHub issues for known problems

---

**Migration Checklist**:
- [ ] Stop old services
- [ ] Start new system with `./scripts/manage.py start`
- [ ] Verify health checks
- [ ] Test MCP tools
- [ ] Update AI agent integration
- [ ] Monitor performance improvements
- [ ] Document any issues