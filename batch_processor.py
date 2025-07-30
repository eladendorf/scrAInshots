import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
from tqdm import tqdm
from screenshot_processor import ScreenshotProcessor
from database_manager import ScreenshotDatabase
import threading
import queue

class BatchProcessor:
    def __init__(self, screenshots_dir: Optional[Path] = None):
        self.processor = ScreenshotProcessor()
        if screenshots_dir:
            self.processor.screenshots_dir = Path(screenshots_dir)
        self.db = ScreenshotDatabase()
        self.progress_queue = queue.Queue()
        self.is_processing = False
        
    def get_unprocessed_screenshots(self) -> List[Path]:
        """Get list of screenshots that haven't been processed yet"""
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        all_screenshots = []
        
        for image_path in self.processor.screenshots_dir.iterdir():
            if image_path.suffix.lower() in image_extensions:
                all_screenshots.append(image_path)
                
        # Check which ones are already in database
        existing_files = set()
        all_docs = self.db.get_all()
        for doc in all_docs:
            if 'filename' in doc['metadata']:
                existing_files.add(doc['metadata']['filename'])
                
        # Return only unprocessed files
        unprocessed = [p for p in all_screenshots if p.name not in existing_files]
        return unprocessed
    
    def process_batch(self, progress_callback: Optional[Callable] = None) -> Dict:
        """Process all unprocessed screenshots with progress tracking"""
        self.is_processing = True
        unprocessed = self.get_unprocessed_screenshots()
        total = len(unprocessed)
        processed = 0
        failed = 0
        results = []
        
        if progress_callback:
            progress_callback({
                'status': 'started',
                'total': total,
                'processed': 0,
                'failed': 0
            })
        
        for i, image_path in enumerate(tqdm(unprocessed, desc="Processing screenshots")):
            # Check if processing should stop
            if not self.is_processing:
                print("Processing stopped by user")
                break
                
            try:
                result = self.processor.process_screenshot(image_path)
                if result:
                    processed += 1
                    results.append(str(result))
                else:
                    failed += 1
            except Exception as e:
                print(f"Error processing {image_path}: {e}")
                failed += 1
            
            if progress_callback:
                progress_callback({
                    'status': 'processing',
                    'total': total,
                    'processed': processed,
                    'failed': failed,
                    'current': image_path.name,
                    'progress': (i + 1) / total * 100
                })
        
        self.is_processing = False
        
        final_status = {
            'status': 'completed',
            'total': total,
            'processed': processed,
            'failed': failed,
            'results': results
        }
        
        if progress_callback:
            progress_callback(final_status)
            
        return final_status
    
    def process_batch_async(self, progress_callback: Optional[Callable] = None):
        """Process batch in a separate thread"""
        thread = threading.Thread(
            target=self.process_batch,
            args=(progress_callback,)
        )
        thread.start()
        return thread
    
    def get_statistics(self) -> Dict:
        """Get statistics about processed screenshots"""
        all_docs = self.db.get_all()
        
        stats = {
            'total_processed': len(all_docs),
            'by_device': {},
            'by_date': {},
            'total_size': 0
        }
        
        for doc in all_docs:
            metadata = doc['metadata']
            
            # Device type stats
            device = metadata.get('device_type', 'unknown')
            stats['by_device'][device] = stats['by_device'].get(device, 0) + 1
            
            # Date stats
            created_date = metadata.get('created_time', '')[:10]
            if created_date:
                stats['by_date'][created_date] = stats['by_date'].get(created_date, 0) + 1
                
            # Size stats
            try:
                size = int(metadata.get('file_size', 0))
                stats['total_size'] += size
            except:
                pass
                
        return stats

if __name__ == "__main__":
    # Test batch processing
    def progress_handler(status):
        print(json.dumps(status))
    
    processor = BatchProcessor()
    stats = processor.get_statistics()
    print("Current statistics:", json.dumps(stats, indent=2))
    
    # Process unprocessed screenshots
    processor.process_batch(progress_handler)