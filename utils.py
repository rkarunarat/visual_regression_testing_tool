import base64
import io
import re
from urllib.parse import urlparse
from PIL import Image
import streamlit as st
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def validate_url(url):
    """Validate if a URL is properly formatted"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def sanitize_filename(filename):
    """Sanitize filename for cross-platform compatibility"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length and remove trailing dots/spaces
    filename = filename[:100].strip('. ')
    
    # Ensure it's not empty
    if not filename:
        filename = f"unnamed_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    return filename

def create_download_link(data, filename, link_text="Download"):
    """Create a download link for data"""
    if isinstance(data, str):
        # Text data
        b64 = base64.b64encode(data.encode()).decode()
        href = f'<a href="data:text/plain;base64,{b64}" download="{filename}">{link_text}</a>'
    else:
        # Binary data
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{link_text}</a>'
    
    return href

def image_to_base64(image):
    """Convert PIL Image to base64 string"""
    try:
        buffered = io.BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        return f"data:image/png;base64,{img_base64}"
    except Exception as e:
        logger.error(f"Error converting image to base64: {e}")
        return None

def resize_image_for_display(image, max_width=800, max_height=600):
    """Resize image for display while maintaining aspect ratio"""
    try:
        width, height = image.size
        
        # Calculate scaling factor
        width_scale = max_width / width
        height_scale = max_height / height
        scale = min(width_scale, height_scale, 1.0)  # Don't upscale
        
        if scale < 1.0:
            new_width = int(width * scale)
            new_height = int(height * scale)
            return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        return image
        
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return image

def format_similarity_score(score):
    """Format similarity score for display"""
    return f"{score:.1f}%"

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

def get_device_icon(device_name):
    """Get appropriate icon for device type"""
    device_icons = {
        'Desktop': '🖥️',
        'Desktop Mac': '💻',
        'Tablet': '📱',
        'Tablet Android': '📱',
        'Mobile': '📱',
        'Mobile Android': '📱'
    }
    return device_icons.get(device_name, '🔍')

def get_browser_icon(browser_name):
    """Get appropriate icon for browser type"""
    browser_icons = {
        'Chrome': '🔵',
        'Firefox': '🟠',
        'Safari': '🔵',
        'Edge': '🟦'
    }
    return browser_icons.get(browser_name, '🌐')

def get_status_icon(is_match):
    """Get status icon based on test result"""
    return "✅" if is_match else "❌"

def format_timestamp(timestamp_str):
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return timestamp_str

def create_summary_card(title, value, delta=None, help_text=None):
    """Create a summary metric card"""
    st.metric(
        label=title,
        value=value,
        delta=delta,
        help=help_text
    )

def display_error_message(error_type, details=None):
    """Display standardized error messages"""
    error_messages = {
        'invalid_url': "❌ Invalid URL format. Please check your URLs.",
        'browser_error': "❌ Browser initialization failed. Please try again.",
        'comparison_error': "❌ Image comparison failed. Check the screenshots.",
        'network_error': "❌ Network error. Please check your internet connection.",
        'timeout_error': "❌ Request timed out. The page may be loading slowly.",
        'permission_error': "❌ Permission denied. Check file access rights."
    }
    
    base_message = error_messages.get(error_type, "❌ An error occurred.")
    
    if details:
        st.error(f"{base_message}\n\nDetails: {details}")
    else:
        st.error(base_message)

def display_success_message(success_type, details=None):
    """Display standardized success messages"""
    success_messages = {
        'test_completed': "✅ Tests completed successfully!",
        'export_completed': "✅ Results exported successfully!",
        'browser_ready': "✅ Browser initialized successfully!",
        'comparison_completed': "✅ Image comparison completed!"
    }
    
    base_message = success_messages.get(success_type, "✅ Operation completed successfully!")
    
    if details:
        st.success(f"{base_message} {details}")
    else:
        st.success(base_message)

def create_progress_indicator(current, total, description="Processing"):
    """Create a progress indicator"""
    progress = current / total if total > 0 else 0
    st.progress(int(progress * 100), text=f"{description}... {current}/{total}")

def extract_domain_from_url(url):
    """Extract domain name from URL for display"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except Exception:
        return url

def calculate_test_duration(start_time, end_time):
    """Calculate test duration in human readable format"""
    try:
        if isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time)
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time)
        
        duration = end_time - start_time
        
        if duration.total_seconds() < 60:
            return f"{duration.total_seconds():.1f} seconds"
        elif duration.total_seconds() < 3600:
            return f"{duration.total_seconds() / 60:.1f} minutes"
        else:
            return f"{duration.total_seconds() / 3600:.1f} hours"
            
    except Exception as e:
        logger.error(f"Error calculating duration: {e}")
        return "Unknown"

def safe_divide(numerator, denominator, default=0):
    """Safely divide two numbers with default fallback"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default

def truncate_text(text, max_length=50):
    """Truncate text with ellipsis if too long"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
