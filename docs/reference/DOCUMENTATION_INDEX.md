# OperationSpectre Documentation Index

This index provides a comprehensive overview of all OperationSpectre documentation, organized by topic and audience.

## 📖 Documentation Overview

### Primary Documentation

| Document | Description | Audience | Status |
|----------|-------------|----------|---------|
| [../README.md](../README.md) | Main documentation with pi-based execution | All users | ✅ Updated |
| [../getting-started/QUICK_START.md](../getting-started/QUICK_START.md) | Quick start guide — first scan in 10 minutes | New users | ✅ Updated |

### Tool-Specific Documentation

| Document | Description | Status |
|----------|-------------|---------|
| [../playbooks/FULL_ARSENAL_README.md](../playbooks/FULL_ARSENAL_README.md) | Complete tools list with pi-based execution | ✅ Updated |
| [../playbooks/WEB_APP_AUDIT.md](../playbooks/WEB_APP_AUDIT.md) | Web application auditing guide | ✅ Updated |
| [../about/parallel_execution.md](../about/parallel_execution.md) | Parallel execution optimization guide | ✅ New |
| [PIPELINES.md](PIPELINES.md) | Complete pipeline documentation and usage | ✅ New |

### Skills Documentation

| Document | Description | Status |
|----------|-------------|---------|
| [../../.pi/skills/SKILLS_INDEX.md](../../.pi/skills/SKILLS_INDEX.md) | Catalog of all available Hermes agent skills | ✅ Updated |

## 🎯 Quick Start Guides

### For New Users
1. **Start Here**: [../getting-started/QUICK_START.md](../getting-started/QUICK_START.md) — Set up the sandbox and run your first scan
2. **Pipeline Basics**: [PIPELINES.md](PIPELINES.md) — Multi-step security pipelines

### For System Administrators
1. **Pipeline Runner**: [../../scripts/pipeline_runner.py](../../scripts/pipeline_runner.py) — Automated workflow script
2. **Performance**: [../about/parallel_execution.md](../about/parallel_execution.md) — Parallel execution optimization

### For AI Developers
1. **Skill Catalog**: [../../.pi/skills/SKILLS_INDEX.md](../../.pi/skills/SKILLS_INDEX.md) — Available AI skills
2. **Parallel Execution**: [../about/parallel_execution.md](../about/parallel_execution.md) — Performance optimization

## 🏗️ Architecture Documentation

### Pi-Only Architecture
OperationSpectre runs in a pi-based execution environment with structured tool outputs.

#### Execution Modes
- **CLI Mode** — Traditional text-based tool invocation
- **Pi Mode** — Native process integration with JSON results

### Integration Points
- **AI Agent**: pi-pentest-recon tools provide structured JSON responses
- **CLI Backward Compatibility**: Existing CLI commands work unchanged
- **Container Orchestration**: Docker Compose manages the sandbox

## 🔧 Tool Reference

See the [Full Arsenal](../playbooks/FULL_ARSENAL_README.md) for the complete tool list.

## 📊 Performance

- Token savings: 60–80% reduction in multi-tool workflows
- See [parallel_execution.md](../about/parallel_execution.md) for details

## 🚀 Deployment

### Development
```bash
./scripts/manage.py start
./scripts/manage.py status
```

### Production
```bash
docker-compose -f docker-compose.full.yml up -d
```

See [main README](../README.md) for complete setup instructions.

## 📚 Learning Path

1. [QUICK_START.md](../getting-started/QUICK_START.md)
2. [PIPELINES.md](PIPELINES.md)
3. [FULL_ARSENAL_README.md](../playbooks/FULL_ARSENAL_README.md)

## 🔍 Troubleshooting

Common issues and solutions are documented in the [main README](../README.md) and individual playbooks.

## 📈 Roadmap

See the project [PLAN.md](PLAN.md) for completed features and planned work.

## 📞 Support

- **Documentation**: Browse the playbooks and reference guides above
- **Skills**: Review [SKILLS_INDEX.md](../../.pi/skills/SKILLS_INDEX.md) for AI capabilities

---

**Quick Navigation**
- [Quick Start](../getting-started/QUICK_START.md)
- [Tools Reference](../playbooks/FULL_ARSENAL_README.md)
- [Main README](../README.md)
