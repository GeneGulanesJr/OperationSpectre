# OperationSpectre Documentation Index

This index provides a comprehensive overview of all OperationSpectre documentation, organized by topic and audience.

## 📖 Documentation Overview

### Primary Documentation
| Document | Description | Audience | Status |
|----------|-------------|----------|---------|
| [README.md](../README.md) | Main documentation with pi-based execution | All users | ✅ Updated |
| [QUICK_START.md](QUICK_START.md) | Quick start guide with both CLI and CLI modes | New users | ✅ Updated |

### Migration Documentation
| Document | Description | Status |
|----------|-------------|---------|
| [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) | Complete migration from old to new system | ✅ New |
| scripts/migrate.py | Automated migration script | ✅ New |

### Tool-Specific Documentation
| Document | Description | Status |
|----------|-------------|---------|
| [opspectre-tools.md](opspectre-tools.md) | Complete tools list with pi-based execution | ✅ Updated |
| [web-app-audit.md](web-app-audit.md) | Web application auditing guide | ✅ Updated |
| [parallel_execution.md](parallel_execution.md) | Parallel execution optimization guide | ✅ New |
| [PIPELINES.md](PIPELINES.md) | Complete pipeline documentation and usage | ✅ New |

### Skills Documentation
| Document | Description | Status |
|----------|-------------|---------|
| [pentest-recon/SKILL.md](../../.pi/skills/pentest-recon/SKILL.md) | Traditional reconnaissance pipeline | ⚠️ Needs update |

## 🎯 Quick Start Guides

### For New Users
1. **Start Here**: [QUICK_START.md](QUICK_START.md) - Choose between CLI and CLI modes
2. **Migration**: [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - If coming from old system
4. **Automated Workflows**: [PIPELINES.md](PIPELINES.md) - Multi-step security pipelines

### For System Administrators
2. **Migration Script**: [scripts/migrate.py](../scripts/migrate.py) - Automated migration
3. **Docker Configuration**: [docker-compose.full.yml](../docker-compose.full.yml) - Container orchestration
4. **Pipeline Management**: [scripts/pipeline_runner.py](../scripts/pipeline_runner.py) - Automated workflows
5. **Performance Optimization**: [parallel_execution.md](parallel_execution.md) - 60-80% faster execution

### For AI Developers
3. **Automated Pipelines**: [scripts/pipeline_runner.py](../scripts/pipeline_runner.py) - Multi-step workflows
4. **Parallel Execution**: [parallel_execution.md](parallel_execution.md) - Performance optimization

## 🏗️ Architecture Documentation

### Pi-Only Architecture
OperationSpectre now supports two execution modes:

#### CLI Mode (Traditional)
```
User → CLI → Docker Container → 50+ Tools
    ↓      ↓      ↓           ↓
Manual  Text   Fast        Full Kali Arsenal
                CLI        Playbooks Embedded
```

### Integration Points
- **AI Agent Integration**: pi-pentest-recon tools provide structured JSON responses
- **CLI Backward Compatibility**: Existing CLI commands work unchanged
- **Container Orchestration**: Docker Compose manages Docker sandbox and sandbox
- **Monitoring**: Health checks, logging, and status management

## 🔧 Tool Reference

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
- **Savings**: 60-80% reduction in multi-tool workflows

### Response Comparison
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
3. Explore token savings and performance benefits

### For System Administrators
2. Use [migration script](../scripts/migrate.py)
3. Set up monitoring and logging

## 🔍 Troubleshooting

### Common Issues
- **Port conflicts**: Use `./scripts/manage.py start --port 8001`
- **Docker issues**: `docker info` and `docker logs opspectre-sandbox`
- **Docker sandbox**: `curl http://localhost:8000/health`
- **Permissions**: `chmod +x scripts/*.py`

### Logs Location
```bash
# All logs
./scripts/manage.py logs --follow

# Specific service logs
  - Service logs: `docker-compose -f docker-compose.full.yml logs -f`
./scripts/manage.py logs --service opspectre-sandbox --follow
```

## 📈 Roadmap

### Completed Features
- ✅ Docker sandbox implementation
- ✅ Auto-startup system
- ✅ 19+ pi-pentest-recon tools
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
2. **Migration**: MIGRATION_GUIDE.md and scripts/migrate.py
3. **Tools**: opspectre-tools.md

### Community Support
- GitHub Issues: Report bugs and request features
- Discussion: Ask questions and share experiences
- Documentation: Help improve docs

---

**Quick Navigation:**
- [Quick Start](QUICK_START.md) - Get started in 5 minutes
- [Migration Guide](MIGRATION_GUIDE.md) - Move to new system
- [Tools Reference](opspectre-tools.md) - All available tools
- [Main README](../README.md) - Complete overview