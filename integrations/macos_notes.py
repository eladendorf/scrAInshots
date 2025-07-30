"""
MacOS Notes integration using macnotesapp
"""
import json
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path

from .data_models import UnifiedTimelineItem, DataSourceType, ConceptCategory

logger = logging.getLogger(__name__)


class MacOSNotesIntegration:
    """Integration for MacOS Notes app"""
    
    def __init__(self):
        self.check_dependencies()
    
    def check_dependencies(self):
        """Check if macnotesapp is installed"""
        try:
            result = subprocess.run(['which', 'notes'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("macnotesapp not found. Install with: pip install macnotesapp")
                raise ImportError("macnotesapp not installed")
        except Exception as e:
            logger.error(f"Error checking macnotesapp: {e}")
            raise
    
    def get_all_notes(self) -> List[Dict[str, Any]]:
        """Get all notes from MacOS Notes app"""
        try:
            # Use macnotesapp CLI to list all notes
            result = subprocess.run(
                ['notes', 'list', '--json'],
                capture_output=True,
                text=True,
                check=True
            )
            
            notes_data = json.loads(result.stdout)
            return notes_data
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running notes command: {e}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing notes JSON: {e}")
            return []
    
    def get_note_content(self, note_id: str) -> Optional[str]:
        """Get the full content of a specific note"""
        try:
            result = subprocess.run(
                ['notes', 'show', note_id, '--json'],
                capture_output=True,
                text=True,
                check=True
            )
            
            note_data = json.loads(result.stdout)
            return note_data.get('body', '')
            
        except Exception as e:
            logger.error(f"Error getting note content for {note_id}: {e}")
            return None
    
    def convert_to_timeline_items(self, notes: List[Dict[str, Any]]) -> List[UnifiedTimelineItem]:
        """Convert MacOS Notes to unified timeline items"""
        timeline_items = []
        
        for note in notes:
            try:
                # Get full note content
                content = self.get_note_content(note['id'])
                if not content:
                    content = note.get('body', '')
                
                # Parse dates
                created = datetime.fromisoformat(note['creation_date'].replace('Z', '+00:00'))
                modified = datetime.fromisoformat(note['modification_date'].replace('Z', '+00:00'))
                
                # Create unified item
                item = UnifiedTimelineItem(
                    id=f"note_{note['id']}",
                    source_type=DataSourceType.MACOS_NOTE,
                    title=note.get('name', 'Untitled Note'),
                    content=content,
                    timestamp=created,
                    last_modified=modified,
                    metadata={
                        'folder': note.get('folder', 'Notes'),
                        'account': note.get('account', 'iCloud'),
                        'has_attachments': note.get('attachment_count', 0) > 0,
                        'word_count': len(content.split()) if content else 0
                    },
                    extracted_concepts=[],  # Will be filled by concept extractor
                    concept_categories=[],  # Will be filled by categorizer
                    related_items=[],
                    source_id=note['id'],
                    source_metadata=note
                )
                
                timeline_items.append(item)
                
            except Exception as e:
                logger.error(f"Error converting note {note.get('id')}: {e}")
                continue
        
        return timeline_items
    
    def fetch_notes_in_timerange(self, start_date: datetime, end_date: datetime) -> List[UnifiedTimelineItem]:
        """Fetch notes modified within a specific time range"""
        all_notes = self.get_all_notes()
        
        # Filter notes by modification date
        filtered_notes = []
        for note in all_notes:
            try:
                modified = datetime.fromisoformat(note['modification_date'].replace('Z', '+00:00'))
                if start_date <= modified <= end_date:
                    filtered_notes.append(note)
            except Exception as e:
                logger.error(f"Error parsing date for note {note.get('id')}: {e}")
                continue
        
        return self.convert_to_timeline_items(filtered_notes)
    
    def search_notes(self, query: str) -> List[UnifiedTimelineItem]:
        """Search notes by content"""
        try:
            result = subprocess.run(
                ['notes', 'find', query, '--json'],
                capture_output=True,
                text=True,
                check=True
            )
            
            notes_data = json.loads(result.stdout)
            return self.convert_to_timeline_items(notes_data)
            
        except Exception as e:
            logger.error(f"Error searching notes: {e}")
            return []