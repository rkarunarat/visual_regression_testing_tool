#!/bin/bash

# Visual Regression Testing Tool - Deployment Script
# Usage: ./deploy.sh [production|staging|local]

set -e

ENVIRONMENT=${1:-local}
APP_NAME="visual-regression-testing"
DOCKER_IMAGE="$APP_NAME:latest"

echo "🚀 Deploying Visual Regression Testing Tool - Environment: $ENVIRONMENT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
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

# Build the Docker image
print_status "Building Docker image..."
docker build -t $DOCKER_IMAGE .

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down || true

# Start the application
print_status "Starting application..."
if [ "$ENVIRONMENT" = "production" ]; then
    # Production: with nginx reverse proxy
    docker-compose --profile with-nginx up -d
    print_status "Application started with nginx reverse proxy"
    print_status "Access your app at: http://your-domain.com"
else
    # Local/Staging: direct access
    docker-compose up -d
    print_status "Application started"
    print_status "Access your app at: http://localhost:8501"
fi

# Wait for application to be ready
print_status "Waiting for application to be ready..."
sleep 10

# Health check
print_status "Performing health check..."
if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
    print_status "✅ Application is healthy and ready!"
else
    print_warning "⚠️ Health check failed. Application may still be starting up."
    print_status "Check logs with: docker-compose logs -f"
fi

# Show running containers
print_status "Running containers:"
docker-compose ps

# Show logs
print_status "Recent logs:"
docker-compose logs --tail=20

echo ""
print_status "🎉 Deployment completed!"
echo ""
print_status "Useful commands:"
echo "  View logs:     docker-compose logs -f"
echo "  Stop app:      docker-compose down"
echo "  Restart app:   docker-compose restart"
echo "  Update app:    ./deploy.sh $ENVIRONMENT"
echo ""
print_status "Application URL:"
if [ "$ENVIRONMENT" = "production" ]; then
    echo "  http://your-domain.com"
else
    echo "  http://localhost:8501"
fi
