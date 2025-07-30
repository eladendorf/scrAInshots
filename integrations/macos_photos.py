"""
MacOS Photos app integration for accessing screenshots
"""
import os
import subprocess
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import tempfile
import shutil

logger = logging.getLogger(__name__)


class MacOSPhotosIntegration:
    """Integration for MacOS Photos app to access screenshots album"""
    
    def __init__(self):
        self.check_platform()
        self.photos_library_path = self._find_photos_library()
        
    def check_platform(self):
        """Check if running on macOS"""
        import platform
        if platform.system() != 'Darwin':
            raise Exception("MacOS Photos integration only works on macOS")
    
    def _find_photos_library(self) -> Optional[Path]:
        """Find the Photos library path"""
        # Default location
        default_path = Path.home() / 'Pictures' / 'Photos Library.photoslibrary'
        if default_path.exists():
            return default_path
        
        # Try to find it via AppleScript
        script = '''
        tell application "System Events"
            tell application "Photos"
                return POSIX path of (get properties)
            end tell
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout:
                # Parse the path from the output
                return Path(result.stdout.strip())
        except:
            pass
        
        return None
    
    def get_screenshots_album_photos(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get photos from the Screenshots album using AppleScript"""
        
        # AppleScript to get screenshots
        script = f'''
        tell application "Photos"
            set screenshotPhotos to {{}}
            set maxPhotos to {limit}
            set photoCount to 0
            
            -- Try to find Screenshots album
            try
                set screenshotAlbum to album "Screenshots"
            on error
                -- Try alternate names
                try
                    set screenshotAlbum to album "Screen Shots"
                on error
                    try
                        set screenshotAlbum to album "Screen Captures"
                    on error
                        return "No Screenshots album found"
                    end try
                end try
            end try
            
            -- Get photos from the album
            set albumPhotos to media items of screenshotAlbum
            
            repeat with aPhoto in albumPhotos
                if photoCount ≥ maxPhotos then exit repeat
                
                try
                    set photoInfo to {{}}
                    set photoInfo to photoInfo & (id of aPhoto as string)
                    set photoInfo to photoInfo & (filename of aPhoto as string)
                    set photoInfo to photoInfo & (date of aPhoto as string)
                    set photoInfo to photoInfo & (altitude of aPhoto as string)
                    set photoInfo to photoInfo & (location of aPhoto as string)
                    
                    -- Get dimensions if available
                    try
                        set photoInfo to photoInfo & ((width of aPhoto as string) & "x" & (height of aPhoto as string))
                    on error
                        set photoInfo to photoInfo & "unknown"
                    end try
                    
                    set screenshotPhotos to screenshotPhotos & {{photoInfo}}
                    set photoCount to photoCount + 1
                    
                on error errMsg
                    -- Skip photos that cause errors
                end try
            end repeat
            
            return screenshotPhotos
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"AppleScript error: {result.stderr}")
                return []
            
            # Parse the result
            output = result.stdout.strip()
            if output == "No Screenshots album found":
                logger.warning("No Screenshots album found in Photos")
                return []
            
            # Parse the AppleScript list output
            photos = self._parse_applescript_list(output)
            return photos
            
        except subprocess.TimeoutExpired:
            logger.error("Timeout while accessing Photos app")
            return []
        except Exception as e:
            logger.error(f"Error accessing Photos app: {e}")
            return []
    
    def _parse_applescript_list(self, applescript_output: str) -> List[Dict[str, Any]]:
        """Parse AppleScript list output into Python data structures"""
        photos = []
        
        # AppleScript returns nested lists like: {{id, filename, date, ...}, {...}, ...}
        # Remove outer braces and split by }, {
        output = applescript_output.strip()
        if output.startswith('{') and output.endswith('}'):
            output = output[1:-1]
        
        # Split into individual photo records
        photo_strings = output.split('}, {')
        
        for photo_str in photo_strings:
            photo_str = photo_str.strip('{}')
            if not photo_str:
                continue
                
            # Split the fields
            fields = [f.strip() for f in photo_str.split(',')]
            
            if len(fields) >= 6:
                try:
                    photo_data = {
                        'id': fields[0].strip('"'),
                        'filename': fields[1].strip('"'),
                        'date': fields[2].strip('"'),
                        'altitude': fields[3].strip('"'),
                        'location': fields[4].strip('"'),
                        'dimensions': fields[5].strip('"') if len(fields) > 5 else 'unknown'
                    }
                    
                    # Parse date
                    try:
                        # AppleScript date format: "Monday, November 25, 2024 at 10:30:00 AM"
                        date_str = photo_data['date']
                        # Remove day name and "at"
                        date_parts = date_str.split(', ', 1)[1].replace(' at ', ' ')
                        photo_data['datetime'] = datetime.strptime(date_parts, '%B %d, %Y %I:%M:%S %p')
                    except:
                        photo_data['datetime'] = datetime.now()
                    
                    photos.append(photo_data)
                    
                except Exception as e:
                    logger.error(f"Error parsing photo data: {e}")
                    continue
        
        return photos
    
    def export_photo(self, photo_id: str, output_path: Path) -> bool:
        """Export a specific photo from Photos to a file"""
        
        script = f'''
        tell application "Photos"
            set targetPhoto to media item id "{photo_id}"
            set exportFolder to POSIX file "{output_path.parent}"
            
            export {{targetPhoto}} to exportFolder with using originals
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Error exporting photo {photo_id}: {e}")
            return False
    
    def export_screenshots_batch(self, photos: List[Dict[str, Any]], 
                               output_dir: Path, 
                               max_export: int = 50) -> List[Path]:
        """Export multiple screenshots from Photos"""
        output_dir.mkdir(parents=True, exist_ok=True)
        exported_files = []
        
        # Create temporary directory for exports
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # AppleScript to export multiple photos at once
            photo_ids = [p['id'] for p in photos[:max_export]]
            photo_id_list = ', '.join([f'media item id "{pid}"' for pid in photo_ids])
            
            script = f'''
            tell application "Photos"
                set photosToExport to {{{photo_id_list}}}
                set exportFolder to POSIX file "{temp_path}"
                
                export photosToExport to exportFolder with using originals
            end tell
            '''
            
            try:
                logger.info(f"Exporting {len(photo_ids)} photos from Photos app...")
                result = subprocess.run(
                    ['osascript', '-e', script],
                    capture_output=True,
                    text=True,
                    timeout=60  # Give it more time for batch export
                )
                
                if result.returncode == 0:
                    # Move exported files to output directory
                    for photo in photos[:max_export]:
                        # Look for the exported file
                        possible_names = [
                            photo['filename'],
                            photo['filename'].replace(' ', '_'),
                            f"{photo['id']}.png",
                            f"{photo['id']}.jpg"
                        ]
                        
                        for name in possible_names:
                            temp_file = temp_path / name
                            if temp_file.exists():
                                # Create output filename with date
                                date_str = photo['datetime'].strftime('%Y-%m-%d_%H-%M-%S')
                                output_name = f"{date_str}_{photo['filename']}"
                                output_file = output_dir / output_name
                                
                                shutil.move(str(temp_file), str(output_file))
                                exported_files.append(output_file)
                                
                                # Store metadata
                                metadata = {
                                    'photo_id': photo['id'],
                                    'original_filename': photo['filename'],
                                    'date': photo['datetime'].isoformat(),
                                    'dimensions': photo['dimensions'],
                                    'source': 'photos_app'
                                }
                                
                                metadata_file = output_file.with_suffix('.json')
                                with open(metadata_file, 'w') as f:
                                    json.dump(metadata, f, indent=2)
                                
                                break
                
            except subprocess.TimeoutExpired:
                logger.error("Timeout during batch export")
            except Exception as e:
                logger.error(f"Error during batch export: {e}")
        
        logger.info(f"Successfully exported {len(exported_files)} photos")
        return exported_files
    
    def get_recent_screenshots(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get screenshots from the last N days"""
        all_screenshots = self.get_screenshots_album_photos(limit=500)
        
        # Filter by date
        cutoff_date = datetime.now() - timedelta(days=days)
        recent = []
        
        for photo in all_screenshots:
            if photo.get('datetime') and photo['datetime'] > cutoff_date:
                recent.append(photo)
        
        return sorted(recent, key=lambda x: x['datetime'], reverse=True)
    
    def scan_and_process_screenshots(self, processor, output_dir: Path, 
                                   days: int = 30, limit: int = 50) -> Dict[str, Any]:
        """Scan Photos screenshots and process them"""
        logger.info(f"Scanning Photos app for screenshots from last {days} days...")
        
        # Get recent screenshots
        screenshots = self.get_recent_screenshots(days)
        logger.info(f"Found {len(screenshots)} screenshots in Photos")
        
        if not screenshots:
            return {'processed': 0, 'errors': 0, 'skipped': 0}
        
        # Export screenshots
        exported_files = self.export_screenshots_batch(
            screenshots, 
            output_dir / 'photos_screenshots',
            max_export=limit
        )
        
        # Process exported screenshots
        results = {
            'processed': 0,
            'errors': 0,
            'skipped': 0,
            'screenshots': []
        }
        
        for file_path in exported_files:
            try:
                # Load metadata
                metadata_file = file_path.with_suffix('.json')
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                else:
                    metadata = {}
                
                # Process the screenshot
                result = processor.process_screenshot(str(file_path))
                
                if result:
                    # Add Photos-specific metadata
                    result['metadata']['photos_id'] = metadata.get('photo_id')
                    result['metadata']['photos_date'] = metadata.get('date')
                    
                    results['screenshots'].append(result)
                    results['processed'] += 1
                else:
                    results['errors'] += 1
                    
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results['errors'] += 1
        
        return results


class PhotosScreenshotWatcher:
    """Watch for new screenshots in Photos app and process them automatically"""
    
    def __init__(self, photos_integration: MacOSPhotosIntegration, 
                 processor, check_interval: int = 300):
        self.photos = photos_integration
        self.processor = processor
        self.check_interval = check_interval  # seconds
        self.processed_ids = set()
        self._load_processed_ids()
    
    def _load_processed_ids(self):
        """Load previously processed photo IDs"""
        cache_file = Path.home() / '.scrainshots' / 'photos_processed.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    self.processed_ids = set(data.get('processed_ids', []))
            except:
                pass
    
    def _save_processed_ids(self):
        """Save processed photo IDs"""
        cache_file = Path.home() / '.scrainshots' / 'photos_processed.json'
        cache_file.parent.mkdir(exist_ok=True)
        
        with open(cache_file, 'w') as f:
            json.dump({'processed_ids': list(self.processed_ids)}, f)
    
    def check_for_new_screenshots(self) -> List[Dict[str, Any]]:
        """Check for new screenshots in Photos"""
        # Get recent screenshots
        recent = self.photos.get_recent_screenshots(days=1)
        
        # Filter out already processed
        new_screenshots = []
        for photo in recent:
            if photo['id'] not in self.processed_ids:
                new_screenshots.append(photo)
        
        return new_screenshots
    
    def process_new_screenshots(self, output_dir: Path) -> Dict[str, Any]:
        """Process any new screenshots found"""
        new_screenshots = self.check_for_new_screenshots()
        
        if not new_screenshots:
            return {'processed': 0, 'new_screenshots': 0}
        
        logger.info(f"Found {len(new_screenshots)} new screenshots in Photos")
        
        # Export and process
        exported = self.photos.export_screenshots_batch(
            new_screenshots,
            output_dir / 'photos_screenshots' / 'auto',
            max_export=10  # Limit per check
        )
        
        processed = 0
        for file_path in exported:
            try:
                result = self.processor.process_screenshot(str(file_path))
                if result:
                    processed += 1
                    
                    # Mark as processed
                    for photo in new_screenshots:
                        if photo['filename'] in str(file_path):
                            self.processed_ids.add(photo['id'])
                            break
                            
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        # Save processed IDs
        self._save_processed_ids()
        
        return {
            'processed': processed,
            'new_screenshots': len(new_screenshots)
        }