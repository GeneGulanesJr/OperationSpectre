#!/bin/bash
# =========================================================================
# build.sh — Build OperationSpectre Docker images with persistent caching
#
# Usage:
#   ./scripts/build.sh              # Full build (base + app) with cache
#   ./scripts/build.sh app          # Only rebuild app layer (fast!)
#   ./scripts/build.sh base         # Only rebuild base layer
#   ./scripts/build.sh --no-cache   # Full clean build
#   ./scripts/build.sh --push       # Build and push base to registry
#   ./scripts/build.sh --help       # Show usage
# =========================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONTAINERS_DIR="$PROJECT_DIR/containers"
CACHE_DIR="$PROJECT_DIR/.docker-cache"

# Defaults
BUILD_BASE=true
BUILD_APP=true
NO_CACHE=""
PUSH=false
REGISTRY="${OPSPECTRE_REGISTRY:-}"
BASE_TAG="opspectre-base:latest"
APP_TAG="opspectre-full:latest"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

usage() {
    cat <<EOF
${CYAN}OperationSpectre Docker Build${NC}

Usage: $0 [command] [options]

Commands:
  (none)        Full build (base + app)
  base          Only build the base image
  app           Only build the app layer (fast, uses cached base)

Options:
  --no-cache    Disable all caching
  --push        Push base image to registry after build
  --help        Show this help

Environment:
  OPSPECTRE_REGISTRY   Docker registry for base image (e.g. ghcr.io/org/opspectre-base)

Cache:
  BuildKit layer cache is stored in: ${CACHE_DIR}
  Delete it to force a full rebuild: rm -rf ${CACHE_DIR}

Examples:
  $0                    # Full build with cache
  $0 app                # Rebuild only app layer (~2-5 min)
  $0 base               # Rebuild only base layer
  $0 app --no-cache     # Clean rebuild of app layer
EOF
    exit 0
}

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        --no-cache) NO_CACHE="--no-cache" ;;
        --push) PUSH=true ;;
        --help|-h) usage ;;
        base) BUILD_APP=false ;;
        app) BUILD_BASE=false ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            usage
            ;;
    esac
done

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check BuildKit
if ! docker buildx version > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: docker buildx not found. Using plain docker build (slower).${NC}"
    USE_BUILDX=false
else
    USE_BUILDX=true
fi

mkdir -p "$CACHE_DIR"

# Registry tag for base image
if [ -n "$REGISTRY" ]; then
    BASE_REGISTRY_TAG="$REGISTRY"
fi

# =========================================================================
# Build Base Image
# =========================================================================
build_base() {
    echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Building base image: ${BASE_TAG}${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════${NC}"

    if [ "$USE_BUILDX" = true ]; then
        CACHE_FROM_FLAG="--cache-from=type=local,src=${CACHE_DIR}/base"
        CACHE_TO_FLAG="--cache-to=type=local,dest=${CACHE_DIR}/base,mode=max"

        docker buildx build \
            -f "$CONTAINERS_DIR/Dockerfile.base" \
            -t "$BASE_TAG" \
            --load \
            $CACHE_FROM_FLAG \
            $CACHE_TO_FLAG \
            $NO_CACHE \
            "$PROJECT_DIR"
    else
        docker build \
            -f "$CONTAINERS_DIR/Dockerfile.base" \
            -t "$BASE_TAG" \
            $NO_CACHE \
            "$PROJECT_DIR"
    fi

    echo -e "${GREEN}✓ Base image built: ${BASE_TAG}${NC}"

    # Push if requested
    if [ "$PUSH" = true ] && [ -n "$REGISTRY" ]; then
        echo -e "${YELLOW}Tagging and pushing to ${REGISTRY}...${NC}"
        docker tag "$BASE_TAG" "$REGISTRY"
        docker push "$REGISTRY"
        echo -e "${GREEN}✓ Pushed: ${REGISTRY}${NC}"
    fi
}

# =========================================================================
# Build App Image
# =========================================================================
build_app() {
    # Check if base exists locally
    if ! docker image inspect "$BASE_TAG" > /dev/null 2>&1; then
        echo -e "${YELLOW}Base image ${BASE_TAG} not found locally."
        if [ -n "$REGISTRY" ]; then
            echo -e "Pulling from ${REGISTRY}...${NC}"
            docker pull "$REGISTRY" && docker tag "$REGISTRY" "$BASE_TAG"
        else
            echo -e "${YELLOW}Building base image first...${NC}"
            build_base
        fi
    fi

    echo -e "${CYAN}═══════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Building app layer: ${APP_TAG}${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════${NC}"

    if [ "$USE_BUILDX" = true ]; then
        CACHE_FROM_FLAG="--cache-from=type=local,src=${CACHE_DIR}/app"
        CACHE_TO_FLAG="--cache-to=type=local,dest=${CACHE_DIR}/app,mode=max"

        docker buildx build \
            -f "$CONTAINERS_DIR/Dockerfile" \
            -t "$APP_TAG" \
            --load \
            $CACHE_FROM_FLAG \
            $CACHE_TO_FLAG \
            $NO_CACHE \
            "$PROJECT_DIR"
    else
        docker build \
            -f "$CONTAINERS_DIR/Dockerfile" \
            -t "$APP_TAG" \
            $NO_CACHE \
            "$PROJECT_DIR"
    fi

    echo -e "${GREEN}✓ App image built: ${APP_TAG}${NC}"
}

# =========================================================================
# Main
# =========================================================================
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     OPERATIONSPECTRE Docker Build        ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

START_TIME=$(date +%s)

if [ "$BUILD_BASE" = true ]; then
    build_base
    echo ""
fi

if [ "$BUILD_APP" = true ]; then
    build_app
    echo ""
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Build complete in ${MINUTES}m ${SECONDS}s${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo ""
echo "Images:"
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | grep -E "opspectre|REPOSITORY" || true
echo ""
echo "Next steps:"
echo "  docker compose -f containers/docker-compose.yml up -d"
echo "  OR"
echo "  ./scripts/start-opspectre.sh"
