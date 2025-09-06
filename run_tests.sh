#!/bin/bash

# Visual Regression Testing Tool - Test Runner
# Runs the functionality test suite before deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️ $1${NC}"
}

print_header "VISUAL REGRESSION TESTING TOOL - TEST RUNNER"

# Check if Python is available
if ! command -v python &> /dev/null; then
    print_error "Python is not installed or not in PATH"
    exit 1
fi

# Check if test file exists
if [ ! -f "test_functionality.py" ]; then
    print_error "test_functionality.py not found"
    exit 1
fi

print_info "Running functionality tests..."

# Run the test suite
python test_functionality.py

# Capture exit code
TEST_EXIT_CODE=$?

if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_header "TESTS PASSED"
    print_success "All tests passed! Ready for deployment."
    echo ""
    print_info "You can now:"
    echo "  1. Deploy locally: ./deploy.sh local"
    echo "  2. Deploy to server: ./deploy.sh production"
    echo "  3. Push to repository: git add . && git commit -m 'message' && git push"
else
    print_header "TESTS FAILED"
    print_error "Some tests failed. Please fix issues before deploying."
    exit 1
fi
