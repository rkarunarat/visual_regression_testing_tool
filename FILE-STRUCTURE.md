# File Structure Overview

## 📁 Complete Project Structure

```
visual_regression_testing_tool/
├── 🐳 Docker & Deployment
│   ├── Dockerfile              # Standard production Dockerfile
│   ├── Dockerfile.robust       # Robust version for network issues
│   ├── docker-compose.yml      # Docker Compose configuration
│   ├── deploy.sh               # Standard deployment script
│   ├── deploy-robust.sh        # Robust deployment script
│   ├── deploy-local.sh         # Local Python deployment (Linux/macOS)
│   ├── deploy-local.bat        # Local Python deployment (Windows)
│   └── nginx.conf              # Nginx configuration for production
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
│   ├── README-DEPLOYMENT.md    # Complete deployment guide
│   ├── PRODUCTION-DEPLOYMENT.md # Production deployment guide
│   ├── LOCAL-SETUP.md          # Local Python setup guide
│   ├── FILE-STRUCTURE.md       # This file
│   └── replit.md               # Replit-specific documentation
├── 🧪 Testing
│   ├── run_tests.sh            # Linux/macOS test runner
│   └── run_tests.bat           # Windows test runner
├── ⚙️ Configuration
│   ├── requirements.txt        # Python dependencies
│   ├── pyproject.toml          # Python project configuration
│   ├── uv.lock                 # UV lock file
│   ├── env.example             # Environment variables template
│   ├── .env                    # Environment variables (ignored by git)
│   ├── .gitignore              # Git ignore patterns
│   └── .dockerignore           # Docker ignore patterns
└── 🔧 System Files
    └── systemd/
        └── visual-regression-testing.service # Systemd service file
```

## 📋 File Descriptions

### 🐳 Docker & Deployment
- **`Dockerfile`** - Standard production Dockerfile with optimized Playwright setup
- **`Dockerfile.robust`** - Robust version that handles network issues gracefully
- **`docker-compose.yml`** - Docker Compose configuration for easy deployment
- **`deploy.sh`** - Standard deployment script (recommended)
- **`deploy-robust.sh`** - Robust deployment script for network issues
- **`nginx.conf`** - Nginx reverse proxy configuration for production

### 🎯 Core Application
- **`app.py`** - Main Streamlit web application with all UI components
- **`browser_automation.py`** - Playwright browser automation and screenshot capture
- **`browser_manager.py`** - Wrapper for browser automation (import alias)
- **`config.py`** - Configuration for browsers, devices, and viewports
- **`image_comparator.py`** - Image comparison logic and similarity calculations
- **`image_comparison.py`** - Image comparison utilities (import alias)
- **`result_manager.py`** - Test result management and storage
- **`results_store.py`** - Result storage utilities (import alias)
- **`utils.py`** - Utility functions for UI and file operations
- **`test_functionality.py`** - Comprehensive test suite for all functionality

### 📚 Documentation
- **`README.md`** - Main project documentation with quick start guide
- **`README-DEPLOYMENT.md`** - Complete deployment instructions (Docker + Native)
- **`FILE-STRUCTURE.md`** - This file structure overview
- **`replit.md`** - Replit-specific setup and usage

### 🧪 Testing
- **`run_tests.sh`** - Linux/macOS test runner script
- **`run_tests.bat`** - Windows test runner script

### ⚙️ Configuration
- **`requirements.txt`** - Python package dependencies
- **`pyproject.toml`** - Python project configuration and metadata
- **`uv.lock`** - UV package manager lock file

### 🔧 System Files
- **`systemd/visual-regression-testing.service`** - Systemd service file for production deployment

## 🚀 Quick Commands

### Deployment
```bash
# Standard deployment (recommended)
./deploy.sh

# Robust deployment (for network issues)
./deploy-robust.sh

# Production with nginx
./deploy.sh production
```

### Management
```bash
# View logs
docker-compose logs -f

# Stop application
docker-compose down

# Restart application
docker-compose restart

# Check status
docker-compose ps
```

### Testing
```bash
# Run functionality tests
python test_functionality.py

# Use test runners
./run_tests.sh        # Linux/macOS
run_tests.bat         # Windows
```

## 📁 Generated Directories

When running the application, these directories are created:
- **`test_results/`** - Contains all test results organized by test ID
- **`logs/`** - Application logs and error reports
- **`ssl/`** - SSL certificates for production deployment (if using nginx)
