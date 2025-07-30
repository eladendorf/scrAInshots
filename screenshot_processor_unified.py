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
from local_llm import LocalScreenshotProcessor

class UnifiedScreenshotProcessor:
    """Screenshot processor that can use either LMStudio API or local LLM"""
    
    def __init__(self, screenshots_dir: Optional[Path] = None):
        self.config_path = Path.home() / ".scrainshots" / "config.json"
        self.load_config()
        
        # Initialize appropriate processor based on config
        if self.config["runtime"] == "local":
            self.processor = LocalScreenshotProcessor(self.config["local_model"])
        else:
            # Use regular API processor
            from screenshot_processor import ScreenshotProcessor
            self.processor = ScreenshotProcessor(
                lm_studio_url=self.config["lmstudio_url"],
                model=self.config["lmstudio_model"]
            )
            
        if screenshots_dir:
            self.processor.screenshots_dir = Path(screenshots_dir)
            
    def load_config(self):
        """Load configuration"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "runtime": "lmstudio",
                "local_model": "gemma-2b",
                "lmstudio_url": "http://localhost:1234/v1",
                "lmstudio_model": "google/gemma-3-12b"
            }
            
    def process_screenshot(self, image_path: Path) -> Optional[Path]:
        """Process a single screenshot using configured runtime"""
        return self.processor.process_screenshot(image_path)
        
    def process_all_screenshots(self) -> List[Path]:
        """Process all screenshots using configured runtime"""
        return self.processor.process_all_screenshots()
        
    def get_runtime_info(self) -> Dict:
        """Get information about current runtime"""
        return {
            "runtime": self.config["runtime"],
            "model": self.config.get(f"{self.config['runtime']}_model", "unknown"),
            "screenshots_dir": str(self.processor.screenshots_dir)
        }

if __name__ == "__main__":
    # Test unified processor
    processor = UnifiedScreenshotProcessor()
    info = processor.get_runtime_info()
    print(f"Using runtime: {info['runtime']}")
    print(f"Model: {info['model']}")
    print(f"Screenshots directory: {info['screenshots_dir']}")