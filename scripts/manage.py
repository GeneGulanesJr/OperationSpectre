#!/usr/bin/env python3
"""
Comprehensive Management Script for OperationSpectre with MCP Integration

This script provides unified management for:
- Docker sandbox
- MCP server
- Development environment
- Production deployment
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


class OperationSpectreManager:
    """Unified manager for OperationSpectre components"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.docker_compose_file = self.project_root / "docker-compose.full.yml"
        self.scripts_dir = self.project_root / "scripts"

    def check_docker_available(self):
        """Check if Docker is available"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ Docker: {result.stdout.strip()}")
                return True
        except Exception:
            pass
        print("✗ Docker not found. Please install Docker first.")
        return False

    def check_opspectre_available(self):
        """Check if OperationSpectre CLI is available"""
        try:
            result = subprocess.run(['opspectre', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ OperationSpectre: {result.stdout.strip()}")
                return True
        except Exception:
            pass
        print("✗ OperationSpectre CLI not found. Please install it first.")
        return False

    def start_full_stack(self, host='localhost', port=8000, no_wait=False):
        """Start complete OperationSpectre stack with MCP server"""
        print("🚀 Starting OperationSpectre with MCP Integration")
        print("=" * 50)

        # Check requirements
        if not self.check_docker_available():
            return 1
        if not self.check_opspectre_available():
            return 1

        # Change to project directory
        os.chdir(self.project_root)

        try:
            # Start services using docker-compose
            print("🐳 Starting Docker containers...")
            result = subprocess.run([
                'docker-compose', '-f', str(self.docker_compose_file), 'up', '-d'
            ], capture_output=True, text=True)

            if result.returncode != 0:
                print(f"✗ Failed to start containers: {result.stderr}")
                return 1

            print("✓ Docker containers started")

            # Wait for services if requested
            if not no_wait:
                print("⏳ Waiting for services to be ready...")

                # Wait for sandbox
                if not self._wait_for_sandbox():
                    print("✗ Sandbox did not become ready")
                    return 1

                # Wait for MCP server
                if not self._wait_for_mcp_server(host, port):
                    print("⚠️  MCP server may still be starting up...")

            # Show status
            self._show_status(host, port)

            return 0

        except Exception as e:
            print(f"✗ Error starting stack: {e}")
            return 1

    def stop_full_stack(self, force=False):
        """Stop complete OperationSpectre stack"""
        print("🛑 Stopping OperationSpectre with MCP Integration")
        print("=" * 50)

        os.chdir(self.project_root)

        try:
            # Stop services using docker-compose
            print("🐳 Stopping Docker containers...")
            result = subprocess.run([
                'docker-compose', '-f', str(self.docker_compose_file), 'down'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("✓ Docker containers stopped")
            else:
                print(f"⚠️  Containers stop returned: {result.stderr}")

            if force:
                self._force_cleanup()

            print("🎉 All services stopped successfully!")
            return 0

        except Exception as e:
            print(f"✗ Error stopping stack: {e}")
            return 1

    def restart_full_stack(self, host='localhost', port=8000):
        """Restart complete OperationSpectre stack"""
        print("🔄 Restarting OperationSpectre with MCP Integration")
        print("=" * 50)

        os.chdir(self.project_root)

        try:
            # Stop current services
            print("🛑 Stopping current services...")
            subprocess.run([
                'docker-compose', '-f', str(self.docker_compose_file), 'down'
            ], capture_output=True)

            # Start services
            return self.start_full_stack(host, port)

        except Exception as e:
            print(f"✗ Error restarting stack: {e}")
            return 1

    def show_status(self, host='localhost', port=8000):
        """Show current status of all services"""
        print("📊 OperationSpectre Status")
        print("=" * 50)

        # Check Docker containers
        try:
            result = subprocess.run([
                'docker-compose', '-f', str(self.docker_compose_file), 'ps'
            ], capture_output=True, text=True)
            print("\n🐳 Docker Containers:")
            print(result.stdout)
        except Exception as e:
            print(f"✗ Error checking Docker status: {e}")

        # Check MCP server
        try:
            import requests
            response = requests.get(f'http://{host}:{port}/health', timeout=5)
            if response.status_code == 200:
                print(f"\n🔧 MCP Server: RUNNING (http://{host}:{port})")
                # Show available tools
                tools_response = requests.get(f'http://{host}:{port}/tools', timeout=5)
                if tools_response.status_code == 200:
                    tools = tools_response.json()
                    tool_count = len(tools.get('tools', []))
                    print(f"🛠️  Available tools: {tool_count}")
            else:
                print("\n🔧 MCP Server: NOT RUNNING")
        except Exception as e:
            print(f"\n🔧 MCP Server: NOT RUNNING ({e})")

        # Check sandbox
        try:
            result = subprocess.run(['opspectre', 'sandbox', 'status'], capture_output=True, text=True)
            if "running" in result.stdout.lower():
                print("🐚 Sandbox: RUNNING")
            else:
                print("🐚 Sandbox: NOT RUNNING")
        except Exception as e:
            print(f"🐚 Sandbox: NOT RUNNING ({e})")

        return 0

    def logs(self, service='all', follow=False):
        """Show logs from services"""
        os.chdir(self.project_root)

        if follow:
            subprocess.run([
                'docker-compose', '-f', str(self.docker_compose_file), 'logs', '-f', service
            ])
        else:
            result = subprocess.run([
                'docker-compose', '-f', str(self.docker_compose_file), 'logs', service
            ], capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)

    def update_images(self):
        """Update Docker images"""
        print("🔄 Updating Docker images...")

        os.chdir(self.project_root)

        try:
            # Pull latest images
            result = subprocess.run([
                'docker-compose', '-f', str(self.docker_compose_file), 'pull'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("✓ Images updated successfully")
                return 0
            else:
                print(f"✗ Failed to update images: {result.stderr}")
                return 1

        except Exception as e:
            print(f"✗ Error updating images: {e}")
            return 1

    def shell(self, service='opspectre-sandbox'):
        """Get shell in a service container"""
        os.chdir(self.project_root)

        subprocess.run([
            'docker-compose', '-f', str(self.docker_compose_file), 'exec', service, '/bin/bash'
        ])

    def _wait_for_sandbox(self, timeout=60):
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

    def _wait_for_mcp_server(self, host='localhost', port=8000, timeout=60):
        """Wait for MCP server to be ready"""
        print("⏳ Waiting for MCP server to be ready...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                import requests
                response = requests.get(f'http://{host}:{port}/health', timeout=5)
                if response.status_code == 200:
                    print("✓ MCP server is ready!")
                    return True
            except Exception:
                pass

            time.sleep(2)

        print("✗ MCP server did not become ready within timeout")
        return False

    def _show_status(self, host='localhost', port=8000):
        """Show detailed status information"""
        print("\n" + "=" * 60)
        print("🎯 OPERATION SPECTRE STATUS")
        print("=" * 60)

        # MCP Server Info
        try:
            import requests
            response = requests.get(f'http://{host}:{port}/tools', timeout=5)
            if response.status_code == 200:
                tools = response.json()
                tool_count = len(tools.get('tools', []))
                print("🔧 MCP Server: RUNNING")
                print(f"   URL: http://{host}:{port}")
                print(f"   Tools: {tool_count} available")
                print(f"   Health: http://{host}:{port}/health")
        except Exception:
            print("🔧 MCP Server: NOT RUNNING")

        # Docker Info
        try:
            result = subprocess.run(['docker-compose', '-f', str(self.docker_compose_file), 'ps'], capture_output=True, text=True)
            print("\n🐳 Docker Containers:")
            print(result.stdout)
        except Exception:
            print("🐳 Docker Containers: Error checking status")

        print("\n🚀 Quick Commands:")
        print("  - Test MCP: curl http://localhost:8000/tools")
        print("  - Python: from pi_pentest_recon_mcp import run_reconnaissance")
        print("  - Pipeline: python3 scripts/pipeline_runner.py scripts/pipelines/mcp-recon.yaml --target example.com")

    def _force_cleanup(self):
        """Force cleanup of any remaining processes"""
        print("🧹 Performing force cleanup...")

        # Kill any remaining MCP processes
        subprocess.run(['pkill', '-f', 'mcp_server.py'], capture_output=True)

        # Kill any remaining OperationSpectre processes
        subprocess.run(['pkill', '-f', 'opspectre'], capture_output=True)

        # Force stop docker containers
        subprocess.run('docker stop $(docker ps -q --filter "name=opspectre")', capture_output=True, shell=True)

        print("✓ Force cleanup completed")


def main():
    """Main function"""
    manager = OperationSpectreManager()

    parser = argparse.ArgumentParser(description='Manage OperationSpectre with MCP Integration')
    parser.add_argument('--host', default='localhost', help='MCP server host')
    parser.add_argument('--port', type=int, default=8000, help='MCP server port')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start complete stack')
    start_parser.add_argument('--no-wait', action='store_true', help='Don\'t wait for services')

    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop complete stack')
    stop_parser.add_argument('--force', action='store_true', help='Force cleanup')

    # Restart command
    _restart_parser = subparsers.add_parser('restart', help='Restart complete stack')

    # Status command
    _status_parser = subparsers.add_parser('status', help='Show status')

    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show logs')
    logs_parser.add_argument('--service', default='all', help='Service to show logs for')
    logs_parser.add_argument('--follow', action='store_true', help='Follow logs')

    # Update command
    _update_parser = subparsers.add_parser('update', help='Update Docker images')

    # Shell command
    shell_parser = subparsers.add_parser('shell', help='Get shell in container')
    shell_parser.add_argument('--service', default='opspectre-sandbox', help='Service to connect to')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == 'start':
            return manager.start_full_stack(args.host, args.port, args.no_wait)
        elif args.command == 'stop':
            return manager.stop_full_stack(args.force)
        elif args.command == 'restart':
            return manager.restart_full_stack(args.host, args.port)
        elif args.command == 'status':
            return manager.show_status(args.host, args.port)
        elif args.command == 'logs':
            return manager.logs(args.service, args.follow)
        elif args.command == 'update':
            return manager.update_images()
        elif args.command == 'shell':
            return manager.shell(args.service)
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\n⛔ Operation cancelled by user")
        return 1


if __name__ == "__main__":
    sys.exit(main())
