import json
import os
from datetime import datetime
import hashlib
from pathlib import Path
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ResultManager:
    def __init__(self, results_dir="test_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.screenshots_dir = self.results_dir / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)
    
    def save_result(self, test_id: str, result: Dict[str, Any]) -> bool:
        """Save a single test result"""
        try:
            # Create test-specific directory
            test_dir = self.results_dir / test_id
            test_dir.mkdir(exist_ok=True)
            
            # Save screenshots
            screenshot_paths = self._save_screenshots(test_dir, result)
            
            # Create result metadata (without binary data) - ensure JSON serializable
            result_metadata = {
                'test_name': str(result['test_name']),
                'browser': str(result['browser']),
                'device': str(result['device']),
                'staging_url': str(result['staging_url']),
                'production_url': str(result['production_url']),
                'similarity_score': float(result['similarity_score']),
                'is_match': bool(result['is_match']),
                'timestamp': str(result['timestamp']),
                'screenshot_paths': screenshot_paths
            }
            
            # Save metadata to JSON
            result_file = test_dir / f"{self._generate_result_filename(result)}.json"
            with open(result_file, 'w') as f:
                json.dump(result_metadata, f, indent=2)
            
            logger.info(f"Saved result for {result['test_name']} - {result['browser']} ({result['device']})")
            return True
            
        except Exception as e:
            logger.error(f"Error saving result: {e}")
            return False
    
    def _save_screenshots(self, test_dir: Path, result: Dict[str, Any]) -> Dict[str, str]:
        """Save screenshots and return their paths"""
        screenshot_paths = {}
        
        try:
            # Generate filename base
            filename_base = self._generate_result_filename(result)
            
            # Save staging screenshot
            if result.get('staging_screenshot'):
                staging_path = test_dir / f"{filename_base}_staging.png"
                result['staging_screenshot'].save(staging_path)
                screenshot_paths['staging'] = str(staging_path.relative_to(self.results_dir))
            
            # Save production screenshot
            if result.get('production_screenshot'):
                production_path = test_dir / f"{filename_base}_production.png"
                result['production_screenshot'].save(production_path)
                screenshot_paths['production'] = str(production_path.relative_to(self.results_dir))
            
            # Save diff image if available
            if result.get('diff_image'):
                diff_path = test_dir / f"{filename_base}_diff.png"
                result['diff_image'].save(diff_path)
                screenshot_paths['diff'] = str(diff_path.relative_to(self.results_dir))
            
        except Exception as e:
            logger.error(f"Error saving screenshots: {e}")
        
        return screenshot_paths
    
    def _generate_result_filename(self, result: Dict[str, Any]) -> str:
        """Generate a unique filename for a test result"""
        # Create a string that uniquely identifies this test
        identifier = f"{result['test_name']}_{result['browser']}_{result['device']}_{result['timestamp']}"
        
        # Clean the identifier for use as filename
        safe_identifier = "".join(c for c in identifier if c.isalnum() or c in ('_', '-')).rstrip()
        
        return safe_identifier[:100]  # Limit length
    
    def load_test_results(self, test_id: str) -> List[Dict[str, Any]]:
        """Load all results for a specific test run"""
        try:
            test_dir = self.results_dir / test_id
            if not test_dir.exists():
                logger.warning(f"Test directory {test_id} not found")
                return []
            
            results = []
            for json_file in test_dir.glob("*.json"):
                try:
                    with open(json_file, 'r') as f:
                        result = json.load(f)
                        results.append(result)
                except Exception as e:
                    logger.error(f"Error loading result from {json_file}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error loading test results for {test_id}: {e}")
            return []
    
    def list_test_runs(self) -> List[Dict[str, Any]]:
        """List all available test runs"""
        try:
            test_runs = []
            
            for test_dir in self.results_dir.iterdir():
                if test_dir.is_dir() and test_dir.name != "screenshots":
                    # Count results in this test run
                    result_count = len(list(test_dir.glob("*.json")))
                    
                    if result_count > 0:
                        # Get the most recent result timestamp
                        try:
                            latest_result = None
                            latest_time = None
                            
                            for json_file in test_dir.glob("*.json"):
                                with open(json_file, 'r') as f:
                                    result = json.load(f)
                                    result_time = datetime.fromisoformat(result['timestamp'])
                                    
                                    if latest_time is None or result_time > latest_time:
                                        latest_time = result_time
                                        latest_result = result
                            
                            test_runs.append({
                                'test_id': test_dir.name,
                                'result_count': result_count,
                                'latest_timestamp': latest_time.isoformat() if latest_time else None,
                                'created': test_dir.stat().st_ctime
                            })
                            
                        except Exception as e:
                            logger.error(f"Error processing test run {test_dir.name}: {e}")
            
            # Sort by creation time (newest first)
            test_runs.sort(key=lambda x: x['created'], reverse=True)
            return test_runs
            
        except Exception as e:
            logger.error(f"Error listing test runs: {e}")
            return []
    
    def delete_test_run(self, test_id: str) -> bool:
        """Delete a complete test run"""
        try:
            test_dir = self.results_dir / test_id
            if test_dir.exists():
                import shutil
                shutil.rmtree(test_dir)
                logger.info(f"Deleted test run {test_id}")
                return True
            else:
                logger.warning(f"Test run {test_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting test run {test_id}: {e}")
            return False
    
    def get_summary_stats(self, test_id: str) -> Dict[str, Any]:
        """Get summary statistics for a test run"""
        try:
            results = self.load_test_results(test_id)
            
            if not results:
                return {}
            
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r.get('is_match', False))
            failed_tests = total_tests - passed_tests
            
            # Calculate average similarity score
            scores = [r.get('similarity_score', 0) for r in results]
            avg_similarity = sum(scores) / len(scores) if scores else 0
            
            # Group by browser and device
            browsers = {}
            devices = {}
            
            for result in results:
                browser = result.get('browser', 'Unknown')
                device = result.get('device', 'Unknown')
                
                if browser not in browsers:
                    browsers[browser] = {'total': 0, 'passed': 0}
                browsers[browser]['total'] += 1
                if result.get('is_match', False):
                    browsers[browser]['passed'] += 1
                
                if device not in devices:
                    devices[device] = {'total': 0, 'passed': 0}
                devices[device]['total'] += 1
                if result.get('is_match', False):
                    devices[device]['passed'] += 1
            
            return {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'average_similarity': avg_similarity,
                'browsers': browsers,
                'devices': devices,
                'timestamp': results[0].get('timestamp') if results else None
            }
            
        except Exception as e:
            logger.error(f"Error calculating summary stats: {e}")
            return {}
    
    def cleanup_old_results(self, days_to_keep: int = 30) -> int:
        """Clean up results older than specified days"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            cleaned_count = 0
            
            for test_dir in self.results_dir.iterdir():
                if test_dir.is_dir() and test_dir.stat().st_ctime < cutoff_time:
                    import shutil
                    shutil.rmtree(test_dir)
                    cleaned_count += 1
                    logger.info(f"Cleaned up old test run: {test_dir.name}")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0
