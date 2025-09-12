# 🔍 Visual Regression Testing Tool

Catch visual bugs before users do! A comprehensive Streamlit-based solution for automated visual testing with advanced screenshot comparison, real-time progress tracking, and detailed reporting.

## 🛠️ Technology Stack

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.49%2B-ff4b4b?logo=streamlit)
![Playwright](https://img.shields.io/badge/Playwright-1.55%2B-brightgreen)
![Pillow](https://img.shields.io/badge/Pillow-11.3%2B-9cf)
![OpenCV](https://img.shields.io/badge/OpenCV-4.11%2B-5C3EE8?logo=opencv&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![Deployment](https://img.shields.io/badge/Deployment-Production%20Ready-28a745)

## 🎯 What Problems Does This Solve?

### **For QA Teams**
- **Catch visual regressions** before they reach production
- **Automate repetitive visual testing** across multiple browsers and devices
- **Generate professional reports** for stakeholders
- **Compare staging vs production** environments instantly

### **For Frontend Developers**
- **Verify responsive design** across different screen sizes
- **Test cross-browser compatibility** automatically
- **Detect layout shifts** and visual inconsistencies
- **Validate UI changes** before deployment

### **For DevOps Teams**
- **Integrate visual testing** into CI/CD pipelines
- **Monitor production visual health** continuously
- **Deploy with confidence** knowing visual changes are tracked
- **Scale testing** across multiple environments

### **For Product Teams**
- **Ensure brand consistency** across all touchpoints
- **Validate A/B test results** visually
- **Maintain design system integrity**
- **Track visual changes** over time

## ✨ Key Features

- **🌐 Multi-Browser Testing**: Chrome, Firefox, Safari, Edge support
- **📱 Device Emulation**: Desktop, Tablet, Mobile testing
- **🔍 Advanced Comparison**: SSIM, pixel-level, and histogram analysis
- **📊 Real-Time Progress**: Live testing updates and metrics
- **📄 Professional Reports**: PDF reports with detailed comparisons
- **🌍 Region Testing**: Geo-specific testing with locale/timezone support
- **📈 Result Management**: Export, cleanup, and detailed comparison views
- **🚀 Easy Deployment**: Docker-ready with production configurations

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
# Clone and deploy
git clone <your-repo-url>
cd visual_regression_testing_tool
./deploy.sh local

# Access at http://localhost:8501
```

### Option 2: Local Python
```bash
# Install and run
./deploy-local.sh
# Access at http://localhost:8501
```

📖 **Detailed deployment guides**: [README-DEPLOYMENT.md](README-DEPLOYMENT.md) | [PRODUCTION-DEPLOYMENT.md](PRODUCTION-DEPLOYMENT.md)

## 🎯 Use Cases

### **Web Development Workflow**
1. **Staging vs Production**: Compare your staging environment with production
2. **Feature Branches**: Test new features against main branch
3. **Responsive Design**: Verify layouts across devices
4. **Cross-Browser**: Ensure compatibility across browsers

### **CI/CD Integration**
- **Automated Testing**: Run visual tests on every deployment
- **Regression Detection**: Catch visual changes in pull requests
- **Quality Gates**: Block deployments with visual regressions
- **Monitoring**: Continuous visual health monitoring

### **Design System Validation**
- **Component Testing**: Test individual UI components
- **Brand Consistency**: Ensure design system compliance
- **A/B Testing**: Compare different design variations
- **Accessibility**: Visual accessibility testing

## 🏗️ How It Works

1. **Configure URLs**: Add staging and production URL pairs
2. **Select Browsers/Devices**: Choose testing combinations
3. **Run Tests**: Automated screenshot capture and comparison
4. **Analyze Results**: Side-by-side, overlay, and diff views
5. **Export Reports**: PDF reports and detailed exports

## 🛠️ Technology Stack

- **Frontend**: Streamlit web interface
- **Automation**: Playwright browser automation
- **Image Processing**: PIL, OpenCV, scikit-image
- **Deployment**: Docker containers with nginx
- **Reporting**: ReportLab PDF generation

## 📊 Comparison Views

- **Side-by-Side**: Staging vs Production comparison
- **Overlay**: Transparent overlay with opacity control
- **Difference**: Highlighted visual differences
- **Metrics**: Similarity scores and detailed analysis

## 🌍 Region Testing

Test your applications from different geographic locations:
- **USA**: New York timezone and locale
- **Europe**: London timezone and locale
- **Asia**: Tokyo timezone and locale
- **Middle East**: Dubai timezone and locale
- **And more...**

## 📈 Perfect For

- **QA Engineers** - Automated visual regression testing
- **Frontend Developers** - Cross-browser and responsive testing
- **DevOps Teams** - CI/CD integration and monitoring
- **Product Teams** - Design validation and A/B testing
- **Web Agencies** - Client project quality assurance

## 🎯 Why Choose This Tool?

- ✅ **No Complex Setup** - Just run and test
- ✅ **Professional Reports** - PDF exports with detailed analysis
- ✅ **Real-Time Updates** - Live progress tracking
- ✅ **Production Ready** - Docker deployment with health checks
- ✅ **Cross-Platform** - Works on Windows, macOS, Linux
- ✅ **Active Development** - Regular updates and improvements

## 📚 Documentation

- **[Deployment Guide](README-DEPLOYMENT.md)** - Complete deployment instructions
- **[Production Setup](PRODUCTION-DEPLOYMENT.md)** - Production server deployment
- **[Local Setup](LOCAL-SETUP.md)** - Local development setup
- **[File Structure](FILE-STRUCTURE.md)** - Project organization

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines and feel free to submit issues and pull requests.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Built with ❤️ for the testing community**

*Catch visual bugs before users do!*