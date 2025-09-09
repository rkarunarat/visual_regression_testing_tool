# 🚀 Production Deployment Guide

This guide covers deploying the Visual Regression Testing Tool to production servers like AWS EC2, Digital Ocean, or any cloud provider.

## 📋 Prerequisites

- **Server**: Ubuntu 20.04+ or similar Linux distribution
- **Docker**: Installed and running
- **Docker Compose**: Installed
- **Domain**: Optional (for custom domain setup)
- **SSL Certificate**: Optional (for HTTPS)

## 🛠️ Server Setup

### 1. Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again to apply docker group changes
```

### 2. Clone and Setup Application

```bash
# Clone your repository
git clone <your-repo-url>
cd visual_regression_testing_tool

# Make scripts executable
chmod +x deploy.sh deploy-robust.sh
```

## 🌐 Deployment Options

### Option 1: Standard Production Deployment

```bash
# Deploy with nginx reverse proxy
./deploy.sh production
```

**What this does:**
- ✅ Runs app on port 80 (standard HTTP port)
- ✅ Uses nginx reverse proxy for better performance
- ✅ Includes security headers and rate limiting
- ✅ Ready for SSL/HTTPS setup

**Access:** `http://your-server-ip` or `http://your-domain.com`

### Option 2: Robust Deployment (if network issues)

```bash
# Deploy with fallback build strategy
./deploy-robust.sh production
```

**What this does:**
- ✅ Same as standard but with fallback Docker build
- ✅ Handles network issues during package installation
- ✅ More reliable for servers with limited internet

## 🔧 Configuration

### Environment Variables

Create a `.env` file for custom configuration:

```bash
# Copy the example file
cp env.example .env

# Edit the configuration
nano .env
```

**Key Configuration Options:**
- `EXTERNAL_PORT`: External port (default: 80)
- `STREAMLIT_SERVER_PORT`: Internal Streamlit port (default: 8501)
- `DOMAIN`: Your domain for production (optional)
- `LOG_LEVEL`: Logging level (default: INFO)
- `SECRET_KEY`: Secret key for production (recommended)

### Custom Domain Setup

1. **Update nginx.conf:**
```bash
# Edit nginx.conf
nano nginx.conf

# Change this line:
server_name _;  # Accept any domain

# To your domain:
server_name your-domain.com www.your-domain.com;
```

2. **Point DNS to your server:**
```
A Record: your-domain.com → your-server-ip
A Record: www.your-domain.com → your-server-ip
```

### SSL/HTTPS Setup (Optional)

1. **Install Certbot:**
```bash
sudo apt install certbot python3-certbot-nginx
```

2. **Get SSL Certificate:**
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

3. **Auto-renewal:**
```bash
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔍 Monitoring and Maintenance

### Check Application Status

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f

# Check health
curl http://localhost/health
```

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
./deploy.sh production
```

### Backup Test Results

```bash
# Backup test results
tar -czf test_results_backup_$(date +%Y%m%d).tar.gz test_results/

# Restore test results
tar -xzf test_results_backup_20240101.tar.gz
```

## 🚨 Troubleshooting

### Common Issues

**1. Port 80 already in use:**
```bash
# Check what's using port 80
sudo netstat -tlnp | grep :80

# Stop conflicting service
sudo systemctl stop apache2  # or nginx
```

**2. Docker build fails:**
```bash
# Try robust deployment
./deploy-robust.sh production

# Or check network connectivity
ping google.com
```

**3. Application not accessible:**
```bash
# Check firewall
sudo ufw status
sudo ufw allow 80
sudo ufw allow 443

# Check Docker containers
docker-compose ps
docker-compose logs
```

**4. SSL certificate issues:**
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate
sudo certbot renew
```

### Performance Optimization

**1. Increase server resources:**
- Minimum: 2GB RAM, 2 CPU cores
- Recommended: 4GB RAM, 4 CPU cores

**2. Optimize Docker:**
```bash
# Clean up unused images
docker system prune -a

# Monitor resource usage
docker stats
```

## 📊 Production Checklist

- [ ] Server has sufficient resources (2GB+ RAM)
- [ ] Docker and Docker Compose installed
- [ ] Application deployed successfully
- [ ] Health check passes
- [ ] Domain configured (if using custom domain)
- [ ] SSL certificate installed (if using HTTPS)
- [ ] Firewall configured (ports 80, 443 open)
- [ ] Backup strategy in place
- [ ] Monitoring setup (optional)

## 🔗 Quick Commands Reference

```bash
# Deploy
./deploy.sh production

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Restart application
docker-compose restart

# Update application
git pull && ./deploy.sh production
```

## 📞 Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify server resources: `docker stats`
3. Test connectivity: `curl http://localhost/health`
4. Review this guide for troubleshooting steps

---

**🎉 Your Visual Regression Testing Tool is now running in production!**
