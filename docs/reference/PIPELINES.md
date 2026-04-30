# OperationSpectre Pipelines

## Overview

OperationSpectre supports **automated multi-step pipelines** that execute complex security workflows with intelligent dependency management and optional parallel execution for dramatically faster results.

## Pipeline Modes

### 1. Sequential Execution (Original)
```
Step 1 → Step 2 → Step 3 → Step 4 → Step 5
```
Traditional sequential execution for maximum compatibility.

### 2. Parallel Execution (Optimized)
```
Step 1 ────────┐
              ├─→ Step 4
Step 2 ────────┘
              ├─→ Step 5
Step 3 ────────┘
```
Intelligent parallel execution can reduce scan times by **60-80%**.

## Available Pipelines

### 🚀 Parallel Pentest Pipeline (Recommended)
**File**: `pipelines/parallel_pentest.yaml`  
**Performance**: 60-80% faster than sequential  
**Use Case**: Full security pentest with optimized parallel execution

```bash
python3 scripts/pipeline_runner.py pipelines/parallel_pentest.yaml --target example.com --parallel
```

### 🔍 Standard Pentest Pipeline
**File**: `pipelines/pentest.yaml`  
**Performance**: Traditional sequential execution  
**Use Case**: Backward compatibility and debugging

```bash
python3 scripts/pipeline_runner.py pipelines/pentest.yaml --target example.com
```

### 🎯 CTF Web Challenge Pipeline
**File**: `pipelines/ctf-web.yaml`  
**Performance**: Sequential (complex dependencies)  
**Use Case**: Capture-the-flag web challenges

```bash
python3 scripts/pipeline_runner.py pipelines/ctf-web.yaml --target http://10.10.10.10:8080
```

### 🔐 CTF Crypto Challenge Pipeline
**File**: `pipelines/ctf-crypto.yaml`  
**Performance**: Sequential (linear process)  
**Use Case**: Cryptographic challenges

```bash
python3 scripts/pipeline_runner.py pipelines/ctf-crypto.yaml --input "encrypted_string_here"
```

## Pipeline Structure

### Basic Pipeline Format
```yaml
name: "Pipeline Name"
description: "What this pipeline does"
variables:
  TARGET: ""
  DOMAIN: ""
  OUTPUT_DIR: "/workspace/output/pipeline-name"

steps:
  - id: step1
    name: "Step 1 Description"
    prompt: "What this step should accomplish"
    command: "shell command to execute (optional)"
    depends_on: []  # Dependencies on other steps
    is_report: false  # Is this the final report?
```

### Parallel Optimization Strategy

#### Level 0: All Independent Steps
```yaml
- id: osint
  name: "Passive OSINT"
  depends_on: []  # No dependencies
  prompt: "Conduct passive reconnaissance"

- id: port_scan
  name: "Port Scan"
  depends_on: []  # No dependencies  
  prompt: "Scan for open ports and services"
```

#### Level 1: Dependent Steps
```yaml
- id: subdomain_enum
  name: "Subdomain Discovery"
  depends_on: [osint]  # Requires OSINT results
  prompt: "Find subdomains based on OSINT findings"
```

#### Level 2: Parallel Execution
```yaml
- id: vuln_scan
  name: "Vulnerability Scan"
  depends_on: [subdomain_enum]  # Can run with dir_scan
  prompt: "Scan for vulnerabilities"

- id: dir_scan
  name: "Directory Discovery"
  depends_on: [port_scan]  # Independent of vuln_scan
  prompt: "Discover web directories"
```

## Command Line Options

### Basic Usage
```bash
# Run pipeline
python3 scripts/pipeline_runner.py pipelines/parallel_pentest.yaml --target example.com

# With parallel execution (recommended)
python3 scripts/pipeline_runner.py pipelines/parallel_pentest.yaml --target example.com --parallel

# Custom output directory
python3 scripts/pipeline_runner.py pipelines/pentest.yaml --target example.com --output-dir /results

# Specify model
python3 scripts/pipeline_runner.py pipelines/ctf-web.yaml --target http://10.10.10.10 --model local/llama3:9b
```

### Advanced Options
```bash
# Control concurrency
python3 scripts/pipeline_runner.py script.yaml --parallel --concurrency 3

# Adjust timeouts
python3 scripts/pipeline_runner.py script.yaml --parallel --step-timeout 600

# Custom provider
python3 scripts/pipeline_runner.py script.yaml --target example.com --provider ollama
```

## Performance Comparison

| Pipeline Type | Sequential Time | Parallel Time | Improvement |
|---------------|-----------------|---------------|-------------|
| Basic Recon   | 8 min           | 3 min         | 62.5%       |
| Full Pentest  | 15 min          | 5 min         | 66.7%       |
| Multi-Target  | 25 min          | 8 min         | 68.0%       |

## Output Structure

### Sequential Pipeline Output
```
/workspace/output/pentest/
├── summaries/
│   ├── osint.txt
│   ├── port_scan.txt
│   ├── subdomain_enum.txt
│   └── vuln_scan.txt
└── REPORT.md
```

### Parallel Pipeline Output
```
/workspace/output/parallel-pentest/
├── summaries/
│   ├── osint.txt          # Completed in ~63s
│   ├── port_scan.txt      # Completed in ~183s (runs concurrently)
│   ├── subdomain_enum.txt # Completed in ~42s (after osint)
│   ├── dir_enum.txt       # Completed in ~61s (after port_scan)
│   └── final_report.txt   # Consolidates all results
└── REPORT.md              # Final consolidated report
```

## Best Practices

### 1. Pipeline Design
- **Group independent steps** together
- **Minimize dependencies** when possible
- **Use clear naming** for debugging
- **Set appropriate timeouts** for network operations

### 2. Parallel Execution
- **Use --parallel flag** for independent tasks
- **Adjust concurrency** based on available resources
- **Monitor system load** during execution
- **Handle network bandwidth** for concurrent operations

### 3. Error Handling
- Failed dependencies automatically skip dependent steps
- Individual step failures don't stop the entire pipeline
- Detailed error reporting for troubleshooting

### 4. Resource Management
- Limit concurrent workers for memory-constrained systems
- Increase timeouts for slow network operations
- Monitor disk space for large outputs

## Migration Guide

### From Sequential to Parallel

1. **Choose the parallel pipeline**:
   ```bash
   # Replace old sequential pipeline
   cp pipelines/pentest.yaml pipelines/parallel_pentest.yaml
   ```

2. **Add --parallel flag**:
   ```bash
   python3 scripts/pipeline_runner.py script.yaml --target example.com --parallel
   ```

3. **Test performance**:
   ```bash
   python3 test_parallel_execution.py
   ```

### Troubleshooting Common Issues

#### Resource Exhaustion
```bash
# Reduce concurrency
python3 scripts/pipeline_runner.py script.yaml --parallel --concurrency 2

# Increase timeouts for slow operations
python3 scripts/pipeline_runner.py script.yaml --parallel --step-timeout 600
```

#### Dependency Conflicts
```bash
# Review pipeline dependencies in the YAML file
# Ensure dependent steps complete before dependent ones start
```

#### Memory Issues
```bash
# Reduce concurrent workers
python3 scripts/pipeline_runner.py script.yaml --parallel --concurrency 2

# Use custom output directory
python3 scripts/pipeline_runner.py script.yaml --parallel --output-dir /tmp/pipeline
```

## Creating Custom Pipelines

### Example: Web Application Audit Pipeline
```yaml
name: "Web Application Security Audit"
description: "Comprehensive web application security assessment"
variables:
  TARGET: ""
  DOMAIN: ""
  OUTPUT_DIR: "/workspace/output/web-audit"

steps:
  - id: recon
    name: "Initial Reconnaissance"
    prompt: "Conduct passive reconnaissance on the target"
    depends_on: []
  
  - id: port_scan
    name: "Port Enumeration"
    prompt: "Scan for open web ports and services"
    depends_on: []
  
  - id: vuln_scan
    name: "Vulnerability Assessment"
    prompt: "Scan for known web vulnerabilities"
    depends_on: [recon, port_scan]
  
  - id: web_content
    name: "Web Content Analysis"
    prompt: "Analyze web application content and structure"
    depends_on: [port_scan]
  
  - id: final_report
    name: "Security Assessment Report"
    prompt: "Generate comprehensive security assessment report"
    depends_on: [recon, port_scan, vuln_scan, web_content]
    is_report: true
```

## Integration with Other Systems

### AI Agent Workflows
```python
# AI agent can trigger pipelines
pipeline_result = run_pipeline(
    "pipelines/parallel_pentest.yaml",
    target="example.com",
    parallel=True
)
```

### CI/CD Integration
```yaml
# Example GitHub Action
- name: Security Scan
  run: |
    python3 scripts/pipeline_runner.py pipelines/parallel_pentest.yaml \
      --target ${{ vars.TARGET_DOMAIN }} \
      --parallel \
      --output-dir ./security-results
```

## Future Enhancements

1. **Dynamic Pipeline Generation** - AI-powered pipeline creation
2. **Adaptive Concurrency** - Automatic resource adjustment
3. **Caching System** - Result caching for repeated operations
4. **Pipeline Templates** - Pre-built pipeline templates
5. **Performance Analytics** - Detailed performance metrics

## Support

For issues and questions:
1. Check the [parallel execution guide](parallel_execution.md)
2. Run the test suite: `python3 test_parallel_execution.py`
3. Review pipeline logs in the output directory
4. Check system resources during execution