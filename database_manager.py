import chromadb
from chromadb.config import Settings
from pathlib import Path
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

class ScreenshotDatabase:
    def __init__(self, db_path="./screenshot_db"):
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="screenshots",
            metadata={"description": "Screenshot analysis data"}
        )
        
    def add_screenshot(self, md_path: Path, metadata: Dict, content: str):
        """Add a screenshot analysis to the database"""
        doc_id = hashlib.md5(md_path.name.encode()).hexdigest()
        
        # Prepare metadata for ChromaDB
        chroma_metadata = {
            "filename": metadata.get("filename", ""),
            "created_time": metadata.get("created_time", ""),
            "modified_time": metadata.get("modified_time", ""),
            "dimensions": metadata.get("dimensions", ""),
            "device_type": metadata.get("probable_device", "unknown"),
            "file_size": str(metadata.get("file_size", 0)),
            "md_path": str(md_path),
            "original_path": str(metadata.get("original_path", "")),
            "timestamp": datetime.now().isoformat()
        }
        
        self.collection.add(
            documents=[content],
            metadatas=[chroma_metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def search(self, query: str, n_results: int = 10) -> List[Dict]:
        """Search screenshots by content"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        formatted_results = []
        for i in range(len(results['ids'][0])):
            formatted_results.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None
            })
            
        return formatted_results
    
    def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get screenshots within a date range"""
        all_data = self.collection.get()
        
        filtered_results = []
        for i in range(len(all_data['ids'])):
            metadata = all_data['metadatas'][i]
            created_time = metadata.get('created_time', '')
            
            if start_date <= created_time <= end_date:
                filtered_results.append({
                    "id": all_data['ids'][i],
                    "content": all_data['documents'][i],
                    "metadata": metadata
                })
                
        return filtered_results
    
    def get_all(self) -> List[Dict]:
        """Get all screenshots from the database"""
        all_data = self.collection.get()
        
        results = []
        for i in range(len(all_data['ids'])):
            results.append({
                "id": all_data['ids'][i],
                "content": all_data['documents'][i],
                "metadata": all_data['metadatas'][i]
            })
            
        return results
    
    def update_content(self, doc_id: str, new_content: str):
        """Update the content of a screenshot analysis"""
        self.collection.update(
            ids=[doc_id],
            documents=[new_content]
        )
    
    def delete(self, doc_id: str):
        """Delete a screenshot from the database"""
        self.collection.delete(ids=[doc_id])
    
    def get_by_id(self, doc_id: str) -> Optional[Dict]:
        """Get a specific screenshot by ID"""
        result = self.collection.get(ids=[doc_id])
        
        if result['ids']:
            return {
                "id": result['ids'][0],
                "content": result['documents'][0],
                "metadata": result['metadatas'][0]
            }
        return None