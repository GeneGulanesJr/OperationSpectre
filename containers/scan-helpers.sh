#!/bin/bash
# ============================================================
# SCAN HELPERS - Shared output directory utilities
# ============================================================
# Source this in playbooks and agent scripts for consistent
# scan output naming: scan_runs/ToolName_SiteName_Timestamp/
# ============================================================

export SCAN_RUNS_DIR="/workspace/scan_runs"
mkdir -p "$SCAN_RUNS_DIR"

# Extract a clean site name from a URL
# Usage: site_name "https://www.example.com:8080/path"  =>  "example-com"
site_name() {
    local url="$1"
    echo "$url" | sed -E 's|https?://||' | sed -E 's|:.*||' | sed -E 's|^www\.||' | sed -E 's|\.|-|g'
}

# Create a scan output directory with standard naming
# Usage: scan_dir "BurpSuite" "https://example.com"
# Returns: path to /workspace/scan_runs/BurpSuite_example-com_20260410_203300/
scan_dir() {
    local tool="$1"
    local url="$2"
    local site=$(site_name "$url")
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local dir="$SCAN_RUNS_DIR/${tool}_${site}_${timestamp}"
    mkdir -p "$dir"
    echo "$dir"
}
