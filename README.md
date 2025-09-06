# Visual Diff

A Streamlit-based visual regression tool that screenshots pairs of URLs across browsers/devices, compares images, and reports differences.

## Features

- URL pairs input (manual/CSV)
- Multi-browser and multi-device testing (Chrome recommended)
- Per-combo screenshots (staging/production) and visual diff
- Detailed Comparison UI: side-by-side, overlay with opacity, diff
- Results management: list, load, export ZIP, delete/cleanup
- Reports: Summary PDF (table) and Full PDF (SxP, overlay, diff per test)
- **Production Ready**: Docker, systemd service, nginx reverse proxy, SSL support

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

## 🧪 Testing

Before deploying or pushing changes, run the comprehensive test suite:

```bash
# Run all functionality tests
python test_functionality.py

# Or use the test runner scripts
./run_tests.sh        # Linux/macOS
run_tests.bat         # Windows
```

The test suite verifies:
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

## Quick start

- Python 3.11+
- Create and activate a virtual environment (recommended):

Windows (PowerShell):
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:
```
python3 -m venv .venv
source .venv/bin/activate
```

- Install dependencies and Playwright browsers:
```
pip install -r requirements.txt
python -m playwright install chromium
```

- Run locally:
```
streamlit run app.py
```

- Deactivate the venv when done: `deactivate`

## Folder structure

```
VisualDiff/
  app.py                  # Streamlit app
  browser_automation.py   # Playwright manager (internal)
  browser_manager.py      # Import alias for clarity
  image_comparison.py     # Comparator (internal)
  image_comparator.py     # Import alias for clarity
  result_manager.py       # Results persistence (internal)
  results_store.py        # Import alias for clarity
  config.py               # Browsers, devices, viewports
  utils.py                # UI/util helpers
  test_results/           # Saved runs: <test_id>/<browser>/<device>/
```

## Usage notes

- Start with Chrome. Firefox mobile/tablet emulation can be limited depending on environment.
- Results are stored under `test_results/<test_id>/<browser>/<device>/` with JSON + PNGs.
- Use Manage Test Runs to load, export, or delete runs.

## 🚀 Production Deployment

For production deployment on your own server, we provide comprehensive deployment options:

### 📖 [Complete Deployment Guide](README-DEPLOYMENT.md)

**Quick Start Options:**

#### 🐳 Docker Deployment (Recommended)
```bash
# One-command deployment
./deploy.sh local

# With nginx reverse proxy
./deploy.sh production
```

#### 🖥️ Native Server Installation
```bash
# Automated installation on Ubuntu/Debian
sudo ./install.sh
```

#### ☁️ Cloud Providers
- **AWS EC2**: Launch instance → Run install script
- **DigitalOcean**: Create droplet → Run install script
- **Google Cloud**: Create VM → Run install script

### Key Features
- ✅ **Production Ready**: Nginx reverse proxy, SSL support, security headers
- ✅ **Auto-Restart**: Systemd service with automatic restarts
- ✅ **Health Checks**: Built-in monitoring and health endpoints
- ✅ **Security**: Non-root user, restricted permissions, firewall configs
- ✅ **Monitoring**: Comprehensive logging and status checks
- ✅ **Backup Ready**: Easy backup scripts for test results

### Simple Manual Deployment
```bash
# Basic production run
streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

For detailed instructions, security configurations, and troubleshooting, see the [Complete Deployment Guide](README-DEPLOYMENT.md).

## Troubleshooting

- Firefox mobile/tablet: if runs fail, try Desktop only or use Chrome.
- Large pages: DecompressionBombWarning is handled; very tall mobile images are cropped in PDFs.
- If images don’t show after “Load Results”, the app loads them from disk automatically.
