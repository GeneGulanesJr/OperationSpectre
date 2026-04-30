#!/usr/bin/env python3
"""
Complete startup script for OperationSpectre with MCP server

This script starts both the Docker sandbox and MCP server together
for seamless integration.
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def check_requirements():
    """Check if required components are available"""
    print("🔍 Checking requirements...")

    # Check Docker
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True, check=True)
        print(f"✓ Docker: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Docker not found. Please install Docker first.")
        return False

    # Check OperationSpectre
    try:
        result = subprocess.run(['opspectre', '--version'], capture_output=True, text=True, check=True)
        print(f"✓ OperationSpectre: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ OperationSpectre CLI not found. Please install it first.")
        return False

    return True


def start_sandbox():
    """Start OperationSpectre sandbox"""
    print("🚀 Starting OperationSpectre sandbox...")

    try:
        # Check if sandbox is already running
        result = subprocess.run(['opspectre', 'sandbox', 'status'], capture_output=True, text=True)

        if "running" in result.stdout.lower():
            print("✓ Sandbox is already running")
            return True

        # Start sandbox
        result = subprocess.run(['opspectre', 'sandbox', 'start'], capture_output=True, text=True)

        if result.returncode == 0:
            print("✓ Sandbox started successfully")
            return True
        else:
            print(f"✗ Failed to start sandbox: {result.stderr}")
            return False

    except Exception as e:
        print(f"✗ Error starting sandbox: {e}")
        return False


def wait_for_sandbox(timeout=60):
    """Wait for sandbox to be ready"""
    print("⏳ Waiting for sandbox to be ready...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            result = subprocess.run(['opspectre', 'sandbox', 'status'], capture_output=True, text=True)
            if "running" in result.stdout.lower():
                print("✓ Sandbox is ready!")
                return True
        except Exception:
            pass

        time.sleep(2)

    print("✗ Sandbox did not become ready within timeout")
    return False


def start_mcp_server(host='localhost', port=8000):
    """Start MCP server"""
    print(f"🔧 Starting MCP server on {host}:{port}...")

    try:
        # Change to the project directory
        project_dir = Path(__file__).parent.parent
        os.chdir(project_dir)

        # Start MCP server
        command = [
            sys.executable, 'scripts/mcp_server.py',
            '--host', host,
            '--port', port,
            '--log-level', 'INFO'
        ]

        # Start server in background
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Give server time to start
        time.sleep(3)

        # Check if server is running
        try:
            import requests
            response = requests.get(f'http://{host}:{port}/health', timeout=5)
            if response.status_code == 200:
                print(f"✓ MCP server started successfully on {host}:{port}")
                return process
            else:
                print(f"✗ MCP server health check failed: {response.status_code}")
                return None
        except Exception as e:
            print(f"✗ MCP server connection failed: {e}")
            return None

    except Exception as e:
        print(f"✗ Error starting MCP server: {e}")
        return False


def test_mcp_connection(host='localhost', port=8000, timeout=30):
    """Test MCP server connection"""
    print("🔍 Testing MCP server connection...")

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            import requests
            response = requests.get(f'http://{host}:{port}/tools', timeout=5)
            if response.status_code == 200:
                tools = response.json()
                tool_count = len(tools.get('tools', []))
                print(f"✓ MCP server connected with {tool_count} tools available")
                return True
        except Exception:
            pass

        time.sleep(1)

    print("✗ Failed to connect to MCP server")
    return False


def print_status(host='localhost', port=8000):
    """Print current status"""
    print("\n" + "="*60)
    print("🎯 OPERATION SPECTRE STATUS")
    print("="*60)

    # Check sandbox
    try:
        result = subprocess.run(['opspectre', 'sandbox', 'status'], capture_output=True, text=True)
        sandbox_status = "✓ RUNNING" if "running" in result.stdout.lower() else "✗ NOT RUNNING"
        print(f"Sandbox: {sandbox_status}")
    except Exception:
        print("Sandbox: ✗ ERROR")

    # Check MCP server
    try:
        import requests
        response = requests.get(f'http://{host}:{port}/health', timeout=5)
        mcp_status = "✓ RUNNING" if response.status_code == 200 else "✗ NOT RUNNING"
        print(f"MCP Server: {mcp_status}")
    except Exception:
        print("MCP Server: ✗ NOT RUNNING")

    print(f"\n🔗 MCP Server URL: http://{host}:{port}")
    print(f"📚 Tools available: http://{host}:{port}/tools")
    print(f"🏥 Health check: http://{host}:{port}/health")

    print("\n🛠️ Usage Examples:")
    print("  - Python: from pi_pentest_recon_mcp import run_reconnaissance")
    print("  - Pipeline: python3 scripts/pipeline_runner.py scripts/pipelines/mcp-recon.yaml --target example.com")
    print(f"  - Direct: curl http://{host}:{port}/tools")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Start OperationSpectre with MCP server')
    parser.add_argument('--host', default='localhost', help='MCP server host')
    parser.add_argument('--port', type=int, default=8000, help='MCP server port')
    parser.add_argument('--no-wait', action='store_true', help='Don\'t wait for services to be ready')
    parser.add_argument('--skip-sandbox', action='store_true', help='Skip sandbox startup')
    parser.add_argument('--skip-mcp', action='store_true', help='Skip MCP server startup')

    args = parser.parse_args()

    print("🚀 Starting OperationSpectre with MCP Integration")
    print("="*50)

    # Check requirements
    if not check_requirements():
        return 1

    # Start sandbox
    if not args.skip_sandbox:
        if not start_sandbox():
            return 1

        if not args.no_wait:
            if not wait_for_sandbox():
                return 1

    # Start MCP server
    mcp_process = None
    if not args.skip_mcp:
        mcp_process = start_mcp_server(args.host, args.port)

        if not args.no_wait:
            if not test_mcp_connection(args.host, args.port):
                print("⚠️  MCP server may still be starting up...")

    # Print status
    print_status(args.host, args.port)

    # Keep script running if MCP server started
    if mcp_process:
        print("\n🎉 OperationSpectre with MCP server is running!")
        print("Press Ctrl+C to stop both services...")

        try:
            # Wait for MCP process to finish
            mcp_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down services...")

            # Stop sandbox
            try:
                subprocess.run(['opspectre', 'sandbox', 'stop'], capture_output=True)
                print("✓ Sandbox stopped")
            except Exception:
                print("✗ Error stopping sandbox")

            # Stop MCP server
            if mcp_process:
                mcp_process.terminate()
                print("✓ MCP server stopped")

            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
