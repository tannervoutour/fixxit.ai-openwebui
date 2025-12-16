#!/bin/bash

# ==============================================================================
# Fixxit.ai OpenWebUI - Docker Build Script
# ==============================================================================
# This script builds the production Docker image for deployment
#
# Usage:
#   ./build-docker.sh              # Build with auto-generated tag
#   ./build-docker.sh v1.0.0       # Build with specific version tag
#   ./build-docker.sh latest       # Build and tag as latest
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(dirname "$(readlink -f "$0")")"
IMAGE_NAME="fixxit-openwebui"
REGISTRY="${DOCKER_REGISTRY:-}"  # Optional: set DOCKER_REGISTRY env var for pushing

# ==============================================================================
# Helper Functions
# ==============================================================================

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ✗${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
}

# ==============================================================================
# Pre-build Checks
# ==============================================================================

check_docker() {
    if ! command -v docker >/dev/null 2>&1; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    log_success "Docker found: $(docker --version)"
}

check_git() {
    if ! command -v git >/dev/null 2>&1; then
        log_warning "Git not found. Build hash will be 'unknown'"
        return 1
    fi
    return 0
}

# ==============================================================================
# Build Process
# ==============================================================================

# Determine version tag
VERSION=${1:-$(date +%Y%m%d-%H%M%S)}
BUILD_HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
FULL_TAG="${IMAGE_NAME}:${VERSION}"

log "======================================================================"
log "Fixxit.ai OpenWebUI - Docker Build"
log "======================================================================"
log "Image Name:     ${IMAGE_NAME}"
log "Version Tag:    ${VERSION}"
log "Git Hash:       ${BUILD_HASH}"
log "Full Tag:       ${FULL_TAG}"
if [ -n "$REGISTRY" ]; then
    log "Registry:       ${REGISTRY}"
fi
log "======================================================================"

# Run checks
check_docker
check_git

# Confirm build
echo ""
read -p "Proceed with build? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    log "Build cancelled"
    exit 0
fi

echo ""
log "Starting Docker build..."

cd "$PROJECT_ROOT"

# Build the image
log "Building Docker image: ${FULL_TAG}"
docker build \
    --build-arg BUILD_HASH="${BUILD_HASH}" \
    --tag "${FULL_TAG}" \
    --tag "${IMAGE_NAME}:latest" \
    --file Dockerfile \
    . || {
        log_error "Docker build failed"
        exit 1
    }

log_success "Docker build completed successfully!"

# Show image info
echo ""
log "Image information:"
docker images | grep "${IMAGE_NAME}" | head -2

# Show image size
IMAGE_SIZE=$(docker images "${FULL_TAG}" --format "{{.Size}}")
log "Image size: ${IMAGE_SIZE}"

# Tag for registry if configured
if [ -n "$REGISTRY" ]; then
    echo ""
    log "Tagging for registry: ${REGISTRY}"
    docker tag "${FULL_TAG}" "${REGISTRY}/${FULL_TAG}"
    docker tag "${IMAGE_NAME}:latest" "${REGISTRY}/${IMAGE_NAME}:latest"
    log_success "Tagged for registry"

    echo ""
    read -p "Push to registry now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Pushing to registry..."
        docker push "${REGISTRY}/${FULL_TAG}"
        docker push "${REGISTRY}/${IMAGE_NAME}:latest"
        log_success "Pushed to registry successfully"
    fi
fi

echo ""
log "======================================================================"
log_success "Build complete! Image ready for deployment"
log "======================================================================"
log "Image tags created:"
log "  - ${FULL_TAG}"
log "  - ${IMAGE_NAME}:latest"
if [ -n "$REGISTRY" ]; then
    log "  - ${REGISTRY}/${FULL_TAG}"
    log "  - ${REGISTRY}/${IMAGE_NAME}:latest"
fi
echo ""
log "Next steps:"
log "  1. Test locally: docker-compose -f docker-compose.prod.yml up"
log "  2. Deploy to server: ./deploy-docker.sh ${VERSION}"
log "  3. Or save image: docker save ${FULL_TAG} | gzip > fixxit-openwebui-${VERSION}.tar.gz"
log "======================================================================"
