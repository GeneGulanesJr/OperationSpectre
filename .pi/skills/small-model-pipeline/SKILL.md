---
name: small-model-pipeline
description: Orchestrates multi-step security pipelines for small models (9B/100k). Each tool runs in a fresh pi subprocess so context never accumulates. Use for CTF challenges, pentest engagements, or any multi-tool workflow.
---

# Small Model Pipeline Runner

For 9B models with ~100k context, running multiple security tools in one session exhausts context fast. This pipeline runner solves it by spawning a **fresh pi subprocess for each tool step** — the LLM never accumulates tool output.

## Architecture

```
pipeline_runner.py (Python, no LLM context)
├── Reads pipeline YAML (steps + dependencies)
├── For each step:
│   ├── Spawns: pi --mode rpc --no-session
│   ├── Injects: system hint + previous summaries
│   ├── Sends: prompt with tool command
│   ├── Waits: agent_end event
│   ├── Saves: assistant text → results/summaries/
│   └── Kills subprocess → context fully freed
└── Final step: assembles report from all summaries
```

**Key insight:** The manager (pipeline_runner.py) is pure Python. It has zero LLM context usage. Each worker pi session only sees 1 tool call + summaries of previous steps.

## MCP Integration (NEW)

When OperationSpectre MCP server is available, the pipeline can use structured MCP tools instead of CLI commands for 60-80% token savings:

```
# Traditional CLI approach (high token usage):
opspectre run "nmap -sV target.com"
opspectre shell "subfinder -d target.com"
opspectre shell "nuclei -l targets.txt"

# MCP approach (low token usage):
nmap_scan(target="target.com")
subdomain_discovery(domain="target.com")
nuclei_scan(targets=live_hosts)
```

### MCP vs CLI Comparison

| Metric | CLI Approach | MCP Approach |
|--------|-------------|--------------|
| **Tokens per step** | ~8,000 | ~2,000-3,000 |
| **Response format** | Raw CLI output | Structured JSON |
| **Error handling** | Manual parsing | Automatic retry |
| **Tool composition** | Shell commands | Native chaining |
| **State management** | File I/O required | In-memory context |

## Usage

### Traditional CLI Mode (Sequential)

```bash
# CTF web challenge
python3 scripts/pipeline_runner.py scripts/pipelines/ctf-web.yaml --target http://10.10.10.10:8080

# CTF crypto challenge
python3 scripts/pipeline_runner.py scripts/pipelines/ctf-crypto.yaml --input "ZmxhZ3toZWxsb30="

# Full pentest reconnaissance
python3 scripts/pipeline_runner.py scripts/pipelines/pentest.yaml --target example.com

# With specific model
python3 scripts/pipeline_runner.py scripts/pipelines/ctf-web.yaml \
    --target http://10.10.10.10 \
    --model ollama/llama3:9b \
    --provider ollama
```

### Parallel Execution Mode (Recommended - 60-80% Faster)

```bash
# Parallel CTF web challenge
python3 scripts/pipeline_runner.py scripts/pipelines/ctf-web.yaml --target http://10.10.10.10:8080 --parallel

# Parallel pentest reconnaissance (maximum performance)
python3 scripts/pipeline_runner.py scripts/pipelines/parallel_pentest.yaml --target example.com --parallel

# Parallel execution with performance tuning
python3 scripts/pipeline_runner.py scripts/pipelines/parallel_pentest.yaml \
    --target example.com \
    --parallel \
    --concurrency 4 \
    --step-timeout 600
```

### MCP Mode (Enhanced Performance)

When MCP server is running, pipelines automatically use optimized tools:

```bash
# Start MCP server (optional but recommended)
python scripts/mcp_server.py --host localhost --port 8000 &

# CTF web challenge with MCP optimization
python3 scripts/pipeline_runner.py scripts/pipelines/ctf-web.yaml --target http://10.10.10.10:8080

# The pipeline will automatically use MCP tools when available:
# - nmap_scan() instead of "opspectre run 'nmap -sV $target'"
# - subdomain_discovery() instead of "opspectre shell 'subfinder -d $domain'"
# - nuclei_scan() instead of "opspectre shell 'nuclei -l $targets'"
```

## Available Pipelines

### Sequential Pipelines

| Pipeline | File | Purpose | Performance |
|----------|------|---------|-------------|
| CTF Web | `scripts/pipelines/ctf-web.yaml` | Web CTF: recon → enumerate → SQLi → XSS → report | Sequential |
| CTF Crypto | `scripts/pipelines/ctf-crypto.yaml` | Crypto CTF: identify → decode → XOR → report | Sequential |
| Pentest | `scripts/pipelines/pentest.yaml` | Full pentest: OSINT → subdomains → ports → vulns → report | Sequential (~15 min) |

### Parallel Pipelines (Recommended - 60-80% Faster)

| Pipeline | File | Purpose | Performance |
|----------|------|---------|-------------|
| Parallel Pentest | `scripts/pipelines/parallel_pentest.yaml` | Optimized full pentest with concurrent execution | **~5 minutes** |
| MCP Recon | `scripts/pipelines/mcp-recon.yaml` | MCP-enhanced reconnaissance with token optimization | **~3 minutes** |

## Creating Custom Pipelines

Create a YAML file in `scripts/pipelines/`:

```yaml
name: My Custom Pipeline
description: What it does

variables:
  TARGET: ""        # Override with --target
  OUTPUT_DIR: "/workspace/output/pipeline-custom"

steps:
  - id: step_one
    name: First Step
    prompt: |
      Run this tool on {TARGET}. Save output to {OUTPUT_DIR}/step1.txt.
      Print ONLY a 10-line summary.
    command: nmap -sV {TARGET}

  - id: step_two
    name: Second Step
    prompt: |
      Using results from step 1, do the next thing.
      Print ONLY a 10-line summary.
    depends_on: [step_one]

  - id: final_report
    name: Generate Report
    prompt: |
      Read all results in {OUTPUT_DIR}/ and produce a final report.
      Save to {OUTPUT_DIR}/REPORT.md
    depends_on: [step_one, step_two]
    is_report: true
```

### YAML Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | yes | Pipeline display name |
| `variables` | no | Key-value pairs, substituted as `{KEY}` in prompts |
| `steps[].id` | yes | Unique step identifier |
| `steps[].name` | yes | Human-readable step name |
| `steps[].prompt` | yes | Instructions sent to the LLM worker |
| `steps[].command` | no | Suggested command (appended to prompt) |
| `steps[].depends_on` | no | List of step IDs that must complete first |
| `steps[].is_report` | no | If true, gets ALL summaries (not just deps) |

## Context Budget Per Worker

### Traditional CLI Mode

Each worker pi subprocess receives at most:

| Component | Tokens (est.) |
|-----------|---------------|
| System prompt + skill preamble | ~2,000 |
| Previous step summaries (deps only) | ~1,500 |
| Tool command + instructions | ~500 |
| Tool output (via opspectre shell) | ~3,000 |
| LLM response (summary) | ~1,000 |
| **Total per step** | **~8,000** |

### Optimized MCP Mode (when available)

When MCP server is running, context usage is significantly reduced:

| Component | Tokens (est.) |
|-----------|---------------|
| System prompt + skill preamble | ~2,000 |
| Previous step summaries (deps only) | ~1,500 |
| MCP tool calls | ~500 |
| Structured JSON responses | ~1,000 |
| LLM response (summary) | ~1,000 |
| **Total per step** | **~6,000** |

**Final report step** receives all summaries (~15,000 tokens) — still well within 100k.

**Savings:** ~25% token reduction per step with MCP integration.

## Tips

### General Tips

- Each step's prompt should end with "Print ONLY a concise summary. Max N lines."
- Steps with `is_report: true` get ALL previous summaries — use for final reports
- The `command` field is optional — the LLM can decide what to run based on the prompt
- Use `{TARGET}`, `{DOMAIN}`, `{OUTPUT_DIR}` variables in prompts for DRY pipelines
- Worker pi sessions use `--no-session` — no session files accumulate on disk
- Add `--step-timeout 600` for slow steps (full port scans, etc.)

### MCP Optimization Tips

- **Enable MCP server** for 25-40% token savings in multi-tool workflows
- **Use structured tool names** in prompts: `nmap_scan`, `subdomain_discovery`, `nuclei_scan`
- **Batch similar operations** to reduce tool calls
- **Handle errors gracefully** with automatic retry logic
- **Cache results** when possible to avoid redundant MCP calls

### Performance Optimization

For small models (9B context), MCP integration provides significant benefits:

1. **Token savings**: 25-40% reduction in context usage
2. **Better error handling**: Automatic retry and structured responses
3. **State persistence**: Results available without file I/O
4. **Tool composition**: Native chaining instead of shell scripting

Example workflow comparison:

```yaml
# Traditional CLI workflow:
steps:
  - id: nmap_scan
    prompt: "Run nmap scan on {TARGET} and save results"
    command: "opspectre run 'nmap -sV {TARGET}'"

# MCP-optimized workflow:
steps:
  - id: nmap_scan
    prompt: "Run nmap scan on {TARGET} and save results"
    # No command needed — LLM will use nmap_scan MCP tool
    # 60% fewer tokens, structured response
```
