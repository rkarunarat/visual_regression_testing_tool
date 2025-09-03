import numpy as np
from PIL import Image, ImageDraw, ImageChops
import cv2
from skimage.metrics import structural_similarity as ssim
import io
import logging

logger = logging.getLogger(__name__)

class ImageComparator:
    def __init__(self):
        self.default_threshold = 95.0
    
    def compare_images(self, image1, image2, threshold=None):
        """
        Compare two PIL Images and return comparison results
        
        Args:
            image1: PIL Image (staging)
            image2: PIL Image (production)
            threshold: Similarity threshold percentage (default: 95.0)
        
        Returns:
            dict: Comparison results with similarity score, match status, and diff image
        """
        if threshold is None:
            threshold = self.default_threshold
        
        try:
            # Ensure images are the same size
            image1, image2 = self.resize_images_to_match(image1, image2)
            
            # Convert to numpy arrays
            img1_np = np.array(image1)
            img2_np = np.array(image2)
            
            # Calculate multiple similarity metrics
            similarity_scores = self.calculate_similarity_metrics(img1_np, img2_np)
            
            # Use the average of different similarity metrics
            final_score = np.mean([
                similarity_scores['ssim'],
                similarity_scores['pixel_similarity'],
                similarity_scores['histogram_similarity']
            ])
            
            # Determine if images match based on threshold
            is_match = final_score >= (threshold / 100.0)
            
            # Generate difference image
            diff_image = self.create_difference_image(image1, image2) if not is_match else None
            
            return {
                'similarity_score': final_score * 100,
                'is_match': is_match,
                'diff_image': diff_image,
                'detailed_scores': {
                    'ssim': similarity_scores['ssim'] * 100,
                    'pixel_similarity': similarity_scores['pixel_similarity'] * 100,
                    'histogram_similarity': similarity_scores['histogram_similarity'] * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Error comparing images: {e}")
            return {
                'similarity_score': 0.0,
                'is_match': False,
                'diff_image': None,
                'error': str(e)
            }
    
    def resize_images_to_match(self, image1, image2):
        """Resize images to have the same dimensions"""
        # Get dimensions
        w1, h1 = image1.size
        w2, h2 = image2.size
        
        # Use the larger dimensions to avoid information loss
        target_width = max(w1, w2)
        target_height = max(h1, h2)
        
        # Resize both images
        if (w1, h1) != (target_width, target_height):
            # Create new image with white background
            new_image1 = Image.new('RGB', (target_width, target_height), 'white')
            new_image1.paste(image1, (0, 0))
            image1 = new_image1
        
        if (w2, h2) != (target_width, target_height):
            # Create new image with white background
            new_image2 = Image.new('RGB', (target_width, target_height), 'white')
            new_image2.paste(image2, (0, 0))
            image2 = new_image2
        
        return image1, image2
    
    def calculate_similarity_metrics(self, img1_np, img2_np):
        """Calculate various similarity metrics"""
        # Ensure images are the same shape
        if img1_np.shape != img2_np.shape:
            raise ValueError("Images must have the same dimensions")
        
        # Convert to grayscale for SSIM calculation
        if len(img1_np.shape) == 3:
            gray1 = cv2.cvtColor(img1_np, cv2.COLOR_RGB2GRAY)
            gray2 = cv2.cvtColor(img2_np, cv2.COLOR_RGB2GRAY)
        else:
            gray1 = img1_np
            gray2 = img2_np
        
        # Structural Similarity Index
        ssim_score = ssim(gray1, gray2, data_range=gray1.max() - gray1.min())
        
        # Pixel-wise similarity
        pixel_diff = np.abs(img1_np.astype(float) - img2_np.astype(float))
        pixel_similarity = 1.0 - (np.mean(pixel_diff) / 255.0)
        
        # Histogram similarity
        hist_similarity = self.calculate_histogram_similarity(img1_np, img2_np)
        
        return {
            'ssim': max(0, ssim_score),  # Ensure non-negative
            'pixel_similarity': max(0, pixel_similarity),
            'histogram_similarity': hist_similarity
        }
    
    def calculate_histogram_similarity(self, img1_np, img2_np):
        """Calculate histogram similarity between two images"""
        try:
            # Calculate histograms for each channel
            if len(img1_np.shape) == 3:
                # RGB image
                hist1 = [cv2.calcHist([img1_np], [i], None, [256], [0, 256]) for i in range(3)]
                hist2 = [cv2.calcHist([img2_np], [i], None, [256], [0, 256]) for i in range(3)]
            else:
                # Grayscale image
                hist1 = [cv2.calcHist([img1_np], [0], None, [256], [0, 256])]
                hist2 = [cv2.calcHist([img2_np], [0], None, [256], [0, 256])]
            
            # Calculate correlation for each channel
            correlations = []
            for h1, h2 in zip(hist1, hist2):
                correlation = cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)
                correlations.append(max(0, correlation))  # Ensure non-negative
            
            return np.mean(correlations)
            
        except Exception as e:
            logger.warning(f"Error calculating histogram similarity: {e}")
            return 0.0
    
    def create_difference_image(self, image1, image2):
        """Create an image highlighting the differences between two images"""
        try:
            # Ensure images are the same size
            image1, image2 = self.resize_images_to_match(image1, image2)
            
            # Calculate pixel differences
            diff = ImageChops.difference(image1, image2)
            
            # Convert to numpy array for processing
            diff_np = np.array(diff)
            
            # Create a more visible difference image
            # Convert to grayscale for threshold calculation
            gray_diff = cv2.cvtColor(diff_np, cv2.COLOR_RGB2GRAY)
            
            # Apply threshold to identify significant differences
            _, thresh = cv2.threshold(gray_diff, 30, 255, cv2.THRESH_BINARY)
            
            # Create colored difference image
            colored_diff = np.zeros_like(diff_np)
            
            # Color significant differences in red
            mask = thresh > 0
            colored_diff[mask] = [255, 0, 0]  # Red for differences
            
            # Blend with original images for context
            alpha = 0.7
            base_image = np.array(image1)
            blended = (alpha * base_image + (1 - alpha) * colored_diff).astype(np.uint8)
            
            # Add red highlighting where there are differences
            blended[mask] = [255, 100, 100]  # Light red for differences
            
            return Image.fromarray(blended)
            
        except Exception as e:
            logger.error(f"Error creating difference image: {e}")
            return None
    
    def create_overlay(self, image1, image2, opacity=0.5):
        """Create an overlay image with adjustable opacity"""
        try:
            # Ensure images are the same size
            image1, image2 = self.resize_images_to_match(image1, image2)
            
            # Convert to RGBA for transparency
            img1_rgba = image1.convert('RGBA')
            img2_rgba = image2.convert('RGBA')
            
            # Apply opacity to the first image
            img1_with_opacity = Image.new('RGBA', img1_rgba.size)
            img1_with_opacity = Image.blend(
                Image.new('RGBA', img1_rgba.size, (255, 255, 255, 0)),
                img1_rgba,
                opacity
            )
            
            # Composite the images
            overlay = Image.alpha_composite(img2_rgba, img1_with_opacity)
            
            return overlay.convert('RGB')
            
        except Exception as e:
            logger.error(f"Error creating overlay image: {e}")
            return image1  # Return original image as fallback
    
    def get_image_info(self, image):
        """Get basic information about an image"""
        return {
            'width': image.width,
            'height': image.height,
            'mode': image.mode,
            'format': image.format,
            'size_bytes': len(image.tobytes())
        }
    
    def preprocess_image(self, image):
        """Preprocess image for better comparison"""
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Optional: Apply slight blur to reduce noise
        # image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        return image
