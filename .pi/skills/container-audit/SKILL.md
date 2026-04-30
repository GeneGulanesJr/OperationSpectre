---
name: container-audit
description: Scans Docker images and containers for vulnerabilities using trivy from the opspectre sandbox. Use when auditing container security.
---

# Container Security Audit

Vulnerability scanning and security auditing for Docker images and containers using trivy in the OperationSpectre sandbox. Also supports Dockerfile linting, secret scanning, and compliance checks.

## Prerequisites

- OperationSpectre sandbox running (`opspectre sandbox start`)
- Docker accessible from the host (trivy scans are run from the sandbox but target images on the host)
- Target image name or container name

## Rate-Limit Defaults

Not typically needed for local scanning, but available if scanning remote registries:
```bash
$RL_NUCLEI  # nuclei: -rl 15 -bs 25 -c 5 -timeout 15 -retries 2
$RL_HTTPX   # httpx: -rate-limit 5 -timeout 15 -retries 2
random_ua   # Returns a random User-Agent string
```

## Image Scanning

### Scan Image (Full Report)
```bash
opspectre shell "trivy image <IMAGE_NAME> -o /workspace/output/container-audit/image-report.txt"
```

### Scan Image (JSON)
```bash
opspectre shell "trivy image <IMAGE_NAME> -f json -o /workspace/output/container-audit/image-report.json"
```

### Scan Image (SARIF for CI/CD)
```bash
opspectre shell "trivy image <IMAGE_NAME> -f sarif -o /workspace/output/container-audit/image-report.sarif"
```

### Scan Image (HTML Report)
```bash
opspectre shell "trivy image <IMAGE_NAME> -f html -o /workspace/output/container-audit/image-report.html"
```

## Vulnerability Filtering

### Critical & High Only
```bash
opspectre shell "trivy image <IMAGE_NAME> --severity HIGH,CRITICAL -o /workspace/output/container-audit/image-critical.txt"
```

### By Type (OS vs Library)
```bash
opspectre shell "trivy image <IMAGE_NAME> --vuln-type os -o /workspace/output/container-audit/os-vulns.txt"
opspectre shell "trivy image <IMAGE_NAME> --vuln-type library -o /workspace/output/container-audit/lib-vulns.txt"
```

### Ignore Fixed Vulnerabilities
```bash
opspectre shell "trivy image <IMAGE_NAME> --ignore-unfixed -o /workspace/output/container-audit/fixable-vulns.txt"
```

### Exit Code for CI (fail on critical)
```bash
opspectre shell "trivy image <IMAGE_NAME> --severity HIGH,CRITICAL --exit-code 1 -o /workspace/output/container-audit/ci-check.txt"
```

## Filesystem Scanning

### Scan a Dockerfile
```bash
opspectre shell "trivy fs /workspace/Dockerfile -o /workspace/output/container-audit/dockerfile-scan.txt"
```

### Scan a Project Directory
```bash
opspectre shell "trivy fs /workspace/app/ -o /workspace/output/container-audit/fs-scan.txt"
```

## Config Scanning (Misconfigurations)

### Docker Compose
```bash
opspectre shell "trivy config /workspace/docker-compose.yml -o /workspace/output/container-audit/compose-scan.txt"
```

### Dockerfile Misconfiguration
```bash
opspectre shell "trivy config /workspace/Dockerfile -o /workspace/output/container-audit/dockerfile-config.txt"
```

### Kubernetes Manifests
```bash
opspectre shell "trivy config /workspace/k8s/ -o /workspace/output/container-audit/k8s-scan.txt"
```

### Terraform / CloudFormation
```bash
opspectre shell "trivy config /workspace/infra/ -o /workspace/output/container-audit/infra-scan.txt"
```

## Secret Scanning in Images

### Trivy Secret Scanner
```bash
opspectre shell "trivy image <IMAGE_NAME> --scanners secret -o /workspace/output/container-audit/image-secrets.txt"
```

### Trufflehog Deep Secret Scan
```bash
opspectre shell "trufflehog image <IMAGE_NAME> --json > /workspace/output/container-audit/trufflehog-image-secrets.json"
```

### Git History Secret Scan (source code)
```bash
opspectre shell "trufflehog git https://github.com/<ORG>/<REPO>.git --json > /workspace/output/container-audit/trufflehog-git-secrets.json"
```

## Running Container Scanning

### Scan All Running Containers
```bash
opspectre shell "for c in \$(docker ps --format '{{.Names}}'); do
  echo \"=== Scanning: \$c ===\" && \
  trivy image \$(docker inspect --format='{{.Config.Image}}' \$c) --severity HIGH,CRITICAL -o /workspace/output/container-audit/container-\$c.txt
done"
```

### Scan by Container ID
```bash
opspectre shell "trivy image <IMAGE_ID> -o /workspace/output/container-audit/container-id-scan.txt"
```

## Dockerfile Best Practices Audit

### Manual Dockerfile Checks
```bash
opspectre shell "echo '=== Dockerfile Best Practices ===' && \
  echo '[+] Checking for root user:' && \
  grep -n 'USER' /workspace/Dockerfile || echo '  WARNING: No USER directive found (runs as root)' && \
  echo '[+] Checking for latest tag:' && \
  grep -n ':latest' /workspace/Dockerfile || echo '  OK: No :latest tags found' && \
  echo '[+] Checking for COPY secrets:' && \
  grep -nE 'COPY.*\.env|COPY.*id_rsa|COPY.*credentials' /workspace/Dockerfile || echo '  OK: No secret files copied' && \
  echo '[+] Checking for privileged ports (<1024):' && \
  grep -nE 'EXPOSE\s+[0-9]{1,3}[^0-9]' /workspace/Dockerfile && \
  echo '[+] Checking for --no-install-recommends:' && \
  grep -c 'no-install-recommends' /workspace/Dockerfile && \
  echo '[+] Checking for HEALTHCHECK:' && \
  grep -n 'HEALTHCHECK' /workspace/Dockerfile || echo '  WARNING: No HEALTHCHECK defined' && \
  echo '[+] Checking for .dockerignore:' && \
  ls -la /workspace/.dockerignore 2>/dev/null || echo '  WARNING: No .dockerignore found' && \
  echo '[+] Checking for multi-stage build:' && \
  grep -c 'FROM' /workspace/Dockerfile | awk '{if(\$1>1) print \"  OK: Multi-stage build (\" \$1 \" stages)\"; else print \"  WARNING: Single-stage build\"}'"
```

### Check Image Size
```bash
opspectre shell "docker images <IMAGE_NAME> --format '{{.Size}}'"
```

## Comparative Scans

Scan multiple images and compare:
```bash
opspectre shell "trivy image <IMAGE_V1> -f json -o /workspace/output/container-audit/v1.json"
opspectre shell "trivy image <IMAGE_V2> -f json -o /workspace/output/container-audit/v2.json"
```

## Container Network Security

### Check Exposed Ports
```bash
opspectre shell "docker ps --format '{{.Names}}: {{.Ports}}' | grep -v '<none>'"
```

### Check for Privileged Containers
```bash
opspectre shell "docker ps --format '{{.Names}} {{.Image}}' | while read name img; do
  if docker inspect \$name --format '{{.HostConfig.Privileged}}' | grep -q true; then
    echo \"WARNING: \$name (\$img) is running in PRIVILEGED mode\"
  fi
done"
```

### Check for Sensitive Volume Mounts
```bash
opspectre shell "docker ps --format '{{.Names}}' | while read name; do
  echo \"=== \$name ===\" && \
  docker inspect \$name --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}'
done"
```

## Quick Full Audit

```bash
opspectre run "mkdir -p /workspace/output/container-audit && \
  trivy image <IMAGE_NAME> --severity HIGH,CRITICAL -o /workspace/output/container-audit/critical.txt && \
  trivy image <IMAGE_NAME> --scanners secret -o /workspace/output/container-audit/secrets.txt && \
  trivy image <IMAGE_NAME> -f json -o /workspace/output/container-audit/full-report.json && \
  trufflehog image <IMAGE_NAME> --json > /workspace/output/container-audit/trufflehog-secrets.json 2>/dev/null"
```

## Chaining with Other Skills

| After container-audit... | Use this skill | Why |
|--------------------------|---------------|-----|
| Found exposed secrets | `secret-scanner` | Deep scan source code for more secrets |
| Web app in container | `web-app-audit` | Audit the application layer |
| WordPress in container | `wordpress-audit` | WP-specific vulnerability scanning |
| Critical CVEs found | `exploit-dev` | Attempt exploitation if authorized |
| Ready to report | `report-generator` | Generate structured PDF report |

## Output Locations

All results under `/workspace/output/container-audit/`:
- `image-report.txt/json/html/sarif` — full vulnerability report
- `image-critical.txt` — high/critical severity only
- `os-vulns.txt` / `lib-vulns.txt` — filtered by vulnerability type
- `dockerfile-scan.txt` / `fs-scan.txt` — filesystem scans
- `compose-scan.txt` / `dockerfile-config.txt` — misconfiguration scans
- `image-secrets.txt` — trivy secret scan results
- `trufflehog-image-secrets.json` — trufflehog image secret scan
- `trufflehog-git-secrets.json` — trufflehog git history scan
- `container-*.txt` — per-container vulnerability scans

## Tips

- Use `--exit-code 1` to fail CI pipelines on critical vulnerabilities
- Use `.trivyignore` file to suppress known false positives
- Combine with trufflehog for deeper secret scanning of source code
- Scan both the base image and the final application image
- Check Dockerfile best practices before scanning — fix issues at build time
- Run `dockerfile-best-practices-audit` section on all custom Dockerfiles
- Privileged containers + kernel exploits = container escape → critical finding
- Volume mounts to `/`, `/etc`, `/var/run/docker.sock` are high-risk
- Cross-reference trivy CVEs with nuclei templates for known exploits
