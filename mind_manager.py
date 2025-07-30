"""
Mind Manager - Unified system for managing timeline data from multiple sources
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from integrations.data_models import UnifiedTimelineItem, ConceptCluster, TimeWindow, DataSourceType
from integrations.macos_notes import MacOSNotesIntegration
from integrations.outlook_integration import OutlookIntegration
from integrations.simple_email_integration import SimpleEmailIntegration
from integrations.fireflies_integration import FirefliesIntegration
from integrations.concept_extractor import ConceptExtractor
from database_manager import DatabaseManager
from screenshot_processor import ScreenshotProcessor
from config_manager import ConfigManager

logger = logging.getLogger(__name__)


class MindManager:
    """Central manager for all timeline data sources and analysis"""
    
    def __init__(self, config_path: str = None, use_config_manager: bool = True):
        self.use_config_manager = use_config_manager
        
        if use_config_manager:
            # Use ConfigManager for secure credential storage
            self.config_manager = ConfigManager()
            self.config = self._load_config_from_manager()
        else:
            # Use traditional config file
            self.config = self._load_config(config_path)
        
        # Initialize database
        self.db_manager = DatabaseManager()
        
        # Initialize integrations
        self.notes_integration = None
        self.outlook_integration = None
        self.simple_email_integration = None
        self.fireflies_integration = None
        self.screenshot_processor = ScreenshotProcessor()
        
        # Initialize concept extractor
        self.concept_extractor = ConceptExtractor()
        
        # Data cache
        self.timeline_items = []
        self.concept_clusters = []
        
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file or environment"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default config from environment
        return {
            'outlook': {
                'client_id': os.getenv('OUTLOOK_CLIENT_ID'),
                'client_secret': os.getenv('OUTLOOK_CLIENT_SECRET'),
                'tenant_id': os.getenv('OUTLOOK_TENANT_ID')
            },
            'fireflies': {
                'api_key': os.getenv('FIREFLIES_API_KEY')
            },
            'simple_email': {
                'address': os.getenv('EMAIL_ADDRESS'),
                'password': os.getenv('EMAIL_PASSWORD'),
                'provider': os.getenv('EMAIL_PROVIDER', 'gmail')
            },
            'screenshot_dir': os.getenv('SCREENSHOT_DIR', os.path.expanduser('~/Desktop/screenshots'))
        }
    
    def _load_config_from_manager(self) -> Dict[str, Any]:
        """Load configuration from ConfigManager"""
        config = self.config_manager.get_config()
        env_dict = self.config_manager.get_env_dict()
        
        # Apply environment variables
        for key, value in env_dict.items():
            os.environ[key] = value
        
        # Return formatted config
        return {
            'outlook': {
                'client_id': config.get('outlook_client_id', ''),
                'client_secret': config.get('outlook_client_secret', ''),
                'tenant_id': config.get('outlook_tenant_id', '')
            },
            'fireflies': {
                'api_key': config.get('fireflies_api_key', '')
            },
            'simple_email': {
                'address': config.get('email_address', ''),
                'password': config.get('email_password', ''),
                'provider': config.get('email_provider', 'gmail')
            },
            'screenshot_dir': config.get('screenshot_dir', os.path.expanduser('~/Desktop/screenshots'))
        }
    
    def initialize_integrations(self):
        """Initialize all available integrations"""
        
        # MacOS Notes
        try:
            self.notes_integration = MacOSNotesIntegration()
            logger.info("MacOS Notes integration initialized")
        except Exception as e:
            logger.warning(f"Could not initialize MacOS Notes: {e}")
        
        # Outlook
        if all(self.config['outlook'].values()):
            try:
                self.outlook_integration = OutlookIntegration(
                    client_id=self.config['outlook']['client_id'],
                    client_secret=self.config['outlook']['client_secret'],
                    tenant_id=self.config['outlook']['tenant_id']
                )
                logger.info("Outlook integration initialized")
            except Exception as e:
                logger.warning(f"Could not initialize Outlook: {e}")
        
        # Simple Email (Alternative to Outlook)
        if self.config['simple_email']['address'] and self.config['simple_email']['password']:
            try:
                self.simple_email_integration = SimpleEmailIntegration(
                    email_address=self.config['simple_email']['address'],
                    password=self.config['simple_email']['password'],
                    provider=self.config['simple_email']['provider']
                )
                logger.info("Simple email integration initialized")
            except Exception as e:
                logger.warning(f"Could not initialize simple email: {e}")
        
        # Fireflies
        if self.config['fireflies']['api_key']:
            try:
                self.fireflies_integration = FirefliesIntegration(
                    api_key=self.config['fireflies']['api_key']
                )
                logger.info("Fireflies integration initialized")
            except Exception as e:
                logger.warning(f"Could not initialize Fireflies: {e}")
    
    def fetch_all_data(self, start_date: datetime, end_date: datetime) -> List[UnifiedTimelineItem]:
        """Fetch data from all sources for the given date range"""
        all_items = []
        
        # Fetch screenshots
        logger.info("Fetching screenshots...")
        screenshots = self._fetch_screenshots(start_date, end_date)
        all_items.extend(screenshots)
        logger.info(f"Found {len(screenshots)} screenshots")
        
        # Fetch MacOS Notes
        if self.notes_integration:
            logger.info("Fetching MacOS Notes...")
            notes = self.notes_integration.fetch_notes_in_timerange(start_date, end_date)
            all_items.extend(notes)
            logger.info(f"Found {len(notes)} notes")
        
        # Fetch Outlook emails
        if self.outlook_integration:
            logger.info("Fetching Outlook emails...")
            try:
                # Get received emails
                emails = self.outlook_integration.get_emails(start_date, end_date, filter_fireflies=False)
                email_items = self.outlook_integration.convert_to_timeline_items(emails, 'received')
                all_items.extend(email_items)
                
                # Get sent emails
                sent_emails = self.outlook_integration.get_sent_emails(start_date, end_date)
                sent_items = self.outlook_integration.convert_to_timeline_items(sent_emails, 'sent')
                all_items.extend(sent_items)
                
                logger.info(f"Found {len(email_items) + len(sent_items)} emails")
            except Exception as e:
                logger.error(f"Error fetching Outlook emails: {e}")
        
        # Fetch emails using simple IMAP (if configured and Outlook not available)
        elif self.simple_email_integration:
            logger.info("Fetching emails via IMAP...")
            try:
                self.simple_email_integration.connect()
                
                # Get recent emails
                emails = self.simple_email_integration.get_emails(limit=100)
                email_items = self.simple_email_integration.convert_to_timeline_items(emails)
                all_items.extend(email_items)
                
                # Get sent emails
                sent_emails = self.simple_email_integration.get_sent_emails(limit=50)
                sent_items = self.simple_email_integration.convert_to_timeline_items(sent_emails)
                all_items.extend(sent_items)
                
                # Get Fireflies emails specifically
                fireflies_emails = self.simple_email_integration.get_fireflies_emails()
                fireflies_items = self.simple_email_integration.convert_to_timeline_items(fireflies_emails)
                all_items.extend(fireflies_items)
                
                self.simple_email_integration.disconnect()
                logger.info(f"Found {len(email_items) + len(sent_items) + len(fireflies_items)} emails")
            except Exception as e:
                logger.error(f"Error fetching emails via IMAP: {e}")
        
        # Fetch Fireflies meetings
        if self.fireflies_integration:
            logger.info("Fetching Fireflies meetings...")
            try:
                transcripts = self.fireflies_integration.get_transcripts(start_date, end_date)
                meeting_items = self.fireflies_integration.convert_to_timeline_items(transcripts)
                all_items.extend(meeting_items)
                logger.info(f"Found {len(meeting_items)} meetings")
            except Exception as e:
                logger.error(f"Error fetching Fireflies meetings: {e}")
        
        self.timeline_items = all_items
        return all_items
    
    def _fetch_screenshots(self, start_date: datetime, end_date: datetime) -> List[UnifiedTimelineItem]:
        """Fetch screenshots from database"""
        # Query screenshots from ChromaDB
        results = self.db_manager.get_all_screenshots()
        
        timeline_items = []
        for result in results:
            metadata = result['metadata']
            
            # Parse timestamp
            created_time = datetime.fromisoformat(metadata['created_time'])
            
            # Check if within date range
            if start_date <= created_time <= end_date:
                item = UnifiedTimelineItem(
                    id=f"screenshot_{result['id']}",
                    source_type=DataSourceType.SCREENSHOT,
                    title=metadata['filename'],
                    content=result['document'],  # The analyzed content
                    timestamp=created_time,
                    last_modified=datetime.fromisoformat(metadata['modified_time']),
                    metadata={
                        'dimensions': metadata.get('dimensions', ''),
                        'device_type': metadata.get('device_type', ''),
                        'file_size': metadata.get('file_size', 0),
                        'original_path': metadata.get('original_path', '')
                    },
                    extracted_concepts=[],
                    concept_categories=[],
                    related_items=[],
                    source_id=result['id'],
                    source_metadata=metadata
                )
                timeline_items.append(item)
        
        return timeline_items
    
    def analyze_timeline(self) -> Dict[str, Any]:
        """Analyze the timeline and extract insights"""
        logger.info("Analyzing timeline...")
        
        # Extract concepts from all items
        self.timeline_items = self.concept_extractor.analyze_timeline_items(self.timeline_items)
        
        # Find related items
        self.timeline_items = self.concept_extractor.find_related_items(self.timeline_items)
        
        # Create concept clusters
        self.concept_clusters = self.concept_extractor.create_concept_clusters(self.timeline_items)
        
        # Create time windows
        time_windows = self.concept_extractor.create_time_windows(self.timeline_items)
        
        # Generate summary statistics
        stats = self._generate_statistics()
        
        return {
            'timeline_items': len(self.timeline_items),
            'concept_clusters': len(self.concept_clusters),
            'time_windows': len(time_windows),
            'statistics': stats,
            'top_concepts': self._get_top_concepts(),
            'activity_summary': self._generate_activity_summary(time_windows)
        }
    
    def _generate_statistics(self) -> Dict[str, Any]:
        """Generate statistics about the timeline"""
        source_counts = {}
        category_counts = {}
        
        for item in self.timeline_items:
            # Count by source
            source_counts[item.source_type.value] = source_counts.get(item.source_type.value, 0) + 1
            
            # Count by category
            for category in item.concept_categories:
                category_counts[category.value] = category_counts.get(category.value, 0) + 1
        
        return {
            'by_source': source_counts,
            'by_category': category_counts,
            'total_concepts': sum(len(item.extracted_concepts) for item in self.timeline_items),
            'avg_concepts_per_item': sum(len(item.extracted_concepts) for item in self.timeline_items) / len(self.timeline_items) if self.timeline_items else 0
        }
    
    def _get_top_concepts(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the most frequent concepts"""
        concept_freq = {}
        
        for item in self.timeline_items:
            for concept in item.extracted_concepts:
                concept_freq[concept] = concept_freq.get(concept, 0) + 1
        
        # Sort by frequency
        sorted_concepts = sorted(concept_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'concept': concept, 'frequency': freq}
            for concept, freq in sorted_concepts[:limit]
        ]
    
    def _generate_activity_summary(self, time_windows: List[TimeWindow]) -> List[Dict[str, Any]]:
        """Generate activity summary for time windows"""
        summaries = []
        
        for window in time_windows:
            sources = window.get_sources()
            concepts = window.get_concepts()
            
            summary = {
                'start': window.start.isoformat(),
                'end': window.end.isoformat(),
                'item_count': len(window.items),
                'sources': dict(sources),
                'top_concepts': concepts[:10],
                'has_meeting': DataSourceType.FIREFLIES_MEETING in sources,
                'importance_score': sum(item.importance_score for item in window.items) / len(window.items)
            }
            
            summaries.append(summary)
        
        return summaries
    
    def get_timeline_for_display(self) -> List[Dict[str, Any]]:
        """Get timeline items formatted for display"""
        return [item.to_dict() for item in sorted(self.timeline_items, key=lambda x: x.timestamp, reverse=True)]
    
    def get_clusters_for_display(self) -> List[Dict[str, Any]]:
        """Get concept clusters formatted for display"""
        return [cluster.to_dict() for cluster in self.concept_clusters]
    
    def save_analysis(self, output_path: str):
        """Save analysis results to file"""
        analysis = {
            'generated_at': datetime.now().isoformat(),
            'timeline_items': self.get_timeline_for_display(),
            'concept_clusters': self.get_clusters_for_display(),
            'statistics': self._generate_statistics(),
            'top_concepts': self._get_top_concepts()
        }
        
        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        logger.info(f"Analysis saved to {output_path}")
    
    def search_across_sources(self, query: str) -> List[UnifiedTimelineItem]:
        """Search across all data sources"""
        results = []
        
        # Search screenshots
        screenshot_results = self.db_manager.search_screenshots(query)
        # Convert to timeline items...
        
        # Search notes
        if self.notes_integration:
            note_results = self.notes_integration.search_notes(query)
            results.extend(note_results)
        
        # Search emails
        if self.outlook_integration:
            email_results = self.outlook_integration.search_emails(query)
            results.extend(email_results)
        
        # Search in cached timeline items
        for item in self.timeline_items:
            if query.lower() in item.title.lower() or query.lower() in item.content.lower():
                if item not in results:
                    results.append(item)
        
        return results