# OperationSpectre Documentation Index

This index provides a comprehensive overview of all OperationSpectre documentation, organized by topic and audience.

## 📖 Documentation Overview

### Primary Documentation
| Document | Description | Audience | Status |
|----------|-------------|----------|---------|
| [README.md](../README.md) | Main documentation with MCP integration | All users | ✅ Updated |
| [MCP_USAGE.md](../MCP_USAGE.md) | Complete MCP tools reference and examples | AI developers | ✅ New |
| [AUTO_STARTUP.md](../AUTO_STARTUP.md) | Auto-startup guide for MCP integration | System admins | ✅ New |
| [QUICK_START.md](QUICK_START.md) | Quick start guide with both CLI and MCP modes | New users | ✅ Updated |

### Migration Documentation
| Document | Description | Status |
|----------|-------------|---------|
| [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) | Complete migration from old to new system | ✅ New |
| scripts/migrate.py | Automated migration script | ✅ New |

### Tool-Specific Documentation
| Document | Description | Status |
|----------|-------------|---------|
| [opspectre-tools.md](opspectre-tools.md) | Complete tools list with MCP integration | ✅ Updated |
| [BURP_SUITE_VERIFICATION.md](BURP_SUITE_VERIFICATION.md) | Burp Suite functionality with MCP support | ✅ Updated |
| [FULL_ARSENAL_README.md](FULL_ARSENAL_README.md) | Kali tools documentation with MCP | ✅ Updated |
| [web-app-audit.md](web-app-audit.md) | Web application auditing guide | ✅ Updated |
| [parallel_execution.md](parallel_execution.md) | Parallel execution optimization guide | ✅ New |
| [PIPELINES.md](PIPELINES.md) | Complete pipeline documentation and usage | ✅ New |

### Skills Documentation
| Document | Description | Status |
|----------|-------------|---------|
| [pentest-recon/SKILL.md](../../.pi/skills/pentest-recon/SKILL.md) | Traditional reconnaissance pipeline | ⚠️ Needs update |
| [pentest-recon-mcp/SKILL.md](../../.pi/skills/pentest-recon-mcp/SKILL.md) | MCP-enhanced reconnaissance | ✅ New |
| [pentest-recon-mcp/README.md](../../.pi/skills/pentest-recon-mcp/README.md) | MCP recon guide | ✅ New |

## 🎯 Quick Start Guides

### For New Users
1. **Start Here**: [QUICK_START.md](QUICK_START.md) - Choose between CLI and MCP modes
2. **Migration**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - If coming from old system
3. **MCP Overview**: [MCP_USAGE.md](../MCP_USAGE.md) - For AI agent development
4. **Automated Workflows**: [PIPELINES.md](PIPELINES.md) - Multi-step security pipelines

### For System Administrators
1. **Auto-Startup**: [AUTO_STARTUP.md](../AUTO_STARTUP.md) - Production deployment
2. **Migration Script**: [scripts/migrate.py](../scripts/migrate.py) - Automated migration
3. **Docker Configuration**: [docker-compose.full.yml](../docker-compose.full.yml) - Container orchestration
4. **Pipeline Management**: [scripts/pipeline_runner.py](../scripts/pipeline_runner.py) - Automated workflows
5. **Performance Optimization**: [parallel_execution.md](parallel_execution.md) - 60-80% faster execution

### For AI Developers
1. **MCP Tools**: [MCP_USAGE.md](../MCP_USAGE.md) - Complete tool reference
2. **Recon Pipeline**: [pentest-recon-mcp/README.md](../../.pi/skills/pentest-recon-mcp/README.md) - Advanced workflows
3. **Automated Pipelines**: [scripts/pipeline_runner.py](../scripts/pipeline_runner.py) - Multi-step workflows
4. **Parallel Execution**: [parallel_execution.md](parallel_execution.md) - Performance optimization
3. **Small Model Optimization**: README.md (MCP section) - Token savings and performance

## 🏗️ Architecture Documentation

### Dual Mode Architecture
OperationSpectre now supports two execution modes:

#### CLI Mode (Traditional)
```
User → CLI → Docker Container → 50+ Tools
    ↓      ↓      ↓           ↓
Manual  Text   Fast        Full Kali Arsenal
                CLI        Playbooks Embedded
```

#### MCP Mode (AI Agents)
```
AI Agent → MCP Server → CLI → Docker Container → 50+ Tools
    ↓         ↓         ↓      ↓              ↓
60-80%    Structured Fast   50+ Tools        Full Kali Arsenal
Token     JSON      CLI   Pre-installed    Playbooks Embedded
Saving    Response  Backend Tools          MCP Integration
```

### Integration Points
- **AI Agent Integration**: MCP tools provide structured JSON responses
- **CLI Backward Compatibility**: Existing CLI commands work unchanged
- **Container Orchestration**: Docker Compose manages MCP server and sandbox
- **Monitoring**: Health checks, logging, and status management

## 🔧 Tool Reference

### MCP Tools Available
| Category | Tools | Description |
|----------|-------|-------------|
| **Network Scanning** | `nmap_scan`, `port_scan` | Port scanning with profiles |
| **Subdomain Discovery** | `subdomain_discovery` | Subdomain enumeration |
| **Web Reconnaissance** | `http_probe`, `nuclei_scan` | HTTP probing and vuln scanning |
| **OSINT** | `osint_passive` | Passive reconnaissance |
| **File Operations** | `file_read`, `file_write` | File management |
| **Sandbox** | `sandbox_status` | Container management |

### CLI Tools Available
| Category | Tools | Description |
|----------|-------|-------------|
| **Network Scanning** | `nmap`, `naabu`, `nping` | Network scanning tools |
| **Web Reconnaissance** | `httpx`, `ffuf`, `dirsearch` | Web testing tools |
| **Vulnerability Scanning** | `nuclei`, `sqlmap`, `wapiti` | Security scanners |
| **Exploitation** | `metasploit`, `burpsuite`, `hydra` | Exploitation frameworks |
| **Post-Exploitation** | `john`, `hashcat`, `gobuster` | Password cracking tools |

## 📊 Performance Documentation

### Token Savings
- **Traditional CLI**: ~24,000 tokens per step (subprocess overhead)
- **MCP Integration**: ~6,000-8,000 tokens total (no subprocess overhead)
- **Savings**: 60-80% reduction in multi-tool workflows

### Response Comparison
| Feature | CLI Mode | MCP Mode |
|---------|----------|----------|
| Response Format | Raw text | Structured JSON |
| Error Handling | Basic | Advanced with retry |
| State Management | Manual | Automatic |
| Tool Chaining | Shell escaping | Native integration |
| Monitoring | Basic | Comprehensive |

## 🚀 Deployment Documentation

### Development Environment
```bash
# Quick start for development
./scripts/manage.py start
./scripts/manage.py status
curl http://localhost:8000/health
```

### Production Environment
```bash
# Production deployment
docker-compose -f docker-compose.full.yml up -d
./scripts/manage.py logs --follow
```

### Monitoring and Logging
```bash
# Check all services
./scripts/manage.py status

# View logs
./scripts/manage.py logs --follow

# Health checks
curl http://localhost:8000/health
curl http://localhost:8000/tools
```

## 📚 Learning Path

### For Beginners
1. Start with [QUICK_START.md](QUICK_START.md)
2. Try CLI mode for manual usage
3. Explore basic tools (nmap, file operations)

### For AI Developers
1. Read [MCP_USAGE.md](../MCP_USAGE.md) 
2. Try [pentest-recon-mcp](../../.pi/skills/pentest-recon-mcp/) skill
3. Explore token savings and performance benefits

### For System Administrators
1. Review [AUTO_STARTUP.md](../AUTO_STARTUP.md)
2. Use [migration script](../scripts/migrate.py)
3. Set up monitoring and logging

## 🔍 Troubleshooting

### Common Issues
- **Port conflicts**: Use `./scripts/manage.py start --port 8001`
- **Docker issues**: `docker info` and `docker logs opspectre-sandbox`
- **MCP server**: `curl http://localhost:8000/health`
- **Permissions**: `chmod +x scripts/*.py`

### Logs Location
```bash
# All logs
./scripts/manage.py logs --follow

# Specific service logs
./scripts/manage.py logs --service opspectre-mcp --follow
./scripts/manage.py logs --service opspectre-sandbox --follow
```

## 📈 Roadmap

### Completed Features
- ✅ MCP server implementation
- ✅ Auto-startup system
- ✅ 19+ MCP tools
- ✅ Complete documentation update
- ✅ Migration guide and script
- ✅ Performance optimization
- ✅ Health monitoring

### Planned Features
- 🔄 Enhanced error handling
- 🔄 Advanced monitoring (Prometheus)
- 🔄 Multi-tenant support
- 🔄 GPU acceleration
- 🔄 Web dashboard
- 🔄 API authentication

## 📞 Support

### Documentation Resources
1. **Primary**: README.md and MCP_USAGE.md
2. **Migration**: MIGRATION_GUIDE.md and scripts/migrate.py
3. **Tools**: opspectre-tools.md
4. **Examples**: pentest-recon-mcp/README.md

### Community Support
- GitHub Issues: Report bugs and request features
- Discussion: Ask questions and share experiences
- Documentation: Help improve docs

---

**Quick Navigation:**
- [Quick Start](QUICK_START.md) - Get started in 5 minutes
- [MCP Usage](../MCP_USAGE.md) - Complete tool reference
- [Migration Guide](MIGRATION_GUIDE.md) - Move to new system
- [Tools Reference](opspectre-tools.md) - All available tools
- [Auto Startup](../AUTO_STARTUP.md) - Production deployment
- [Main README](../README.md) - Complete overview