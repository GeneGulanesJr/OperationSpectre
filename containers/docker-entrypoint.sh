#!/bin/bash
set -e

echo "Starting OPERATIONSPECTRE sandbox..."

# NOTE: DNS override removed for security.
# Docker's bridge network provides its own resolver for internet access.
# Forcing public DNS was leaking host network intent.

# ===== CTF VENV AUTO-ACTIVATION =====
export VIRTUAL_ENV_DISABLE_PROMPT=1
source /opt/ctf-python-venv/bin/activate 2>/dev/null
export PYTHONPATH="/opt/opspectre/tools:/opt/ctf-python-venv/lib/python3.13/site-packages:$PYTHONPATH"
export PATH="/opt/ctf-python-venv/bin:$PATH"

echo "Creating workspace directories..."
mkdir -p /workspace/output/{loot,sessions,logs,scans,exploits,reports}
chmod -R a+rw /workspace/output 2>/dev/null || true

echo "Starting PostgreSQL for Metasploit..."
service postgresql start
sleep 2

echo "Starting tool server..."
cd /opt/opspectre/tools
export PYTHONPATH="/opt/opspectre/tools:/opt/ctf-python-venv/lib/python3.13/site-packages:$PYTHONPATH"
export OPSPECTRE_SANDBOX_MODE=true
export TOOL_SERVER_TIMEOUT="${OPSPECTRE_SANDBOX_EXECUTION_TIMEOUT:-120}"
TOOL_SERVER_LOG="/tmp/tool_server.log"

python3 -m opspectre.sandbox.tool_server \
  --token="$TOOL_SERVER_TOKEN" \
  --host=0.0.0.0 \
  --port="$TOOL_SERVER_PORT" \
  --timeout="$TOOL_SERVER_TIMEOUT" > "$TOOL_SERVER_LOG" 2>&1 &

for i in {1..10}; do
  if curl -s "http://127.0.0.1:$TOOL_SERVER_PORT/health" | grep -q '"status":"healthy"'; then
    echo "Tool server healthy on port $TOOL_SERVER_PORT"
    break
  fi
  if [ $i -eq 10 ]; then
    echo "ERROR: Tool server failed to become healthy"
    echo "=== Tool server log ==="
    cat "$TOOL_SERVER_LOG" 2>/dev/null || echo "(no log)"
    exit 1
  fi
  sleep 1
done

echo "OPERATIONSPECTRE sandbox ready"

cd /workspace
exec "$@"
