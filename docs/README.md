# OperationSpectre Documentation

Welcome to the OperationSpectre documentation. This index organizes the docs by category.

## Getting Started

Start here if you're new to OperationSpectre.

- **[QUICK_START.md](getting-started/QUICK_START.md)** — Set up the sandbox, run your first scan, and understand basic usage within 10 minutes.
- *(future: installation guide, tutorial series)*

## Reference

Technical details: CLI commands, configuration, pipeline definitions, and code architecture.

- **[CLI_REFERENCE.md](reference/CLI_REFERENCE.md)** — Complete list of CLI subcommands (`sandbox`, `file`, `code`, `browser`, `performance`, etc.) with options and examples.
- **[PIPELINES.md](reference/PIPELINES.md)** — Pipeline YAML format, step definitions, dependencies, and parallel execution configuration.
- **[PLAN.md](reference/PLAN.md)** — Project development plan, roadmap, and architectural decisions.
- **[DOCUMENTATION_INDEX.md](reference/DOCUMENTATION_INDEX.md)** — Comprehensive index of all documentation, skill catalog, and cross-references.

## Playbooks

Step-by-step guides for specific security tasks and toolchains.

- **[BURP_SUITE_VERIFICATION.md](playbooks/BURP_SUITE_VERIFICATION.md)** — Using Burp Suite for web app assessment.
- **[CONTAINER_PLAYBOOKS.md](playbooks/CONTAINER_PLAYBOOKS.md)** — Docker-based tool execution patterns.
- **[FULL_ARSENAL_README.md](playbooks/FULL_ARSENAL_README.md)** — Complete listing of available tools in the arsenal.
- **[WEB_APP_AUDIT.md](playbooks/WEB_APP_AUDIT.md)** — Web application penetration testing methodology.

## About

Conceptual and operational background.

- **[parallel_execution.md](about/parallel_execution.md)** — How parallel pipeline execution works under the hood.

## Operations

Performance, monitoring, and deployment notes.

- **[PERFORMANCE_ALWAYS_ON.md](operations/PERFORMANCE_ALWAYS_ON.md)** — Continuous performance monitoring setup.
- **[PERFORMANCE_IMPLEMENTATION.md](operations/PERFORMANCE_IMPLEMENTATION.md)** — Implementation details of the performance system.
- *(future: deployment, admin, scaling)*

---

## Skill Catalog

Hermes agent skills are defined in `.pi/skills/`. See `.pi/skills/SKILLS_INDEX.md` for a complete, categorized listing of all available skills and their purposes.

## Repo Structure

```
OperationSpectre/
├── src/opspectre/          # Main Python package
├── .pi/skills/             # Hermes skill definitions
├── pipelines/              # Pipeline YAML definitions
├── scripts/                # Helper scripts (build, start, demos)
├── containers/             # Docker configs (Dockerfile, compose, wrappers, playbooks)
├── docs/                   # This documentation tree
├── tests/                  # Test suite (currently minimal)
├── .gitignore
├── pyproject.toml
└── README.md
```

For development setup, see `docs/getting-started/QUICK_START.md`. For a high-level overview, read `docs/about/README.md` (forthcoming).
