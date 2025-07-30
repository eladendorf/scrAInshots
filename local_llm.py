import os
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, List
import requests
from tqdm import tqdm
import shutil
from datetime import datetime
from screenshot_processor import ScreenshotProcessor

class LocalLLMManager:
    """Manages local LLM runtime using MLX for Mac"""
    
    def __init__(self):
        self.models_dir = Path.home() / ".scrainshots" / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.supported_models = {
            "gemma-2b": {
                "hf_repo": "google/gemma-2b",
                "mlx_repo": "mlx-community/gemma-2b-4bit",
                "size": "1.5GB",
                "description": "Lightweight model, good for basic tasks"
            },
            "phi-3-mini": {
                "hf_repo": "microsoft/Phi-3-mini-4k-instruct",
                "mlx_repo": "mlx-community/Phi-3-mini-4k-instruct-4bit",
                "size": "2.4GB",
                "description": "Small but capable model"
            },
            "mistral-7b": {
                "hf_repo": "mistralai/Mistral-7B-Instruct-v0.2",
                "mlx_repo": "mlx-community/Mistral-7B-Instruct-v0.2-4bit",
                "size": "4.1GB",
                "description": "Powerful open model, requires more RAM"
            }
        }
        self.current_model = None
        self.mlx_installed = False
        
    def check_mlx_installation(self) -> bool:
        """Check if MLX is installed"""
        try:
            import mlx
            import mlx_lm
            self.mlx_installed = True
            return True
        except ImportError:
            return False
            
    def install_mlx(self) -> bool:
        """Install MLX and MLX-LM"""
        print("Installing MLX for Apple Silicon...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "mlx", "mlx-lm"])
            self.mlx_installed = True
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install MLX: {e}")
            return False
            
    def download_model(self, model_name: str, progress_callback=None) -> bool:
        """Download a model from Hugging Face"""
        if model_name not in self.supported_models:
            print(f"Model {model_name} not supported")
            return False
            
        model_info = self.supported_models[model_name]
        model_path = self.models_dir / model_name
        
        if model_path.exists():
            print(f"Model {model_name} already downloaded")
            return True
            
        print(f"Downloading {model_name} from Hugging Face...")
        
        try:
            # Use mlx-lm to download and convert the model
            from mlx_lm import convert
            
            if progress_callback:
                progress_callback({"status": "downloading", "model": model_name, "progress": 0})
            
            # Download using mlx-lm utilities
            subprocess.check_call([
                sys.executable, "-m", "mlx_lm.convert",
                "--hf-path", model_info["mlx_repo"],
                "--mlx-path", str(model_path),
                "--quantize"
            ])
            
            if progress_callback:
                progress_callback({"status": "completed", "model": model_name, "progress": 100})
                
            return True
            
        except Exception as e:
            print(f"Failed to download model: {e}")
            if model_path.exists():
                shutil.rmtree(model_path)
            return False
            
    def list_downloaded_models(self) -> List[str]:
        """List all downloaded models"""
        models = []
        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir() and model_dir.name in self.supported_models:
                models.append(model_dir.name)
        return models
        
    def load_model(self, model_name: str):
        """Load a model for inference"""
        if not self.mlx_installed:
            if not self.check_mlx_installation():
                if not self.install_mlx():
                    raise RuntimeError("Failed to install MLX")
                    
        model_path = self.models_dir / model_name
        if not model_path.exists():
            raise ValueError(f"Model {model_name} not found. Please download it first.")
            
        try:
            from mlx_lm import load, generate
            self.model, self.tokenizer = load(str(model_path))
            self.current_model = model_name
            self.generate_fn = generate
            print(f"Loaded model: {model_name}")
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            return False
            
    def generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Generate text using the loaded model"""
        if not self.current_model:
            raise RuntimeError("No model loaded. Call load_model() first.")
            
        try:
            response = self.generate_fn(
                self.model,
                self.tokenizer,
                prompt=prompt,
                max_tokens=max_tokens,
                temp=temperature
            )
            return response
        except Exception as e:
            print(f"Generation error: {e}")
            return ""
            
    def process_image_with_text(self, image_path: Path, prompt: str) -> Dict:
        """Process an image with text prompt (note: most models don't support vision)"""
        # For now, we'll extract text from image metadata and use text-only processing
        # In the future, we could use vision models like LLaVA when available for MLX
        
        image_context = f"""
Image file: {image_path.name}
Image type: Screenshot
Task: Analyze and describe the content based on the following prompt:

{prompt}

Please provide a detailed analysis.
"""
        
        response = self.generate(image_context, max_tokens=1500)
        
        return {
            "content": response,
            "model": self.current_model,
            "timestamp": datetime.now().isoformat()
        }

class LocalScreenshotProcessor(ScreenshotProcessor):
    """Screenshot processor that uses local LLM instead of API"""
    
    def __init__(self, model_name: str = "gemma-2b"):
        super().__init__()
        self.llm_manager = LocalLLMManager()
        self.model_name = model_name
        self._ensure_model_ready()
        
    def _ensure_model_ready(self):
        """Ensure the model is downloaded and loaded"""
        if self.model_name not in self.llm_manager.list_downloaded_models():
            print(f"Downloading {self.model_name}...")
            if not self.llm_manager.download_model(self.model_name):
                raise RuntimeError(f"Failed to download {self.model_name}")
                
        if not self.llm_manager.load_model(self.model_name):
            raise RuntimeError(f"Failed to load {self.model_name}")
            
    def process_with_llm(self, image_path: Path, metadata: Dict) -> Dict:
        """Process image with local LLM"""
        prompt = f"""Analyze this screenshot and provide a comprehensive markdown report with the following sections:

1. **Text Content**: Extract ALL visible text from the image
2. **Description**: Detailed description of what the image shows
3. **Categorization**: Categorize the content (e.g., website, app, document, code, chat, etc.)
4. **Summary**: Brief summary of the main content and purpose
5. **Key Elements**: List important UI elements, buttons, or features visible
6. **Context Clues**: Any URLs, app names, or identifying information

Device type hint: {metadata.get('probable_device', 'unknown')}
Screenshot dimensions: {metadata.get('dimensions', 'unknown')}
Filename: {image_path.name}

Please be thorough and extract as much information as possible."""

        try:
            response = self.llm_manager.generate(prompt, max_tokens=2000)
            return {
                "content": response,
                "model": f"local:{self.model_name}",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error processing with local LLM: {e}")
            return None

if __name__ == "__main__":
    # Test local LLM manager
    manager = LocalLLMManager()
    
    print("Checking MLX installation...")
    if not manager.check_mlx_installation():
        print("MLX not found. Installing...")
        manager.install_mlx()
        
    print("\nAvailable models:")
    for name, info in manager.supported_models.items():
        print(f"- {name}: {info['description']} ({info['size']})")
        
    print("\nDownloaded models:")
    downloaded = manager.list_downloaded_models()
    if downloaded:
        for model in downloaded:
            print(f"- {model}")
    else:
        print("No models downloaded yet")
        
    # Test download
    if not downloaded:
        print("\nDownloading gemma-2b for testing...")
        if manager.download_model("gemma-2b"):
            print("Download successful!")
            
            # Test generation
            print("\nTesting generation...")
            manager.load_model("gemma-2b")
            response = manager.generate("Hello, this is a test. Please respond briefly.")
            print(f"Response: {response}")