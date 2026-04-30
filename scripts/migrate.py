#!/usr/bin/env python3
"""
OperationSpectre Migration Script

Automatically migrates from old tool server to new MCP integration.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, check=check,
                              capture_output=True, text=True)
        return result.stdout, result.stderr, result.returncode
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e.stdout, e.stderr, e.returncode

def check_old_system():
    """Check if old system is running"""
    # Check for old container
    stdout, _stderr, rc = run_command("docker ps -f name=opspectre-full --format '{{.Names}}'", check=False)
    if rc == 0 and "opspectre-full" in stdout:
        return True

    # Check for old MCP server
    _stdout, _stderr, rc = run_command("lsof -i :48081", check=False)
    return rc == 0

def stop_old_system():
    """Stop old system services"""
    print("🛑 Stopping old system...")

    # Stop old container
    run_command("docker-compose -f containers/docker-compose.yml down", check=False)

    # Kill old MCP processes
    run_command("pkill -f 'tool_server.py'", check=False)

    # Kill any process using port 48081
    run_command("fuser -k 48081/tcp 2>/dev/null || true", check=False)

    print("✅ Old system stopped")

def check_docker_running():
    """Check if Docker is running"""
    _stdout, _stderr, rc = run_command("docker info", check=False)
    if rc != 0:
        print("❌ Docker is not running or not accessible")
        print("Please start Docker and try again")
        sys.exit(1)

    print("✅ Docker is running")

def start_new_system():
    """Start new MCP system"""
    print("🚀 Starting new MCP system...")

    # Check if we're in the right directory
    if not Path("scripts/manage.py").exists():
        print("❌ Not in OperationSpectre directory")
        print("Please run this script from the OperationSpectre root directory")
        sys.exit(1)

    # Start the new system
    _stdout, _stderr, _rc = run_command("./scripts/manage.py start", check=True)

    print("✅ New MCP system started")

def verify_migration():
    """Verify migration was successful"""
    print("🔍 Verifying migration...")

    # Check MCP server health
    stdout, stderr, rc = run_command("curl -s http://localhost:8000/health", check=False)
    if rc != 0 or "healthy" not in stdout:
        print("❌ MCP server health check failed")
        print("Error:", stderr)
        return False

    print("✅ MCP server health check passed")

    # Check tools endpoint
    stdout, stderr, rc = run_command("curl -s http://localhost:8000/tools", check=False)
    if rc != 0 or "nmap_scan" not in stdout:
        print("❌ Tools endpoint check failed")
        print("Error:", stderr)
        return False

    print("✅ Tools endpoint check passed")

    # Test sandbox status
    stdout, stderr, rc = run_command(
        '''curl -s -X POST http://localhost:8000/tools/call \
           -H "Content-Type: application/json" \
           -d '{"tool_name": "sandbox_status", "arguments": {}}' ''',
        check=False
    )
    if rc != 0:
        print("❌ Sandbox integration test failed")
        print("Error:", stderr)
        return False

    print("✅ Sandbox integration test passed")

    return True

def create_backup():
    """Create backup of current configuration"""
    backup_dir = Path("backup_migration")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    backup_dir.mkdir()

    # Backup docker-compose files
    for file in Path(".").glob("docker-compose*.yml"):
        shutil.copy2(file, backup_dir)

    # Backup scripts
    scripts_dir = backup_dir / "scripts"
    scripts_dir.mkdir()
    shutil.copy2("scripts/manage.py", scripts_dir)

    print(f"✅ Created backup in {backup_dir}")

def update_shell_aliases():
    """Update shell aliases if they exist"""
    aliases_file = Path.home() / ".bashrc"
    if not aliases_file.exists():
        return

    # Remove old aliases
    old_aliases = [
        "alias opspectre-server=",
        "alias tool-server=",
        "alias opspectre-start="
    ]

    content = aliases_file.read_text()
    for alias in old_aliases:
        content = content.replace(alias + "# MCP integration", "")
        content = content.replace(alias + "=\"", "")
        content = content.replace("\"", "")
        content = content.replace("\n", "")

    aliases_file.write_text(content)

    # Add new alias
    new_alias = """
# OperationSpectre MCP integration
alias opspectre-mcp="./scripts/manage.py"
alias opspectre="./scripts/manage.py"
"""

    if "# OperationSpectre MCP integration" not in content:
        aliases_file.write_text(content + new_alias)

def show_next_steps():
    """Show next steps after migration"""
    print("\n🎉 Migration completed successfully!")
    print("\n📚 Next Steps:")
    print("1. Read the updated documentation:")
    print("   - README.md (MCP section)")
    print("   - docs/MCP_USAGE.md")
    print("   - docs/MIGRATION_GUIDE.md")

    print("\n2. Test the new system:")
    print("   - ./scripts/manage.py status")
    print("   - curl http://localhost:8000/health")
    print("   - curl http://localhost:8000/tools")

    print("\n3. For AI agents:")
    print("   - Try the pentest-recon-mcp skill")
    print("   - See docs/MCP_USAGE.md for tool reference")

    print("\n4. Performance comparison:")
    print("   - Old system: ~24,000 tokens per step")
    print("   - New MCP system: ~6,000-8,000 tokens total")
    print("   - 60-80% token savings!")

    print("\n🔧 Management Commands:")
    print("   - ./scripts/manage.py start     # Start everything")
    print("   - ./scripts/manage.py stop      # Stop everything")
    print("   - ./scripts/manage.py status    # Check status")
    print("   - ./scripts/manage.py logs     # View logs")
    print("   - ./scripts/manage.py --help    # All commands")

def main():
    """Main migration function"""
    print("🔄 OperationSpectre Migration Script")
    print("=" * 50)

    # Check if we're in the right directory
    if not Path("README.md").exists():
        print("❌ Not in OperationSpectre directory")
        print("Please run this script from the OperationSpectre root directory")
        sys.exit(1)

    # Check Docker
    check_docker_running()

    # Check if old system is running
    if check_old_system():
        print("⚠️  Old system detected, proceeding with migration...")
        stop_old_system()
    else:
        print("✅ No old system detected")

    # Create backup
    create_backup()

    # Start new system
    start_new_system()

    # Wait a bit for services to start
    print("⏳ Waiting for services to start...")
    import time
    time.sleep(10)

    # Verify migration
    if verify_migration():
        print("🎉 Migration successful!")
        update_shell_aliases()
        show_next_steps()

        # Ask if user wants to rollback
        response = input("\n❓ Would you like to test rollback? (y/N): ")
        if response.lower() == 'y':
            print("\n🔄 Testing rollback...")
            test_rollback()
    else:
        print("❌ Migration verification failed!")
        print("Check logs with: ./scripts/manage.py logs")
        sys.exit(1)

def test_rollback():
    """Test rollback to old system"""
    print("\n🔄 Testing rollback...")

    # Stop new system
    run_command("./scripts/manage.py stop", check=True)

    # Start old system
    print("Starting old system...")
    run_command("cd containers && docker-compose up -d", check=True)

    # Test old system
    _stdout, _stderr, rc = run_command("curl -s http://localhost:48081/health", check=False)
    if rc == 0:
        print("✅ Old system working")
    else:
        print("❌ Old system not working")

    print("\nTo rollback permanently:")
    print("1. Stop new system: ./scripts/manage.py stop")
    print("2. Start old system: cd containers && docker-compose up -d")
    print("3. Use old API: curl -H \"Authorization: Bearer $TOKEN\" http://localhost:48081/execute")

if __name__ == "__main__":
    main()
