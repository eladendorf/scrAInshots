#!/usr/bin/env python3
import sys
import json
from pathlib import Path
from screenshot_processor import ScreenshotProcessor
from database_manager import ScreenshotDatabase
from batch_processor import BatchProcessor
import requests
from datetime import datetime
import threading
import uuid

class APIServer:
    def __init__(self):
        self.db = ScreenshotDatabase()
        self.processor = ScreenshotProcessor()
        self.batch_processor = BatchProcessor()
        self.processing_thread = None
        self.processing_status = {
            "is_running": False,
            "job_id": None,
            "progress": 0,
            "total": 0,
            "processed": 0,
            "failed": 0,
            "current_file": None,
            "status": "idle",
            "start_time": None
        }
        
    def get_all(self):
        """Get all screenshots from database"""
        results = self.db.get_all()
        print(json.dumps(results))
        
    def search(self, query):
        """Search screenshots by query"""
        results = self.db.search(query)
        print(json.dumps(results))
        
    def get_by_date(self, start_date, end_date):
        """Get screenshots by date range"""
        results = self.db.get_by_date_range(start_date, end_date)
        print(json.dumps(results))
        
    def process_all(self):
        """Process all screenshots in the directory"""
        processed = self.processor.process_all_screenshots()
        print(json.dumps({
            "processed": len(processed),
            "files": [str(p) for p in processed]
        }))
        
    def refine_content(self, doc_id, prompt):
        """Refine content with additional LLM analysis"""
        # Get existing content
        doc = self.db.get_by_id(doc_id)
        if not doc:
            print(json.dumps({"error": "Document not found"}))
            return
            
        # Create refinement prompt
        refinement_prompt = f"""
{prompt}

Current content:
{doc['content']}

Please provide a detailed analysis based on the above prompt. Include:
1. Company/Product information if applicable
2. Topic analysis and context
3. Related concepts and technologies
4. Any relevant insights or recommendations
"""
        
        try:
            response = requests.post(
                "http://localhost:1234/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": "google/gemma-3-12b",
                    "messages": [
                        {"role": "user", "content": refinement_prompt}
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                refined_content = result['choices'][0]['message']['content']
                
                # Update the markdown file
                md_path = Path(doc['metadata']['md_path'])
                if md_path.exists():
                    content = md_path.read_text()
                    # Find the Additional Context section and update it
                    context_marker = "## Additional Context"
                    if context_marker in content:
                        parts = content.split(context_marker)
                        new_content = f"{parts[0]}{context_marker}\n{refined_content}\n\n---\n**Screenshot Link**: [View Original]({doc['metadata']['original_path']})\n"
                        md_path.write_text(new_content)
                        
                        # Update database
                        self.db.update_content(doc_id, new_content)
                        
                print(json.dumps({"success": True, "refined": True}))
            else:
                print(json.dumps({"error": f"LLM error: {response.status_code}"}))
                
        except Exception as e:
            print(json.dumps({"error": str(e)}))
            
    def start_batch_processing(self):
        """Start batch processing in background"""
        if self.processing_status["is_running"]:
            return {"error": "Processing already running", "status": self.processing_status}
            
        def progress_callback(data):
            """Update progress status"""
            self.processing_status.update({
                "progress": data.get("progress", 0),
                "total": data.get("total", 0),
                "processed": data.get("processed", 0),
                "failed": data.get("failed", 0),
                "current_file": data.get("current", None),
                "status": data.get("status", "processing")
            })
            
            if data.get("status") == "completed":
                self.processing_status["is_running"] = False
                
        # Start processing
        self.processing_status.update({
            "is_running": True,
            "job_id": str(uuid.uuid4()),
            "status": "starting",
            "start_time": datetime.now().isoformat()
        })
        
        self.processing_thread = self.batch_processor.process_batch_async(progress_callback)
        
        return {
            "success": True,
            "job_id": self.processing_status["job_id"],
            "message": "Batch processing started"
        }
        
    def stop_batch_processing(self):
        """Stop batch processing"""
        if not self.processing_status["is_running"]:
            return {"error": "No processing running"}
            
        # Set flag to stop processing
        self.batch_processor.is_processing = False
        
        # Update status
        self.processing_status.update({
            "is_running": False,
            "status": "stopped",
            "start_time": None
        })
        
        return {"success": True, "message": "Batch processing stopped"}
        
    def get_processing_status(self):
        """Get current processing status"""
        # Add statistics
        stats = self.batch_processor.get_statistics()
        return {
            **self.processing_status,
            "statistics": stats
        }

def run_server():
    """Run a simple HTTP server for the API"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import urllib.parse
    
    class APIHandler(BaseHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.api_server = APIServer()
            super().__init__(*args, **kwargs)
            
        def do_GET(self):
            parsed_path = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_path.query)
            
            if parsed_path.path == '/health':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "ok"}).encode())
                
        def log_message(self, format, *args):
            # Suppress default logging
            pass
    
    print("Starting API server on http://localhost:8000")
    server = HTTPServer(('localhost', 8000), APIHandler)
    server.serve_forever()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "server":
        run_server()
    else:
        server = APIServer()
        
        if len(sys.argv) < 2:
            print(json.dumps({"error": "No command provided"}))
            sys.exit(1)
            
        command = sys.argv[1]
        
        if command == "get-all":
            server.get_all()
        elif command == "search" and len(sys.argv) >= 3:
            server.search(sys.argv[2])
        elif command == "get-by-date" and len(sys.argv) >= 4:
            server.get_by_date(sys.argv[2], sys.argv[3])
        elif command == "process-all":
            server.process_all()
        elif command == "refine" and len(sys.argv) >= 4:
            server.refine_content(sys.argv[2], sys.argv[3])
        else:
            print(json.dumps({"error": f"Invalid command: {command}"}))
            sys.exit(1)