"""
Fireflies.ai integration using GraphQL API
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests

from .data_models import UnifiedTimelineItem, DataSourceType, ConceptCategory

logger = logging.getLogger(__name__)


class FirefliesIntegration:
    """Integration for Fireflies.ai meeting transcripts"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('FIREFLIES_API_KEY')
        self.api_url = "https://api.fireflies.ai/graphql"
        
        if not self.api_key:
            logger.warning("Fireflies API key not provided")
    
    def _make_graphql_request(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make GraphQL request to Fireflies API"""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        response = requests.post(self.api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                logger.error(f"GraphQL errors: {data['errors']}")
                raise Exception(f"GraphQL query failed: {data['errors']}")
            return data.get('data', {})
        else:
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            raise Exception(f"Fireflies API request failed: {response.status_code}")
    
    def get_transcripts(self, start_date: datetime, end_date: datetime, limit: int = 50) -> List[Dict[str, Any]]:
        """Get meeting transcripts within date range"""
        
        query = """
        query GetTranscripts($dateMin: DateTime, $dateMax: DateTime, $limit: Int, $skip: Int) {
            transcripts(
                date_min: $dateMin
                date_max: $dateMax
                limit: $limit
                skip: $skip
            ) {
                id
                title
                date
                duration
                meeting_url
                participants
                organizer_email
                summary {
                    overview
                    shorthand_bullet
                    keywords
                    action_items
                    outline
                }
                sentences {
                    text
                    speaker_name
                    start_time
                }
            }
        }
        """
        
        variables = {
            'dateMin': start_date.isoformat() + 'Z',
            'dateMax': end_date.isoformat() + 'Z',
            'limit': limit,
            'skip': 0
        }
        
        all_transcripts = []
        
        while True:
            result = self._make_graphql_request(query, variables)
            transcripts = result.get('transcripts', [])
            
            if not transcripts:
                break
            
            all_transcripts.extend(transcripts)
            
            if len(transcripts) < limit:
                break
            
            variables['skip'] += limit
        
        return all_transcripts
    
    def get_transcript_by_id(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific transcript by ID"""
        
        query = """
        query GetTranscript($transcriptId: String!) {
            transcript(id: $transcriptId) {
                id
                title
                date
                duration
                meeting_url
                participants
                organizer_email
                summary {
                    overview
                    shorthand_bullet
                    keywords
                    action_items
                    outline
                }
                sentences {
                    text
                    speaker_name
                    start_time
                }
                audio_url
            }
        }
        """
        
        variables = {'transcriptId': transcript_id}
        
        result = self._make_graphql_request(query, variables)
        return result.get('transcript')
    
    def convert_to_timeline_items(self, transcripts: List[Dict[str, Any]]) -> List[UnifiedTimelineItem]:
        """Convert Fireflies transcripts to unified timeline items"""
        timeline_items = []
        
        for transcript in transcripts:
            try:
                # Parse meeting date
                meeting_date = datetime.fromisoformat(transcript['date'].replace('Z', '+00:00'))
                
                # Combine transcript sentences into full content
                content_parts = []
                if transcript.get('sentences'):
                    for sentence in transcript['sentences']:
                        speaker = sentence.get('speaker_name', 'Unknown')
                        text = sentence.get('text', '')
                        content_parts.append(f"{speaker}: {text}")
                
                full_content = '\n'.join(content_parts)
                
                # Extract summary info
                summary_data = transcript.get('summary', {})
                
                item = UnifiedTimelineItem(
                    id=f"fireflies_{transcript['id']}",
                    source_type=DataSourceType.FIREFLIES_MEETING,
                    title=transcript['title'],
                    content=full_content or summary_data.get('overview', ''),
                    timestamp=meeting_date,
                    last_modified=meeting_date,  # Fireflies doesn't provide modification date
                    metadata={
                        'duration_minutes': transcript.get('duration', 0) / 60,
                        'participants': transcript.get('participants', []),
                        'organizer': transcript.get('organizer_email', ''),
                        'meeting_url': transcript.get('meeting_url', ''),
                        'has_action_items': bool(summary_data.get('action_items')),
                        'keywords': summary_data.get('keywords', [])
                    },
                    extracted_concepts=summary_data.get('keywords', []),
                    concept_categories=[ConceptCategory.MEETING],
                    related_items=[],
                    source_id=transcript['id'],
                    source_metadata=transcript,
                    summary=summary_data.get('overview', ''),
                    key_topics=summary_data.get('keywords', [])
                )
                
                # Add action items to metadata if present
                if summary_data.get('action_items'):
                    item.metadata['action_items'] = summary_data['action_items']
                
                timeline_items.append(item)
                
            except Exception as e:
                logger.error(f"Error converting transcript {transcript.get('id')}: {e}")
                continue
        
        return timeline_items
    
    def search_transcripts(self, query: str, limit: int = 20) -> List[UnifiedTimelineItem]:
        """Search transcripts by content"""
        # Note: Fireflies API doesn't have direct search endpoint in GraphQL
        # This would need to be implemented by fetching transcripts and filtering locally
        # or using their REST API if available
        
        logger.warning("Search functionality not fully implemented for Fireflies")
        # For now, return empty list
        return []
    
    def get_action_items(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Extract all action items from meetings in date range"""
        transcripts = self.get_transcripts(start_date, end_date)
        
        action_items = []
        for transcript in transcripts:
            summary = transcript.get('summary', {})
            items = summary.get('action_items', [])
            
            for item in items:
                action_items.append({
                    'action': item,
                    'meeting_id': transcript['id'],
                    'meeting_title': transcript['title'],
                    'meeting_date': transcript['date'],
                    'participants': transcript.get('participants', [])
                })
        
        return action_items