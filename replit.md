# Visual Regression Testing Tool

## Overview

This is a Visual Regression Testing Tool built with Streamlit that compares staging and production websites across multiple browsers and devices. The application captures screenshots of web pages and performs visual comparisons to detect differences, helping identify visual regressions in web applications during the development lifecycle.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit for the web interface
- **Design Pattern**: Single-page application with sidebar configuration
- **State Management**: Streamlit session state for maintaining test results and browser manager instances
- **UI Components**: Form-based configuration, data tables for results display, and image comparison viewers

### Backend Architecture
- **Core Components**:
  - `BrowserManager`: Handles browser automation using Playwright
  - `ImageComparator`: Performs visual comparison using multiple similarity metrics
  - `ResultManager`: Manages test result storage and retrieval
- **Design Pattern**: Modular component-based architecture with clear separation of concerns
- **Asynchronous Processing**: Uses asyncio for browser automation to handle multiple browser instances efficiently

### Browser Automation
- **Engine**: Playwright for cross-browser automation
- **Supported Browsers**: Chrome, Firefox, Safari, and Edge
- **Capabilities**: Headless browser operation, screenshot capture, and device emulation
- **Configuration**: Browser-specific launch options and user agent strings

### Image Processing and Comparison
- **Libraries**: PIL (Python Imaging Library), OpenCV, and scikit-image
- **Comparison Metrics**: 
  - Structural Similarity Index (SSIM)
  - Pixel-by-pixel similarity
  - Histogram similarity
- **Output**: Composite similarity score with visual difference highlighting

### Data Storage
- **File System**: Local file storage for screenshots and test results
- **Format**: JSON for test metadata, PNG for screenshots
- **Organization**: Hierarchical directory structure organized by test ID

### Configuration Management
- **Browser Configurations**: Centralized browser settings including engines, user agents, and launch options
- **Device Profiles**: Predefined device configurations for desktop, tablet, and mobile testing
- **Viewport Settings**: Configurable screen resolutions and device characteristics

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for the user interface
- **Playwright**: Browser automation library for taking screenshots
- **Pandas**: Data manipulation and analysis for results handling

### Image Processing
- **Pillow (PIL)**: Image processing and manipulation
- **OpenCV (cv2)**: Computer vision operations for image comparison
- **scikit-image**: Advanced image processing algorithms including SSIM calculation
- **NumPy**: Numerical operations for image array processing

### Utility Libraries
- **asyncio**: Asynchronous programming support for browser operations
- **logging**: Application logging and error tracking
- **pathlib**: Modern path handling for file system operations
- **datetime**: Timestamp management for test results
- **hashlib**: Hash generation for unique identifiers
- **urllib**: URL parsing and validation
- **base64**: Binary data encoding for download links
- **zipfile**: Archive creation for bulk result downloads

### System Requirements
- **Browser Dependencies**: Requires system browsers (Chrome, Firefox, Safari, Edge) to be installed
- **Operating System**: Cross-platform support (Windows, macOS, Linux)
- **Python Environment**: Python 3.7+ with pip package management