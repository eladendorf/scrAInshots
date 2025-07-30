"""
Microsoft Outlook integration using Graph API
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
from urllib.parse import quote

from .data_models import UnifiedTimelineItem, DataSourceType, ConceptCategory

logger = logging.getLogger(__name__)


class OutlookIntegration:
    """Integration for Microsoft Outlook via Graph API"""
    
    def __init__(self, client_id: str = None, client_secret: str = None, tenant_id: str = None):
        self.client_id = client_id or os.getenv('OUTLOOK_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('OUTLOOK_CLIENT_SECRET')
        self.tenant_id = tenant_id or os.getenv('OUTLOOK_TENANT_ID')
        self.access_token = None
        self.token_expiry = None
        
        # Graph API endpoints
        self.graph_base = "https://graph.microsoft.com/v1.0"
        self.auth_base = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0"
    
    def authenticate(self, username: str = None, refresh_token: str = None):
        """Authenticate with Microsoft Graph API"""
        if refresh_token:
            self._refresh_access_token(refresh_token)
        else:
            # For initial setup, we'd need to implement OAuth flow
            # This is a simplified version - in production, implement full OAuth
            logger.warning("Full OAuth flow not implemented. Please provide refresh token.")
            raise NotImplementedError("OAuth flow implementation needed")
    
    def _refresh_access_token(self, refresh_token: str):
        """Refresh the access token using refresh token"""
        token_url = f"{self.auth_base}/token"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'Mail.Read Mail.Read.Shared User.Read offline_access'
        }
        
        response = requests.post(token_url, data=data)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data['access_token']
            self.token_expiry = datetime.now() + timedelta(seconds=token_data['expires_in'])
        else:
            logger.error(f"Failed to refresh token: {response.status_code} - {response.text}")
            raise Exception("Failed to authenticate with Outlook")
    
    def _make_graph_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to Graph API"""
        if not self.access_token or datetime.now() >= self.token_expiry:
            raise Exception("Access token expired or not set")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.graph_base}{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Graph API error: {response.status_code} - {response.text}")
            raise Exception(f"Graph API request failed: {response.status_code}")
    
    def get_emails(self, start_date: datetime, end_date: datetime, 
                   filter_fireflies: bool = True) -> List[Dict[str, Any]]:
        """Get emails within date range, optionally filtering for Fireflies meetings"""
        
        # Build filter query
        date_filter = f"receivedDateTime ge {start_date.isoformat()}Z and receivedDateTime le {end_date.isoformat()}Z"
        
        if filter_fireflies:
            # Filter for Fireflies emails
            date_filter += " and (from/emailAddress/address eq 'noreply@fireflies.ai' or contains(subject, 'Fireflies'))"
        
        params = {
            '$filter': date_filter,
            '$select': 'id,subject,bodyPreview,from,toRecipients,receivedDateTime,lastModifiedDateTime,importance,categories',
            '$orderby': 'receivedDateTime DESC',
            '$top': 100  # Adjust as needed
        }
        
        all_emails = []
        next_link = '/me/messages'
        
        while next_link:
            if next_link.startswith('http'):
                # Full URL from @odata.nextLink
                response = requests.get(next_link, headers={
                    'Authorization': f'Bearer {self.access_token}'
                })
                data = response.json()
            else:
                data = self._make_graph_request(next_link, params if next_link == '/me/messages' else None)
            
            all_emails.extend(data.get('value', []))
            next_link = data.get('@odata.nextLink')
        
        return all_emails
    
    def get_sent_emails(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get sent emails for concept extraction"""
        date_filter = f"sentDateTime ge {start_date.isoformat()}Z and sentDateTime le {end_date.isoformat()}Z"
        
        params = {
            '$filter': date_filter,
            '$select': 'id,subject,bodyPreview,toRecipients,sentDateTime,importance,categories',
            '$orderby': 'sentDateTime DESC',
            '$top': 100
        }
        
        return self._make_graph_request('/me/mailFolders/sentitems/messages', params).get('value', [])
    
    def convert_to_timeline_items(self, emails: List[Dict[str, Any]], 
                                  email_type: str = 'received') -> List[UnifiedTimelineItem]:
        """Convert Outlook emails to unified timeline items"""
        timeline_items = []
        
        for email in emails:
            try:
                # Determine timestamp based on email type
                if email_type == 'sent':
                    timestamp = datetime.fromisoformat(email['sentDateTime'].replace('Z', '+00:00'))
                else:
                    timestamp = datetime.fromisoformat(email['receivedDateTime'].replace('Z', '+00:00'))
                
                last_modified = datetime.fromisoformat(
                    email.get('lastModifiedDateTime', email.get('receivedDateTime', '')).replace('Z', '+00:00')
                )
                
                # Extract sender/recipient info
                if email_type == 'sent':
                    participants = [r['emailAddress']['address'] for r in email.get('toRecipients', [])]
                    participant_label = 'to'
                else:
                    participants = [email['from']['emailAddress']['address']]
                    participant_label = 'from'
                
                # Determine if this is a Fireflies meeting
                is_fireflies = 'fireflies.ai' in email.get('from', {}).get('emailAddress', {}).get('address', '').lower()
                
                item = UnifiedTimelineItem(
                    id=f"email_{email['id']}",
                    source_type=DataSourceType.OUTLOOK_EMAIL,
                    title=email['subject'],
                    content=email.get('bodyPreview', ''),
                    timestamp=timestamp,
                    last_modified=last_modified,
                    metadata={
                        'email_type': email_type,
                        participant_label: participants,
                        'importance': email.get('importance', 'normal'),
                        'categories': email.get('categories', []),
                        'is_fireflies': is_fireflies
                    },
                    extracted_concepts=[],
                    concept_categories=[],
                    related_items=[],
                    source_id=email['id'],
                    source_metadata=email
                )
                
                timeline_items.append(item)
                
            except Exception as e:
                logger.error(f"Error converting email {email.get('id')}: {e}")
                continue
        
        return timeline_items
    
    def get_full_email_content(self, email_id: str) -> Optional[str]:
        """Get full email body content"""
        try:
            email = self._make_graph_request(f'/me/messages/{email_id}')
            return email.get('body', {}).get('content', '')
        except Exception as e:
            logger.error(f"Error getting full email content: {e}")
            return None
    
    def search_emails(self, query: str, limit: int = 50) -> List[UnifiedTimelineItem]:
        """Search emails by content"""
        params = {
            '$search': f'"{query}"',
            '$select': 'id,subject,bodyPreview,from,receivedDateTime,lastModifiedDateTime',
            '$top': limit
        }
        
        results = self._make_graph_request('/me/messages', params)
        return self.convert_to_timeline_items(results.get('value', []))