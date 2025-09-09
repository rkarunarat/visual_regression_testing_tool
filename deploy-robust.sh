#!/bin/bash

# Visual Regression Testing Tool - Robust Deployment Script
# Usage: ./deploy-robust.sh [production|staging]

set -e

ENVIRONMENT=${1:-production}
APP_NAME="visual-regression-testing"
DOCKER_IMAGE="$APP_NAME:latest"

echo "🚀 Deploying Visual Regression Testing Tool - Robust Build - Environment: $ENVIRONMENT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if Docker is installed and running
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
print_status "Creating directories..."
mkdir -p test_results logs ssl

# Set permissions
chmod 755 test_results logs

# Build the Docker image with robust approach
print_status "Building robust Docker image (this may take a few minutes)..."
print_info "Using Dockerfile.robust to avoid network issues with package dependencies"

# Try building with multiple approaches to handle network issues
print_status "Attempting robust build with network issue handling..."

# Approach 1: Try robust Dockerfile
if docker build -f Dockerfile.robust -t $DOCKER_IMAGE .; then
    print_status "✅ Robust Docker image built successfully!"
elif docker build -f Dockerfile -t $DOCKER_IMAGE .; then
    print_status "✅ Standard Docker image built successfully!"
else
    print_error "❌ All Docker build approaches failed."
    print_info "This might be due to network connectivity issues."
    print_info ""
    print_info "Try these solutions:"
    print_info "1. Check your internet connection"
    print_info "2. Restart Docker"
    print_info "3. Use local Python deployment: ./deploy-local.sh"
    print_info "4. Try again later when network is more stable"
    exit 1
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down || true

# Start the application
print_status "Starting application..."
if [ "$ENVIRONMENT" = "production" ]; then
    # Production: with nginx reverse proxy
    export EXTERNAL_PORT=80
    docker-compose --profile production up -d
    print_status "Application started with nginx reverse proxy"
    print_status "Access your app at: http://your-server-ip or http://your-domain.com"
    print_status "Nginx is handling SSL termination and load balancing"
else
    # Local: direct access on port 80
    export EXTERNAL_PORT=80
    docker-compose up -d
    print_status "Application started in local mode"
    print_status "Access your app at: http://localhost (port 80)"
fi

# Wait for application to be ready
print_status "Waiting for application to be ready..."
sleep 15

# Health check
print_status "Performing health check..."
if [ "$ENVIRONMENT" = "production" ]; then
    # Check nginx health
    if curl -f http://localhost/health > /dev/null 2>&1; then
        print_status "✅ Application is healthy and ready!"
    else
        print_warning "⚠️ Health check failed. Application may still be starting up."
        print_status "Check logs with: docker-compose logs -f"
    fi
else
    # Check direct Streamlit health
    if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        print_status "✅ Application is healthy and ready!"
    else
        print_warning "⚠️ Health check failed. Application may still be starting up."
        print_status "Check logs with: docker-compose logs -f"
    fi
fi

# Show running containers
print_status "Running containers:"
docker-compose ps

# Show logs
print_status "Recent logs:"
docker-compose logs --tail=20

echo ""
if [ "$ENVIRONMENT" = "production" ]; then
    print_status "🎉 Robust Production Deployment completed!"
    print_status "Your app is now running with nginx reverse proxy"
    print_status "Configure your domain DNS to point to this server"
else
    print_status "🎉 Robust Local Deployment completed!"
    print_status "Your app is now running on http://localhost"
fi

echo ""
print_status "Features:"
echo "  🐳 Docker-based: All dependencies handled in container"
echo "  🎭 Playwright: Full browser automation support"
echo "  📊 Visual Testing: Screenshot comparison across browsers"
echo "  🔄 Production Ready: Health checks, restart policies"
echo "  🛡️ Robust Build: Handles network issues gracefully"
echo ""
print_status "Useful commands:"
echo "  View logs:     docker-compose logs -f"
echo "  Stop app:      docker-compose down"
echo "  Restart app:   docker-compose restart"
echo "  Update app:    ./deploy-robust.sh $ENVIRONMENT"
echo "  Local Python:  ./deploy-local.sh"
