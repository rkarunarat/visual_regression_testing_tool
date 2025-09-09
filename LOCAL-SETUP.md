# 🐍 Local Python Setup Guide

This guide helps you set up the Visual Regression Testing Tool using Python without Docker.

## 📋 Prerequisites

- **Python 3.11+** installed
- **Git** installed
- **Internet connection** for downloading dependencies

## 🚀 Quick Setup

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd visual_regression_testing_tool
```

### 2. Run the Setup Script

**Linux/macOS:**
```bash
./deploy-local.sh
```

**Windows:**
```cmd
deploy-local.bat
```

### 3. Access the Application
Open your browser and go to: **http://localhost:8501**

## 🔧 What the Setup Script Does

1. **Creates Virtual Environment**: Isolated Python environment
2. **Installs Dependencies**: All required Python packages
3. **Installs Playwright**: Browser automation framework
4. **Installs Browsers**: Chromium, Firefox, WebKit
5. **Runs Tests**: Verifies everything works correctly
6. **Starts Application**: Launches the Streamlit web interface

## 🛠️ Manual Setup (Alternative)

If you prefer to set up manually:

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Install Playwright
```bash
playwright install
playwright install-deps  # System dependencies
```

### 4. Run Tests
```bash
python test_functionality.py
```

### 5. Start Application
```bash
streamlit run app.py
```

## 🔍 Troubleshooting

### Python Version Issues
```bash
# Check Python version
python3 --version

# Should be 3.11 or higher
```

### Permission Issues (Linux/macOS)
```bash
# Make script executable
chmod +x deploy-local.sh
```

### Playwright Installation Issues
```bash
# Install system dependencies manually
playwright install-deps

# Or install specific browsers
playwright install chromium
```

### Port Already in Use
```bash
# Kill process using port 8501
lsof -ti:8501 | xargs kill -9  # Linux/macOS
netstat -ano | findstr :8501   # Windows
```

### Virtual Environment Issues
```bash
# Remove and recreate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

## 📁 Project Structure

```
visual_regression_testing_tool/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── deploy-local.sh       # Linux/macOS setup script
├── deploy-local.bat      # Windows setup script
├── test_functionality.py # Test suite
├── venv/                 # Virtual environment (created by script)
├── test_results/         # Test results (created by script)
└── logs/                 # Application logs (created by script)
```

## 🔄 Updating the Application

### 1. Pull Latest Changes
```bash
git pull
```

### 2. Update Dependencies
```bash
source venv/bin/activate  # Activate virtual environment
pip install -r requirements.txt --upgrade
```

### 3. Restart Application
```bash
streamlit run app.py
```

## 🎯 Usage

Once the application is running:

1. **Open Browser**: Go to http://localhost:8501
2. **Add URLs**: Enter staging and production URLs
3. **Configure Tests**: Select browsers and devices
4. **Run Tests**: Click "Run Visual Regression Tests"
5. **View Results**: Compare screenshots and analyze differences

## 🆘 Getting Help

If you encounter issues:

1. **Check Logs**: Look at the terminal output for error messages
2. **Run Tests**: `python test_functionality.py` to verify setup
3. **Check Dependencies**: `pip list` to see installed packages
4. **Reinstall**: Delete `venv` folder and run setup script again

## 🔗 Next Steps

- **Production Deployment**: See [PRODUCTION-DEPLOYMENT.md](PRODUCTION-DEPLOYMENT.md)
- **Docker Setup**: See main [README.md](README.md)
- **Configuration**: See [env.example](env.example) for environment options

---

**🎉 You're all set! Your Visual Regression Testing Tool is running locally.**
