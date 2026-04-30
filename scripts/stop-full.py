#!/usr/bin/env python3
"""
Shutdown script for OperationSpectre with MCP server

This script cleanly stops both the Docker sandbox and MCP server.
"""

import argparse
import subprocess
import sys
import time


def stop_mcp_server(host='localhost', port=8000):
    """Stop MCP server gracefully"""
    print("🛑 Stopping MCP server...")

    try:
        import requests

        # Try graceful shutdown first
        _response = requests.post(f'http://{host}:{port}/shutdown', timeout=5)

        # Wait a bit for server to shutdown
        time.sleep(2)

        # Check if server is still running
        try:
            health_response = requests.get(f'http://{host}:{port}/health', timeout=2)
            if health_response.status_code == 200:
                print("⚠️  MCP server did not shutdown gracefully, force terminating...")
                # Force terminate by killing the process
                subprocess.run(['pkill', '-f', 'mcp_server.py'], timeout=5)
        except Exception:
            # Server is already down
            pass

        print("✓ MCP server stopped")
        return True

    except Exception as e:
        print(f"✗ Error stopping MCP server: {e}")
        return False


def stop_sandbox():
    """Stop OperationSpectre sandbox"""
    print("🛑 Stopping OperationSpectre sandbox...")

    try:
        result = subprocess.run(['opspectre', 'sandbox', 'stop'], capture_output=True, text=True)

        if result.returncode == 0:
            print("✓ Sandbox stopped")
            return True
        else:
            print(f"⚠️  Sandbox stop returned: {result.stderr}")
            return False

    except Exception as e:
        print(f"✗ Error stopping sandbox: {e}")
        return False


def check_status():
    """Check current status of services"""
    print("📊 Checking current status...")

    # Check MCP server
    mcp_running = False
    try:
        import requests
        response = requests.get('http://localhost:8000/health', timeout=2)
        if response.status_code == 200:
            mcp_running = True
            print("✓ MCP server: RUNNING")
        else:
            print("✗ MCP server: NOT RUNNING")
    except Exception:
        print("✗ MCP server: NOT RUNNING")

    # Check sandbox
    sandbox_running = False
    try:
        result = subprocess.run(['opspectre', 'sandbox', 'status'], capture_output=True, text=True)
        if "running" in result.stdout.lower():
            sandbox_running = True
            print("✓ Sandbox: RUNNING")
        else:
            print("✗ Sandbox: NOT RUNNING")
    except Exception:
        print("✗ Sandbox: NOT RUNNING")

    return mcp_running or sandbox_running


def force_cleanup():
    """Force cleanup if services are still running"""
    print("🧹 Performing force cleanup...")

    # Kill any remaining MCP server processes
    try:
        subprocess.run(['pkill', '-f', 'mcp_server.py'], capture_output=True)
        print("✓ Killed any remaining MCP server processes")
    except Exception:
        pass

    # Kill any remaining OperationSpectre processes
    try:
        subprocess.run(['pkill', '-f', 'opspectre'], capture_output=True)
        print("✓ Killed any remaining OperationSpectre processes")
    except Exception:
        pass

    # Force stop docker containers
    try:
        result = subprocess.run(
            ['docker', 'ps', '-q', '--filter', 'name=opspectre'],
            capture_output=True, text=True
        )
        container_ids = result.stdout.strip()
        if container_ids:
            subprocess.run(
                ['docker', 'stop', *container_ids.splitlines()],
                capture_output=True
            )
        print("✓ Stopped any running Docker containers")
    except Exception:
        pass

    print("✓ Force cleanup completed")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Stop OperationSpectre and MCP server')
    parser.add_argument('--host', default='localhost', help='MCP server host')
    parser.add_argument('--port', type=int, default=8000, help='MCP server port')
    parser.add_argument('--force', action='store_true', help='Force cleanup if services are stuck')
    parser.add_argument('--status', action='store_true', help='Show current status without stopping')

    args = parser.parse_args()

    print("🛑 Stopping OperationSpectre with MCP Integration")
    print("="*50)

    # Show status if requested
    if args.status:
        check_status()
        return 0

    # Check what's running
    services_running = check_status()

    if not services_running:
        print("✅ No services are currently running")
        return 0

    # Stop MCP server first (graceful)
    stop_mcp_server(args.host, args.port)

    # Stop sandbox
    stop_sandbox()

    # Wait a moment for services to fully stop
    time.sleep(1)

    # Check if any services are still running
    if args.force:
        print("⚠️  Some services may still be running, forcing cleanup...")
        force_cleanup()

    print("\n🎉 All services stopped successfully!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
