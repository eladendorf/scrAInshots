import os
import json
import base64
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import requests
from PIL import Image
from PIL.ExifTags import TAGS
import platform
import re
from database_manager import ScreenshotDatabase

class ScreenshotProcessor:
    def __init__(self, lm_studio_url="http://localhost:1234/v1", model="google/gemma-3-12b"):
        self.api_url = f"{lm_studio_url}/chat/completions"
        self.model = model
        self.screenshots_dir = Path("/Users/enrico/Desktop/screenshots")
        self.output_dir = Path("./processed_screenshots")
        self.output_dir.mkdir(exist_ok=True)
        self.db = ScreenshotDatabase()
        
    def encode_image(self, image_path: Path) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def extract_metadata(self, image_path: Path) -> Dict:
        """Extract metadata from image file"""
        metadata = {
            "filename": image_path.name,
            "file_size": os.path.getsize(image_path),
            "created_time": datetime.fromtimestamp(os.path.getctime(image_path)).isoformat(),
            "modified_time": datetime.fromtimestamp(os.path.getmtime(image_path)).isoformat(),
        }
        
        try:
            img = Image.open(image_path)
            metadata["dimensions"] = f"{img.width}x{img.height}"
            metadata["format"] = img.format
            
            # Try to extract EXIF data
            exifdata = img.getexif()
            if exifdata:
                for tag_id, value in exifdata.items():
                    tag = TAGS.get(tag_id, tag_id)
                    metadata[f"exif_{tag}"] = str(value)
                    
            # Guess device type based on resolution
            aspect_ratio = img.width / img.height
            if aspect_ratio < 0.6:  # Tall aspect ratio typical of phones
                metadata["probable_device"] = "phone"
            elif img.width >= 1920:  # High resolution typical of computers
                metadata["probable_device"] = "computer"
            else:
                metadata["probable_device"] = "unknown"
                
        except Exception as e:
            print(f"Error extracting image metadata: {e}")
            
        return metadata
    
    def process_with_llm(self, image_path: Path, metadata: Dict) -> Dict:
        """Process image with LLM to extract content and categorization"""
        base64_image = self.encode_image(image_path)
        
        prompt = f"""Analyze this screenshot and provide a comprehensive markdown report with the following sections:

1. **Text Content**: Extract ALL visible text from the image
2. **Description**: Detailed description of what the image shows
3. **Categorization**: Categorize the content (e.g., website, app, document, code, chat, etc.)
4. **Summary**: Brief summary of the main content and purpose
5. **Key Elements**: List important UI elements, buttons, or features visible
6. **Context Clues**: Any URLs, app names, or identifying information

Device type hint: {metadata.get('probable_device', 'unknown')}
Screenshot dimensions: {metadata.get('dimensions', 'unknown')}

Please be thorough and extract as much information as possible."""

        try:
            response = requests.post(
                self.api_url,
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                },
                timeout=60  # 60 second timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "content": result['choices'][0]['message']['content'],
                    "model": self.model,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] LLM API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] LLM request timed out after 60 seconds")
            return None
        except requests.exceptions.ConnectionError:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Cannot connect to LLM API at {self.api_url}")
            print("Make sure LM Studio is running and the server is started on port 1234")
            return None
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error processing with LLM: {e}")
            return None
    
    def create_markdown_file(self, image_path: Path, metadata: Dict, llm_result: Dict) -> Path:
        """Create markdown file with all extracted information"""
        # Generate unique ID for the screenshot
        file_hash = hashlib.md5(image_path.name.encode()).hexdigest()[:8]
        md_filename = f"{image_path.stem}_{file_hash}.md"
        md_path = self.output_dir / md_filename
        
        content = f"""# Screenshot Analysis: {image_path.name}

## Metadata
- **File**: {metadata['filename']}
- **Created**: {metadata['created_time']}
- **Modified**: {metadata['modified_time']}
- **Dimensions**: {metadata.get('dimensions', 'unknown')}
- **Format**: {metadata.get('format', 'unknown')}
- **Size**: {metadata['file_size']} bytes
- **Device Type**: {metadata.get('probable_device', 'unknown')}
- **Original Path**: {image_path}

## LLM Analysis
*Analyzed on {llm_result['timestamp']} using {llm_result['model']}*

{llm_result['content']}

## Additional Context
*This section will be populated with additional research and context*

---
**Screenshot Link**: [View Original]({image_path})
"""
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return md_path
    
    def process_screenshot(self, image_path: Path) -> Optional[Path]:
        """Process a single screenshot"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting processing: {image_path.name}")
        
        # Extract metadata
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Extracting metadata...")
        metadata = self.extract_metadata(image_path)
        metadata["original_path"] = str(image_path)
        
        # Process with LLM
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Sending to LLM for analysis...")
        llm_result = self.process_with_llm(image_path, metadata)
        
        if llm_result:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] LLM analysis complete, creating markdown...")
            # Create markdown file
            md_path = self.create_markdown_file(image_path, metadata, llm_result)
            
            # Add to database
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            doc_id = self.db.add_screenshot(md_path, metadata, md_content)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Completed: {image_path.name} -> {md_path.name} (ID: {doc_id})")
            return md_path
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✗ Failed to process: {image_path.name}")
            return None
    
    def process_all_screenshots(self) -> List[Path]:
        """Process all screenshots in the directory"""
        processed_files = []
        image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        
        for image_path in self.screenshots_dir.iterdir():
            if image_path.suffix.lower() in image_extensions:
                result = self.process_screenshot(image_path)
                if result:
                    processed_files.append(result)
                    
        return processed_files

if __name__ == "__main__":
    processor = ScreenshotProcessor()
    
    # Test with a single screenshot first
    screenshots = list(processor.screenshots_dir.glob("*.png"))[:1]
    
    if screenshots:
        print(f"Testing with: {screenshots[0]}")
        processor.process_screenshot(screenshots[0])
    else:
        print("No screenshots found in the directory")