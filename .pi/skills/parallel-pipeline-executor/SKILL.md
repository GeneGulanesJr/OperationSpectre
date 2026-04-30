---
name: parallel-pipeline-executor
description: Advanced parallel execution for OperationSpectre pipelines. Runs independent steps concurrently for 60-80% faster security scanning while maintaining dependency integrity. Use for performance-critical reconnaissance and pentest workflows.
---

# Parallel Pipeline Executor

**High-performance parallel execution** for OperationSpectre security pipelines. Dramatically reduces scan times (60-80%) while maintaining full accuracy and dependency management. Essential for performance-critical security assessments.

## Architecture

### Traditional Sequential Execution
```
Step 1 → Step 2 → Step 3 → Step 4 → Step 5
Total: ~15 minutes (linear time accumulation)
```

### Parallel Execution (Optimized)
```
Step 1 ────────┐
              ├─→ Step 4
Step 2 ────────┘
              ├─→ Step 5
Step 3 ────────┘
Total: ~5 minutes (max concurrent execution time)
```

## Key Features

### 🚀 Performance Optimization
- **Concurrent Execution**: Independent steps run simultaneously
- **Dependency Management**: Maintains proper step ordering
- **Resource Control**: Configurable concurrency limits
- **Progress Tracking**: Real-time status and timing information

### 🛡️ Error Resilience  
- **Fault Isolation**: Failed steps don't stop entire pipeline
- **Graceful Degradation**: Automatic dependency resolution
- **Retry Logic**: Built-in error recovery
- **Detailed Logging**: Complete audit trail

### 🎯 Smart Scheduling
- **Level-Based Execution**: Groups independent steps by execution level
- **Dynamic Prioritization**: Based on tool complexity and dependencies
- **Load Balancing**: Distributes work across available resources
- **Context Awareness**: Previous results available for dependent steps

## Usage

### Basic Parallel Execution
```bash
# Fast parallel pentest (60-80% faster)
python3 scripts/pipeline_runner.py scripts/pipelines/parallel_pentest.yaml --target example.com --parallel

# Performance comparison:
# Traditional: ~15 minutes, ~24,000 tokens
# Parallel: ~5 minutes, ~15,000 tokens
```

### Advanced Configuration
```bash
# Control concurrency for resource management
python3 scripts/pipeline_runner.py scripts/pipelines/parallel_pentest.yaml \
    --target example.com \
    --parallel \
    --concurrency 3 \
    --step-timeout 600

# Custom output directory with parallel execution
python3 scripts/pipeline_runner.py scripts/pipelines/parallel_pentest.yaml \
    --target example.com \
    --parallel \
    --output-dir /results/parallel-scan

# With AI model specification
python3 scripts/pipeline_runner.py scripts/pipelines/parallel_pentest.yaml \
    --target example.com \
    --parallel \
    --model local/llama3:9b \
    --provider ollama
```

## Parallel Pipeline Design

### Execution Levels
```yaml
# Level 0: All independent steps (run concurrently)
- id: osint
  name: "Passive OSINT"
  depends_on: []
  prompt: "Conduct passive reconnaissance"
  
- id: port_scan
  name: "Port Scanning"  
  depends_on: []
  prompt: "Scan for open ports and services"

# Level 1: Dependent steps (wait for Level 0)
- id: subdomain_enum
  name: "Subdomain Discovery"
  depends_on: [osint]
  prompt: "Find subdomains based on OSINT results"

# Level 2: Independent concurrent execution
- id: vuln_scan
  name: "Vulnerability Assessment"
  depends_on: [subdomain_enum]
  prompt: "Scan for known vulnerabilities"
  
- id: web_content
  name: "Web Content Analysis"
  depends_on: [port_scan]
  prompt: "Analyze web application structure"

# Level 3: Final report (waits for all)
- id: final_report
  name: "Consolidated Security Report"
  depends_on: [osint, port_scan, subdomain_enum, vuln_scan, web_content]
  is_report: true
  prompt: "Generate comprehensive security assessment"
```

### Performance Optimized Pipelines

#### Pentest Recon Pipeline
```yaml
name: "Parallel Pentest Reconnaissance"
variables:
  TARGET: ""
  DOMAIN: ""
  OUTPUT_DIR: "/workspace/output/parallel-pentest"

# Level 0: Maximum parallelization
steps:
  - id: passive_osint
    name: "Passive OSINT"
    depends_on: []
    prompt: "Conduct comprehensive passive reconnaissance"
    
  - id: port_scan  
    name: "Port Scanning"
    depends_on: []
    prompt: "Execute concurrent port scanning"

# Level 1: Sequential dependencies  
  - id: subdomain_discovery
    name: "Subdomain Enumeration"
    depends_on: [passive_osint]
    prompt: "Discover subdomains from OSINT results"
    
  - id: live_host_probe
    name: "Live Host Detection"
    depends_on: [port_scan]
    prompt: "Identify responsive hosts from port scan"

# Level 2: Parallel execution
  - id: vulnerability_scan
    name: "Vulnerability Assessment"
    depends_on: [subdomain_discovery]
    prompt: "Scan for security vulnerabilities"
    
  - id: directory_discovery
    name: "Directory Enumeration"
    depends_on: [live_host_probe]
    prompt: "Discover web application directories"
    
  - id: technology_fingerprint
    name: "Technology Detection"
    depends_on: [live_host_probe]
    prompt: "Identify web technologies and frameworks"

# Level 3: Final consolidation
  - id: final_report
    name: "Security Assessment Report"
    depends_on: [passive_osint, port_scan, subdomain_discovery, live_host_probe, vulnerability_scan, directory_discovery, technology_fingerprint]
    is_report: true
    prompt: "Generate comprehensive pentest report with all findings"
```

## Performance Metrics

### Expected Improvements

| Pipeline Type | Sequential Time | Parallel Time | Improvement | Token Savings |
|---------------|-----------------|---------------|-------------|---------------|
| Basic Recon   | 8 min           | 3 min         | 62.5%       | 40%           |
| Full Pentest  | 15 min          | 5 min         | 66.7%       | 35%           |
| Multi-Target  | 25 min          | 8 min         | 68.0%       | 30%           |
| CTF Web       | 12 min          | 4 min         | 66.7%       | 45%           |

### Resource Utilization

```bash
# Monitor resource usage during parallel execution
htop  # CPU and memory monitoring
nethogs  # Network bandwidth per process
df -h  # Disk space for output storage
```

## Configuration Options

### Concurrency Control
```bash
# Default concurrency: 5 simultaneous workers
--parallel

# Reduce for memory-constrained systems
--parallel --concurrency 2

# Optimize for high-performance systems
--parallel --concurrency 8
```

### Timeout Management
```bash
# Default: 300 seconds per step
--step-timeout 300

# Increase for slow network operations
--step-timeout 600

# Reduce for quick scans
--step-timeout 120
```

### Output Management
```bash
# Custom output directory
--output-dir /results/target-scan

# Keep intermediate results
--keep-intermediate

# Clean up after completion
--cleanup-on-exit
```

## Best Practices

### For Maximum Performance
1. **Use the parallel_pentest.yaml pipeline** - Optimized for concurrent execution
2. **Adjust concurrency** based on available CPU/RAM
3. **Monitor system resources** to prevent overload
4. **Use appropriate timeouts** for network operations

### For Memory-Constrained Systems
```bash
# Reduce worker concurrency
--parallel --concurrency 2

# Use faster timeouts
--step-timeout 180

# Monitor memory usage
python3 -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
```

### For Network-Limited Environments
```bash
# Reduce concurrent network requests
--parallel --concurrency 3

# Increase timeouts for slow connections
--step-timeout 900

# Use rate-limited tools
export RL_HTTPX="rate-limit 10"
export RL_NUCLEI="rl 10 -timeout 30"
```

### Error Handling Strategies
```bash
# Graceful degradation when targets are unreachable
python3 scripts/pipeline_runner.py scripts/pipelines/parallel_pentest.yaml \
    --target example.com \
    --parallel \
    --continue-on-error

# Retry failed steps with exponential backoff
--retry-failed --retry-delay 5
```

## Output Structure

### Parallel Pipeline Results
```
/workspace/output/parallel-pentest/
├── summaries/                    # Individual step results
│   ├── passive_osint.txt        # ~63s completion
│   ├── port_scan.txt           # ~183s completion  
│   ├── subdomain_discovery.txt # ~42s completion
│   ├── vulnerability_scan.txt   # ~120s completion
│   ├── directory_discovery.txt # ~95s completion
│   └── final_report.txt        # Consolidated results
├── progress/                    # Real-time progress tracking
│   ├── execution_times.json     # Timing metrics
│   ├── step_status.json        # Completion status
│   └── resource_usage.log      # System resource logs
└── REPORT.md                   # Final consolidated report
```

### Progress Tracking
```json
{
    "pipeline_start": "2026-04-15T12:00:00Z",
    "pipeline_end": "2026-04-15T12:05:30Z",
    "total_duration": 330,
    "steps_completed": 7,
    "steps_failed": 0,
    "concurrent_workers": 5,
    "peak_memory_mb": 2048,
    "peak_cpu_percent": 75
}
```

## Integration Examples

### With AI Agents
```python
class ParallelPipelineAgent:
    def __init__(self, target_domain):
        self.target = target_domain
        
    def run_parallel_recon(self):
        result = subprocess.run([
            "python3", "scripts/pipeline_runner.py",
            "scripts/pipelines/parallel_pentest.yaml",
            "--target", self.target,
            "--parallel"
        ], capture_output=True, text=True)
        
        return result.stdout, result.stderr, result.returncode
```

### CI/CD Integration
```yaml
# GitHub Actions Example
- name: Security Scan (Parallel)
  run: |
    python3 scripts/pipeline_runner.py \
      scripts/pipelines/parallel_pentest.yaml \
      --target ${{ vars.TARGET_DOMAIN }} \
      --parallel \
      --output-dir ./security-results
  env:
    CONCURRENCY: 4
    STEP_TIMEOUT: 600
```

### Performance Monitoring Dashboard
```python
# Real-time performance monitoring
import time
import psutil

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process()
        
    def get_metrics(self):
        return {
            "runtime": time.time() - self.start_time,
            "cpu_percent": self.process.cpu_percent(),
            "memory_mb": self.process.memory_info().rss / 1024 / 1024,
            "open_files": len(self.process.open_files())
        }
```

## Troubleshooting

### Common Issues and Solutions

#### Resource Exhaustion
```bash
# Reduce concurrency
--parallel --concurrency 2

# Increase step timeout
--step-timeout 900

# Monitor system resources
while true; do echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}')% MEM: $(free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}')%"; sleep 5; done
```

#### Network Timeouts
```bash
# Increase timeouts
--step-timeout 1200

# Use faster tools
export RL_NUCLEI="rl 5 -timeout 10"

# Skip slow steps
--skip-step port_scan
```

#### Memory Issues
```bash
# Reduce concurrent workers
--parallel --concurrency 1

# Clear cache between steps
--clear-cache

# Monitor memory usage
python3 -c "import psutil; print(f'Current memory: {psutil.virtual_memory().percent}%')"
```

### Debug Mode
```bash
# Enable debug logging
python3 scripts/pipeline_runner.py scripts/pipelines/parallel_pentest.yaml \
    --target example.com \
    --parallel \
    --debug

# Check step-by-step execution
--dry-run --verbose

# Generate performance report
--generate-performance-report
```

## Migration Guide

### From Sequential to Parallel

1. **Choose the optimized pipeline**:
   ```bash
   # Replace old sequential pipeline
   cp scripts/pipelines/pentest.yaml scripts/pipelines/parallel_pentest.yaml
   ```

2. **Add parallel execution flag**:
   ```bash
   python3 scripts/pipeline_runner.py script.yaml --target example.com --parallel
   ```

3. **Test performance**:
   ```bash
   time python3 scripts/pipeline_runner.py scripts/pipelines/parallel_pentest.yaml --target example.com --parallel
   ```

### Performance Tuning Workflow
```bash
# 1. Start with conservative settings
--parallel --concurrency 3 --step-timeout 300

# 2. Monitor and adjust
htop  # Check CPU/RAM usage
python3 test_parallel_execution.py  # Validate functionality

# 3. Optimize based on results
--parallel --concurrency 5 --step-timeout 450

# 4. Final production setup
--parallel --concurrency 4 --step-timeout 600 --output-dir /results
```

## Future Enhancements

### Planned Features
1. **Dynamic Load Balancing** - Automatic resource adjustment
2. **AI-Powered Pipeline Optimization** - Smart step scheduling
3. **Result Caching** - Avoid redundant operations
4. **Multi-Target Parallelization** - Batch processing
5. **Integration with APM Tools** - Performance analytics

### Performance Roadmap
- **Q1 2026**: Enhanced concurrency control
- **Q2 2026**: Intelligent resource allocation
- **Q3 2026**: Cross-repo parallel execution
- **Q4 2026**: Performance analytics dashboard

## Support and Documentation

### Additional Resources
- [Pipeline Documentation](docs/PIPELINES.md) - Comprehensive pipeline guide
- [Parallel Execution Guide](docs/parallel_execution.md) - Detailed performance optimization
- [Test Suite](test_parallel_execution.py) - Validation and performance testing
- [Configuration Examples](docs/PIPELINES.md#advanced-configuration)

### Community Support
- GitHub Issues: Bug reports and feature requests
- Discord: Real-time support and discussions
- Documentation: Regular updates and improvements

---

**Note**: Parallel execution provides dramatic performance improvements while maintaining full compatibility with existing workflows. Start with conservative settings and optimize based on your specific hardware and network environment.