#!/bin/bash
# Start OPERATIONSPECTRE Full Arsenal container
# Usage: ./scripts/start-opspectre.sh [command]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONTAINER_DIR="$PROJECT_DIR/containers"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== OPERATIONSPECTRE Full Arsenal ===${NC}"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Create output directory
# On WSL, mirror output to the Windows Desktop for easy access.
# On Linux/macOS, the volume mount at ./output/ is sufficient.
if grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
    DESKTOP_DIR="/mnt/c/Users/GeneGulanesJr/Desktop/OperationSpectre-Results"
    mkdir -p "$DESKTOP_DIR"
else
    DESKTOP_DIR="$PROJECT_DIR/output"
    mkdir -p "$DESKTOP_DIR"
fi

# Generate token if not set
if [ -z "$TOOL_SERVER_TOKEN" ]; then
    export TOOL_SERVER_TOKEN=$(openssl rand -hex 32)
    echo -e "${YELLOW}Generated TOOL_SERVER_TOKEN: ${TOOL_SERVER_TOKEN}${NC}"
fi

# Check if container is already running
if docker ps -q -f name=opspectre-full | grep -q .; then
    echo -e "${YELLOW}Container already running. Attaching...${NC}"
    docker exec -it opspectre-full bash
    exit 0
fi

# Build if needed
if ! docker image inspect opspectre-full:latest > /dev/null 2>&1; then
    echo -e "${YELLOW}Building container (using cached build)...${NC}"
    "$SCRIPT_DIR/build.sh"
fi

# Start container
echo -e "${GREEN}Starting container...${NC}"
cd "$CONTAINER_DIR"
docker-compose up -d

# Wait for tool server
echo -e "${YELLOW}Waiting for tool server...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:48081/health | grep -q '"status":"healthy"'; then
        echo -e "${GREEN}Tool server ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Tool server failed to start${NC}"
        docker logs opspectre-full
        exit 1
    fi
    sleep 1
done

# Run command if provided
if [ $# -eq 0 ]; then
    echo -e "${GREEN}Container running. Access via:${NC}"
    echo -e "  - Tool Server: http://localhost:48081"
    echo -e "  - VNC: localhost:5900 (password: opspectre)"
    echo -e "  - noVNC: http://localhost:6080/vnc.html"
    echo ""
    echo -e "${YELLOW}To attach:${NC} docker exec -it opspectre-full bash"
    echo -e "${YELLOW}To stop:${NC} cd containers && docker-compose down"
    echo ""
    echo -e "${GREEN}Output directory: $DESKTOP_DIR${NC}"
else
    # Run command in container
    docker exec -it opspectre-full "$@"
fi