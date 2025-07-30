#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path
from local_llm import LocalLLMManager
import threading
import time

class LLMAPIServer:
    def __init__(self):
        self.config_path = Path.home() / ".scrainshots" / "config.json"
        self.config_path.parent.mkdir(exist_ok=True)
        self.load_config()
        self.llm_manager = LocalLLMManager()
        
    def load_config(self):
        """Load configuration"""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {
                "runtime": "lmstudio",  # "lmstudio" or "local"
                "local_model": "gemma-2b",
                "lmstudio_url": "http://localhost:1234/v1",
                "lmstudio_model": "google/gemma-3-12b"
            }
            self.save_config()
            
    def save_config(self):
        """Save configuration"""
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def download_model(self, model_name: str):
        """Download a model with progress tracking"""
        progress_data = {"status": "starting", "model": model_name, "progress": 0}
        
        def progress_callback(data):
            nonlocal progress_data
            progress_data = data
            
        # Start download in background
        success = self.llm_manager.download_model(model_name, progress_callback)
        
        print(json.dumps({
            "success": success,
            "model": model_name,
            "path": str(self.llm_manager.models_dir / model_name) if success else None
        }))
        
    def set_runtime(self, runtime: str, model: str = None):
        """Set the LLM runtime preference"""
        self.config["runtime"] = runtime
        
        if runtime == "local" and model:
            self.config["local_model"] = model
        elif runtime == "lmstudio" and model:
            self.config["lmstudio_model"] = model
            
        self.save_config()
        
        # Update the screenshot processor to use the new runtime
        processor_config = {
            "runtime": runtime,
            "config": self.config
        }
        
        print(json.dumps({
            "success": True,
            "runtime": runtime,
            "config": self.config
        }))
        
    def get_download_progress(self, model_name: str):
        """Get download progress for a model"""
        model_path = self.llm_manager.models_dir / model_name
        
        if model_path.exists():
            print(json.dumps({
                "status": "completed",
                "model": model_name,
                "progress": 100
            }))
        else:
            # Check if download is in progress
            temp_path = model_path.with_suffix('.downloading')
            if temp_path.exists():
                # Estimate progress based on file size
                print(json.dumps({
                    "status": "downloading",
                    "model": model_name,
                    "progress": 50  # Placeholder
                }))
            else:
                print(json.dumps({
                    "status": "not_started",
                    "model": model_name,
                    "progress": 0
                }))

if __name__ == "__main__":
    server = LLMAPIServer()
    
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "download-model" and len(sys.argv) >= 3:
        server.download_model(sys.argv[2])
    elif command == "set-runtime" and len(sys.argv) >= 3:
        model = sys.argv[3] if len(sys.argv) >= 4 else None
        server.set_runtime(sys.argv[2], model)
    elif command == "get-progress" and len(sys.argv) >= 3:
        server.get_download_progress(sys.argv[2])
    else:
        print(json.dumps({"error": f"Invalid command: {command}"}))
        sys.exit(1)