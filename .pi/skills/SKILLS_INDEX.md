# OperationSpectre Skill Index
This index catalogs all Hermes agent skill definitions found in `.pi/skills/`. Skills are domain-specific instructions that guide the AI agent through security workflows.
Many skills reference and build upon each other — cross-references are listed under *Depends On*.

## Skills by Category
### Core Pentest
| Skill | Summary | Depends On |
|-------|---------|------------|
| [Container Security Audit](container-audit/SKILL.md) | (see skill doc) | — |
| [Docker Toolchain Management](docker-toolchain/SKILL.md) | (see skill doc) | — |
| [Exploitation Workflow](exploit-dev/SKILL.md) | (see skill doc) | — |
| [Nmap Scan Playbook](nmap-playbook/SKILL.md) | (see skill doc) | — |
| [Passive OSINT Reconnaissance](passive-osint/SKILL.md) | (see skill doc) | — |
| [Pentest Reconnaissance Pipeline (CLI Mode)](pentest-recon/SKILL.md) | (see skill doc) | — |
| [Pentest Report Generator](report-generator/SKILL.md) | (see skill doc) | — |
| [OperationSpectre Sandbox — Tool Reference](sandbox-tools/SKILL.md) | (see skill doc) | — |
| [Secret Scanner](secret-scanner/SKILL.md) | (see skill doc) | — |
| [web-app-audit — Web Application Security Testing](web-app-audit/SKILL.md) | (see skill doc) | — |
| [WordPress Security Audit](wordpress-audit/SKILL.md) | (see skill doc) | — |

### Agent Development
| Skill | Summary | Depends On |
|-------|---------|------------|
| [jCodeMunch — Structured Code Retrieval](jcodemunch/SKILL.md) | (see skill doc) | — |
| [jDocMunch — Structured Documentation Retrieval](jdocmunch/SKILL.md) | (see skill doc) | — |
| [OperationSpectre Development Helper](opspectre-dev/SKILL.md) | (see skill doc) | — |
| [OperationSpectre Security Suite (Consolidated)](opspectre-security-suite/SKILL.md) | (see skill doc) | — |

### Experimental
| Skill | Summary | Depends On |
|-------|---------|------------|
| [Parallel Pipeline Executor](parallel-pipeline-executor/SKILL.md) | (see skill doc) | — |
| [Small Model Pipeline Runner](small-model-pipeline/SKILL.md) | (see skill doc) | — |

### Reference
| Skill | Summary | Depends On |
|-------|---------|------------|
| [ctf-skills](ctf-skills/SKILL.md) | (see skill doc) | — |

## Notes
- Skills are discovered automatically by the Hermes agent from `.pi/skills/` at runtime.
- The agent loads all enabled skills as configured in `.pi/settings.json`.
- Skill folders may contain `pipeline.yaml` (execution definition) and supporting scripts.
