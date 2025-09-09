# Visual Regression Testing Tool

A comprehensive Streamlit-based visual regression testing tool that captures screenshots of websites across multiple browsers and devices, compares them, and reports visual differences.

## ✨ Features

- **Multi-Browser Testing**: Chrome, Firefox, Safari, Edge support
- **Device Emulation**: Desktop, Tablet, Mobile device testing
- **Visual Comparison**: Side-by-side, overlay, and diff views
- **URL Management**: Manual input or CSV import for bulk testing
- **Results Management**: Export, cleanup, and detailed comparison views
- **PDF Reports**: Summary and detailed reports with screenshots
- **Production Ready**: Docker containerization, health checks, nginx support
- **WSL Compatible**: Works with Rancher Desktop and Windows Subsystem for Linux

## Dependencies

These reflect `requirements.txt`.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.49%2B-ff4b4b?logo=streamlit)
![Playwright](https://img.shields.io/badge/Playwright-1.55%2B-brightgreen)
![Pillow](https://img.shields.io/badge/Pillow-11.3%2B-9cf)
![NumPy](https://img.shields.io/badge/NumPy-2.3%2B-013243?logo=numpy&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.11%2B-5C3EE8?logo=opencv&logoColor=white)
![scikit-image](https://img.shields.io/badge/scikit--image-0.25%2B-F7931E)
![pandas](https://img.shields.io/badge/pandas-2.3%2B-150458?logo=pandas&logoColor=white)
![ReportLab](https://img.shields.io/badge/ReportLab-4.1%2B-6aa84f)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Deployment](https://img.shields.io/badge/Deployment-Production%20Ready-28a745)

Alternative stacks sometimes used elsewhere: Selenium, WebDriver Manager, ImageHash (not used here).

## 🚀 Quick Start

Choose your deployment method:

### Option 1: Docker Deployment (Recommended)
**Prerequisites:** Docker and Docker Compose installed
- **Docker Desktop** or **Rancher Desktop** (both work the same way)

```bash
# Local development (port 80)
./deploy.sh local

# Production deployment (with nginx)
./deploy.sh production

# Robust deployment (for network issues)
./deploy-robust.sh local
```

### Option 2: Local Python Environment
**Prerequisites:** Python 3.11+ installed
- No Docker required
- Uses virtual environment
- Installs all dependencies automatically

```bash
# Linux/macOS
./deploy-local.sh

# Windows
deploy-local.bat
```

**Access:** http://localhost:8501

📖 **[LOCAL-SETUP.md](LOCAL-SETUP.md)** - Detailed local setup guide

### Deployment Method Comparison

| Feature | Docker Deployment | Local Python Deployment |
|---------|------------------|------------------------|
| **Setup Complexity** | ⭐⭐ Simple | ⭐⭐⭐ Moderate |
| **Dependencies** | Docker + Docker Compose | Python 3.11+ |
| **Isolation** | ✅ Complete container isolation | ✅ Virtual environment |
| **Port** | 80 (local) or 80 (production) | 8501 |
| **Resource Usage** | Higher (container overhead) | Lower (native Python) |
| **Cross-platform** | ✅ Works everywhere | ⚠️ Platform-specific |
| **Production Ready** | ✅ With nginx | ⚠️ Manual setup needed |
| **Updates** | `./deploy.sh` | `git pull && ./deploy-local.sh` |

### What Happens During Deployment

**Docker Deployment:**
1. **Docker Build**: Creates container with Python, Playwright, and all dependencies
2. **Browser Installation**: Automatically installs Chromium, Firefox, and WebKit
3. **Health Checks**: Verifies application is running correctly
4. **Ready to Use**: Access the web interface at localhost (port 80) or localhost:8501

**Local Python Deployment:**
1. **Virtual Environment**: Creates isolated Python environment
2. **Dependencies**: Installs all required Python packages
3. **Playwright Setup**: Installs browsers and system dependencies
4. **Testing**: Runs functionality tests to verify setup
5. **Ready to Use**: Starts Streamlit application at localhost:8501

## 🧪 Testing

### Running Tests

**Option 1: Tests run automatically during deployment**
```bash
# Docker deployment - tests run inside container
./deploy.sh local

# Local Python deployment - tests run in virtual environment
./deploy-local.sh
```

**Option 2: Run tests locally (requires Python dependencies)**
```bash
# Install dependencies first
pip install -r requirements.txt

# Then run tests
python test_functionality.py

# Or use the test runner scripts
./run_tests.sh        # Linux/macOS
run_tests.bat         # Windows
```

**Option 3: Run tests in Docker container**
```bash
# Build and run tests in container
docker build -f Dockerfile -t visual-regression-testing .
docker run --rm visual-regression-testing python test_functionality.py
```

### What Tests Verify
- ✅ All imports and dependencies
- ✅ Configuration data integrity
- ✅ Utility functions
- ✅ Class instantiation
- ✅ App syntax and structure
- ✅ Session state handling
- ✅ Cleanup and partial results functionality
- ✅ Playwright setup
- ✅ PDF generation fallbacks
- ✅ Deployment files
- ✅ Requirements file

> **Note**: If you run tests on host system without Python dependencies, some tests will fail. This is normal! Tests run automatically inside Docker container during deployment.

## 🐳 Deployment Options

### Local Development (WSL/Desktop)
```bash
./deploy.sh local
```
- ✅ Runs on **port 80** (http://localhost)
- ✅ Direct Streamlit access
- ✅ Perfect for WSL + Rancher Desktop
- ✅ No nginx overhead

### Production Deployment (AWS/Digital Ocean)
```bash
./deploy.sh production
```
- ✅ Runs on **port 80** (http://your-server-ip)
- ✅ Includes nginx reverse proxy
- ✅ Security headers and rate limiting
- ✅ Ready for SSL/HTTPS setup

### Robust Deployment (For Network Issues)
```bash
./deploy-robust.sh local      # For local development
./deploy-robust.sh production # For production
```
- ✅ Uses robust Dockerfile with fallback logic
- ✅ Handles package download issues gracefully
- ✅ Best for environments with network restrictions


### Useful Commands
```bash
# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Restart application
docker-compose restart

# Update application
./deploy.sh local        # For local development
./deploy.sh production   # For production

# Check container status
docker-compose ps
```

## ⚙️ Configuration

### Environment Variables

You can customize the application using environment variables:

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

## 🌐 Production Deployment

For deploying to AWS, Digital Ocean, or other cloud providers, see the comprehensive guide:

📖 **[PRODUCTION-DEPLOYMENT.md](PRODUCTION-DEPLOYMENT.md)** - Complete production setup guide

**Quick Production Setup:**
1. Deploy to your server: `./deploy.sh production`
2. Configure your domain DNS to point to server IP
3. Access at: `http://your-domain.com` (port 80)
4. Optional: Set up SSL with Let's Encrypt

## 🎯 How to Use

### 1. Configure Test URLs
- Add staging and production URL pairs manually
- Or import from CSV for bulk testing
- Set wait times and similarity thresholds

### 2. Select Browsers & Devices
- **Browsers**: Chrome, Firefox, Safari, Edge
- **Devices**: Desktop, Tablet, Mobile (with device emulation)
- **Viewports**: Automatic sizing based on device selection

### 3. Run Visual Tests
- Execute tests across all browser/device combinations
- Real-time progress tracking
- Automatic screenshot capture

### 4. Analyze Results
- **Side-by-side comparison**: Staging vs Production
- **Overlay view**: With opacity control
- **Diff view**: Highlighted differences
- **Similarity scores**: SSIM, pixel, and histogram metrics

### 5. Export & Manage
- **PDF Reports**: Summary and detailed reports
- **ZIP Export**: All screenshots and data
- **Result Management**: Load, delete, cleanup old tests

## 🏗️ Architecture

- **Frontend**: Streamlit web interface with real-time updates
- **Browser Automation**: Playwright for cross-browser testing
- **Image Processing**: PIL, OpenCV, scikit-image for visual comparison
- **Storage**: Local file system with organized test results
- **Deployment**: Docker containers with health checks and nginx support
- **Testing**: Comprehensive test suite for all functionality

## 📁 Project Structure

```
visual_regression_testing_tool/
├── 🐳 Docker & Deployment
│   ├── Dockerfile              # Standard production Dockerfile
│   ├── Dockerfile.robust       # Robust version for network issues
│   ├── docker-compose.yml      # Docker Compose configuration
│   ├── deploy.sh               # Standard deployment script
│   └── deploy-robust.sh        # Robust deployment script
├── 🎯 Core Application
│   ├── app.py                  # Main Streamlit application
│   ├── browser_automation.py   # Playwright browser automation
│   ├── browser_manager.py      # Browser manager wrapper
│   ├── config.py               # Configuration settings
│   ├── image_comparator.py     # Image comparison logic
│   ├── image_comparison.py     # Image comparison utilities
│   ├── result_manager.py       # Test result management
│   ├── results_store.py        # Result storage utilities
│   ├── utils.py                # Utility functions
│   └── test_functionality.py   # Comprehensive test suite
├── 📚 Documentation
│   ├── README.md               # Main documentation
│   ├── DEPLOYMENT-GUIDE.md     # Deployment guide
│   ├── FILE-STRUCTURE.md       # File structure overview
│   └── rancher-desktop-setup.md # Rancher Desktop setup
└── 🧪 Testing
    ├── run_tests.sh            # Linux/macOS test runner
    └── run_tests.bat           # Windows test runner
```

## 📖 Additional Documentation

- **[Deployment Guide](README-DEPLOYMENT.md)** - Complete deployment instructions
- **[File Structure](FILE-STRUCTURE.md)** - Detailed file organization

## 🚨 Troubleshooting

### Common Issues

**Build Issues:**
- Use `./deploy-robust.sh` for network/package download issues
- Check Docker daemon is running: `docker info`
- Ensure sufficient disk space for browser downloads

**Access Issues:**
- Verify port 8501 is available: `netstat -an | grep 8501`
- Check firewall settings
- Ensure Docker containers are running: `docker-compose ps`

**Browser Issues:**
- Playwright browsers are installed automatically in containers
- No need for local browser installation
- Works in headless mode for all browsers

**Performance Issues:**
- Start with Chrome for best compatibility
- Firefox mobile/tablet emulation may be limited
- Large pages are handled automatically with image optimization

### Getting Help

- Check logs: `docker-compose logs -f`
- View container status: `docker-compose ps`
- Restart if needed: `docker-compose restart`
