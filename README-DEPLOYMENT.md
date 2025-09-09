# Deployment Guide

This guide provides comprehensive deployment options for the Visual Regression Testing Tool.

## 🚀 Quick Start (Docker - Recommended)

### Prerequisites
- Docker and Docker Compose installed
- 2GB+ RAM available
- Port 8501 (or 80/443) accessible

### 1. Clone and Deploy
```bash
# Clone your repository
git clone <your-repo-url>
cd visual_regression_testing_tool

# Make deployment script executable
chmod +x deploy.sh

# Deploy locally
./deploy.sh local

# Or deploy with nginx reverse proxy
./deploy.sh production
```

### 2. Access Your App
- **Local**: http://localhost:8501
- **With Nginx**: http://your-domain.com

## 🐳 Docker Deployment Options

### Option 1: Simple Docker Run
```bash
# Build the image
docker build -t visual-regression-testing .

# Run the container
docker run -d \
  --name visual-regression-testing \
  -p 8501:8501 \
  -v $(pwd)/test_results:/app/test_results \
  --restart unless-stopped \
  visual-regression-testing
```

### Option 2: Docker Compose (Recommended)
```bash
# Start with basic setup
docker-compose up -d

# Start with nginx reverse proxy
docker-compose --profile with-nginx up -d
```

### Option 3: Production with SSL
```bash
# 1. Set up SSL certificates
mkdir ssl
# Copy your cert.pem and key.pem to ssl/ directory

# 2. Update nginx.conf with your domain
# Edit nginx.conf and uncomment HTTPS section

# 3. Deploy with nginx
./deploy.sh production
```

## 🖥️ Native Server Installation

### Prerequisites
- Ubuntu 20.04+ or Debian 11+
- Root access
- 2GB+ RAM
- Python 3.11+

### Automated Installation
```bash
# Download and run installation script
curl -fsSL https://raw.githubusercontent.com/your-repo/install.sh | sudo bash

# Or run locally
sudo ./install.sh
```

### Manual Installation
```bash
# 1. Install system dependencies
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip nginx

# 2. Create application directory
sudo mkdir -p /opt/visual-regression-testing
cd /opt/visual-regression-testing

# 3. Copy your application files
sudo cp -r /path/to/your/app/* .

# 4. Create virtual environment
sudo python3.11 -m venv venv
sudo venv/bin/pip install -r requirements.txt
sudo venv/bin/playwright install chromium

# 5. Set up systemd service
sudo cp systemd/visual-regression-testing.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable visual-regression-testing
sudo systemctl start visual-regression-testing

# 6. Configure nginx
sudo cp nginx.conf /etc/nginx/sites-available/visual-regression-testing
sudo ln -s /etc/nginx/sites-available/visual-regression-testing /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## ☁️ Cloud Provider Deployment

### AWS EC2
```bash
# 1. Launch Ubuntu 20.04+ instance
# 2. Configure security group (ports 22, 80, 443, 8501)
# 3. SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# 4. Run installation
curl -fsSL https://raw.githubusercontent.com/your-repo/install.sh | sudo bash
```

### DigitalOcean Droplet
```bash
# 1. Create Ubuntu droplet
# 2. SSH into droplet
ssh root@your-droplet-ip

# 3. Run installation
curl -fsSL https://raw.githubusercontent.com/your-repo/install.sh | bash
```

### Google Cloud Platform
```bash
# 1. Create VM instance
# 2. SSH into instance
gcloud compute ssh your-instance-name

# 3. Run installation
curl -fsSL https://raw.githubusercontent.com/your-repo/install.sh | sudo bash
```

## 🔧 Configuration

### Environment Variables
```bash
# Optional environment variables
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_HEADLESS=true
export PLAYWRIGHT_BROWSERS_PATH=/app/.cache/ms-playwright
```

### Nginx Configuration
Edit `nginx.conf` to:
- Replace `your-domain.com` with your actual domain
- Configure SSL certificates for HTTPS
- Adjust rate limiting if needed

### Firewall Configuration
```bash
# Ubuntu/Debian with ufw
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Or with iptables
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8501 -j ACCEPT
```

## 📊 Monitoring and Maintenance

### Health Checks
```bash
# Check if service is running
systemctl status visual-regression-testing

# Check application health
curl http://localhost:8501/_stcore/health

# View logs
journalctl -u visual-regression-testing -f
```

### Docker Health Checks
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart
```

### Backup
```bash
# Backup test results
tar -czf backup-$(date +%Y%m%d).tar.gz test_results/

# Backup with Docker
docker run --rm -v visual_regression_testing_test_results:/data -v $(pwd):/backup alpine tar czf /backup/backup-$(date +%Y%m%d).tar.gz -C /data .
```

## 🔒 Security Considerations

1. **Use HTTPS**: Configure SSL certificates for production
2. **Firewall**: Only open necessary ports
3. **Updates**: Keep system and dependencies updated
4. **Monitoring**: Set up log monitoring and alerts
5. **Backups**: Regular backups of test results and configuration

## 🐛 Troubleshooting

### Common Issues

**Service won't start:**
```bash
# Check logs
journalctl -u visual-regression-testing -f

# Check Python environment
/opt/visual-regression-testing/venv/bin/python --version
```

**Docker container fails:**
```bash
# Check container logs
docker logs visual-regression-testing

# Check if ports are available
netstat -tlnp | grep 8501
```

**Nginx 502 error:**
```bash
# Check if Streamlit is running
curl http://localhost:8501/_stcore/health

# Check nginx logs
tail -f /var/log/nginx/error.log
```

**Playwright browsers missing:**
```bash
# Reinstall browsers
playwright install chromium firefox webkit
```

## 📞 Support

If you encounter issues:
1. Check the logs first
2. Verify all dependencies are installed
3. Ensure ports are accessible
4. Check system resources (RAM, disk space)

For additional help, check the main README.md or create an issue in the repository.
