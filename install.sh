#!/bin/bash

# Visual Regression Testing Tool - Server Installation Script
# For Ubuntu/Debian servers

set -e

APP_NAME="visual-regression-testing"
APP_DIR="/opt/$APP_NAME"
SERVICE_USER="streamlit"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run as root (use sudo)"
    exit 1
fi

print_status "Installing Visual Regression Testing Tool..."

# Update system packages
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install required system packages
print_status "Installing system dependencies..."
apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    curl \
    wget \
    git \
    nginx \
    supervisor \
    ca-certificates \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libxkbcommon0 \
    libx11-xcb1 \
    libxshmfence1 \
    libdrm2 \
    libdbus-1-3 \
    libatspi2.0-0 \
    libcups2

# Create service user
print_status "Creating service user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd -r -s /bin/false -d "$APP_DIR" "$SERVICE_USER"
fi

# Create application directory
print_status "Creating application directory..."
mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Clone or copy application files
print_status "Setting up application files..."
if [ -d ".git" ]; then
    print_status "Updating from git repository..."
    git pull
else
    print_warning "Please copy your application files to $APP_DIR"
    print_warning "Or clone your repository: git clone <your-repo-url> ."
fi

# Create Python virtual environment
print_status "Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
print_status "Installing Playwright browsers..."
playwright install chromium firefox webkit

# Create necessary directories
print_status "Creating directories..."
mkdir -p test_results logs
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR"

# Install systemd service
print_status "Installing systemd service..."
cp systemd/visual-regression-testing.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable visual-regression-testing

# Configure nginx
print_status "Configuring nginx..."
cp nginx.conf /etc/nginx/sites-available/visual-regression-testing
ln -sf /etc/nginx/sites-available/visual-regression-testing /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
nginx -t

# Start services
print_status "Starting services..."
systemctl start visual-regression-testing
systemctl restart nginx

# Check service status
print_status "Checking service status..."
sleep 5
if systemctl is-active --quiet visual-regression-testing; then
    print_status "✅ Visual Regression Testing Tool is running!"
else
    print_error "❌ Service failed to start. Check logs: journalctl -u visual-regression-testing -f"
    exit 1
fi

# Show status
print_status "Service status:"
systemctl status visual-regression-testing --no-pager

echo ""
print_status "🎉 Installation completed!"
echo ""
print_status "Your Visual Regression Testing Tool is now running at:"
echo "  http://your-server-ip"
echo ""
print_status "Useful commands:"
echo "  Check status:    systemctl status visual-regression-testing"
echo "  View logs:       journalctl -u visual-regression-testing -f"
echo "  Restart service: systemctl restart visual-regression-testing"
echo "  Stop service:    systemctl stop visual-regression-testing"
echo ""
print_warning "Don't forget to:"
echo "  1. Configure your domain in /etc/nginx/sites-available/visual-regression-testing"
echo "  2. Set up SSL certificates for HTTPS"
echo "  3. Configure firewall rules if needed"
