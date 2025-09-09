#!/bin/bash

# Visual Regression Testing Tool - Local Deployment Script
# Usage: ./deploy-local.sh
# This script sets up a local Python environment without Docker

set -e

echo "🚀 Setting up Visual Regression Testing Tool - Local Environment"

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

# Check if Python is installed
print_status "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11+ first."
    print_info "Visit: https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
print_status "Python version: $PYTHON_VERSION"

if ! python3 -c 'import sys; exit(0 if sys.version_info >= (3, 11) else 1)'; then
    print_warning "Python 3.11+ is recommended. Current version: $PYTHON_VERSION"
    print_info "Some features may not work correctly with older versions."
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip first."
    exit 1
fi

# Create virtual environment
print_status "Creating virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

python3 -m venv venv
print_status "Virtual environment created successfully!"

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install requirements
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
print_status "Installing Playwright browsers..."
playwright install

# Install Playwright system dependencies
print_status "Installing Playwright system dependencies..."
if command -v apt-get &> /dev/null; then
    # Linux (Ubuntu/Debian)
    print_info "Detected Linux system. Installing system dependencies..."
    playwright install-deps
elif command -v brew &> /dev/null; then
    # macOS
    print_info "Detected macOS system. Installing system dependencies..."
    playwright install-deps
elif command -v dnf &> /dev/null; then
    # Fedora
    print_info "Detected Fedora system. Installing system dependencies..."
    playwright install-deps
else
    print_warning "Could not detect package manager. You may need to install system dependencies manually."
    print_info "Visit: https://playwright.dev/python/docs/installation"
fi

# Run tests
print_status "Running functionality tests..."
python test_functionality.py

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p test_results
mkdir -p logs

# Set up environment variables
print_status "Setting up environment..."
if [ ! -f ".env" ]; then
    if [ -f "env.example" ]; then
        cp env.example .env
        print_status "Created .env file from template"
    else
        echo "STREAMLIT_SERVER_PORT=8501" > .env
        echo "STREAMLIT_SERVER_ADDRESS=0.0.0.0" >> .env
        echo "STREAMLIT_SERVER_HEADLESS=true" >> .env
        print_status "Created basic .env file"
    fi
fi

# Start the application
print_status "Starting Visual Regression Testing Tool..."
print_status "The application will be available at: http://localhost:8501"
print_status "Press Ctrl+C to stop the application"
print_status ""

# Load environment variables and start Streamlit
source .env
streamlit run app.py --server.port=${STREAMLIT_SERVER_PORT:-8501} --server.address=${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}
