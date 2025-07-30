"""
Simple email integration using IMAP - works with most email providers
"""
import imaplib
import email
from email.header import decode_header
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional
import os

from .data_models import UnifiedTimelineItem, DataSourceType, ConceptCategory

logger = logging.getLogger(__name__)


class SimpleEmailIntegration:
    """Simple IMAP-based email integration"""
    
    # Common IMAP settings for popular providers
    PROVIDERS = {
        'gmail': {
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587
        },
        'outlook': {
            'imap_server': 'outlook.office365.com',
            'imap_port': 993,
            'smtp_server': 'smtp.office365.com',
            'smtp_port': 587
        },
        'yahoo': {
            'imap_server': 'imap.mail.yahoo.com',
            'imap_port': 993,
            'smtp_server': 'smtp.mail.yahoo.com',
            'smtp_port': 587
        },
        'icloud': {
            'imap_server': 'imap.mail.me.com',
            'imap_port': 993,
            'smtp_server': 'smtp.mail.me.com',
            'smtp_port': 587
        }
    }
    
    def __init__(self, email_address: str = None, password: str = None, provider: str = 'gmail'):
        self.email_address = email_address or os.getenv('EMAIL_ADDRESS')
        self.password = password or os.getenv('EMAIL_PASSWORD')
        self.provider = provider
        self.imap = None
        
        if provider in self.PROVIDERS:
            self.settings = self.PROVIDERS[provider]
        else:
            # Custom provider
            self.settings = {
                'imap_server': os.getenv('IMAP_SERVER'),
                'imap_port': int(os.getenv('IMAP_PORT', '993'))
            }
    
    def connect(self):
        """Connect to email server"""
        try:
            # Create IMAP4 client
            self.imap = imaplib.IMAP4_SSL(
                self.settings['imap_server'], 
                self.settings['imap_port']
            )
            
            # Authenticate
            self.imap.login(self.email_address, self.password)
            logger.info(f"Connected to {self.provider} email")
            
        except Exception as e:
            logger.error(f"Failed to connect to email: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from email server"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass
    
    def get_emails(self, folder: str = 'INBOX', limit: int = 100, 
                   search_criteria: str = 'ALL') -> List[Dict[str, Any]]:
        """Get emails from specified folder"""
        emails = []
        
        try:
            # Select folder
            self.imap.select(folder)
            
            # Search emails
            _, message_ids = self.imap.search(None, search_criteria)
            
            # Get email IDs
            email_ids = message_ids[0].split()
            
            # Limit number of emails
            email_ids = email_ids[-limit:]  # Get most recent
            
            for email_id in email_ids:
                try:
                    # Fetch email data
                    _, msg_data = self.imap.fetch(email_id, '(RFC822)')
                    
                    # Parse email
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            
                            # Extract email data
                            email_data = self._parse_email(msg)
                            email_data['id'] = email_id.decode()
                            email_data['folder'] = folder
                            
                            emails.append(email_data)
                            
                except Exception as e:
                    logger.error(f"Error parsing email {email_id}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
        
        return emails
    
    def _parse_email(self, msg) -> Dict[str, Any]:
        """Parse email message"""
        # Decode subject
        subject = decode_header(msg["Subject"])[0][0]
        if isinstance(subject, bytes):
            subject = subject.decode()
        
        # Get sender
        sender = msg.get("From", "")
        
        # Get date
        date_str = msg.get("Date", "")
        try:
            # Parse email date
            email_date = email.utils.parsedate_to_datetime(date_str)
        except:
            email_date = datetime.now()
        
        # Get body
        body = self._get_email_body(msg)
        
        # Check if it's a Fireflies email
        is_fireflies = 'fireflies' in sender.lower() or 'fireflies' in subject.lower()
        
        return {
            'subject': subject,
            'sender': sender,
            'recipients': msg.get("To", "").split(','),
            'date': email_date,
            'body': body,
            'is_fireflies': is_fireflies,
            'has_attachments': self._has_attachments(msg)
        }
    
    def _get_email_body(self, msg) -> str:
        """Extract email body"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                body = str(msg.get_payload())
        
        return body
    
    def _has_attachments(self, msg) -> bool:
        """Check if email has attachments"""
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                return True
        return False
    
    def get_sent_emails(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get sent emails"""
        # Try common sent folder names
        sent_folders = ['Sent', 'Sent Items', 'Sent Messages', '[Gmail]/Sent Mail']
        
        for folder in sent_folders:
            try:
                emails = self.get_emails(folder=folder, limit=limit)
                if emails:
                    return emails
            except:
                continue
        
        return []
    
    def search_emails(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search emails by subject or sender"""
        # IMAP search criteria
        search_criteria = f'(OR SUBJECT "{query}" FROM "{query}")'
        return self.get_emails(search_criteria=search_criteria, limit=limit)
    
    def get_fireflies_emails(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get Fireflies meeting emails"""
        search_criteria = '(FROM "fireflies.ai")'
        return self.get_emails(search_criteria=search_criteria, limit=limit)
    
    def convert_to_timeline_items(self, emails: List[Dict[str, Any]]) -> List[UnifiedTimelineItem]:
        """Convert emails to unified timeline items"""
        timeline_items = []
        
        for email_data in emails:
            try:
                item = UnifiedTimelineItem(
                    id=f"email_{email_data['id']}",
                    source_type=DataSourceType.OUTLOOK_EMAIL,
                    title=email_data['subject'],
                    content=email_data['body'][:2000],  # Limit content length
                    timestamp=email_data['date'],
                    last_modified=email_data['date'],
                    metadata={
                        'sender': email_data['sender'],
                        'recipients': email_data['recipients'],
                        'folder': email_data.get('folder', 'INBOX'),
                        'has_attachments': email_data['has_attachments'],
                        'is_fireflies': email_data['is_fireflies']
                    },
                    extracted_concepts=[],
                    concept_categories=[
                        ConceptCategory.COMMUNICATION,
                        ConceptCategory.MEETING if email_data['is_fireflies'] else ConceptCategory.OTHER
                    ],
                    related_items=[],
                    source_id=email_data['id'],
                    source_metadata=email_data
                )
                
                timeline_items.append(item)
                
            except Exception as e:
                logger.error(f"Error converting email {email_data.get('id')}: {e}")
                continue
        
        return timeline_items


class AppleMailIntegration:
    """Direct integration with Apple Mail using AppleScript"""
    
    def __init__(self):
        self.check_platform()
    
    def check_platform(self):
        """Check if running on macOS"""
        import platform
        if platform.system() != 'Darwin':
            raise Exception("Apple Mail integration only works on macOS")
    
    def get_recent_emails(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get recent emails using AppleScript"""
        import subprocess
        
        # AppleScript to get recent emails
        script = f'''
        tell application "Mail"
            set emailList to {{}}
            set cutoffDate to (current date) - ({days} * days)
            
            repeat with theAccount in accounts
                repeat with theMailbox in mailboxes of theAccount
                    repeat with theMessage in messages of theMailbox
                        if date received of theMessage > cutoffDate then
                            set emailInfo to {{}}
                            set emailInfo to emailInfo & subject of theMessage
                            set emailInfo to emailInfo & (sender of theMessage as string)
                            set emailInfo to emailInfo & (date received of theMessage as string)
                            set emailInfo to emailInfo & (id of theMessage as string)
                            set end of emailList to emailInfo
                        end if
                    end repeat
                end repeat
            end repeat
            
            return emailList
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True
            )
            
            # Parse the result
            # This is simplified - you'd need to parse AppleScript output properly
            return []
            
        except Exception as e:
            logger.error(f"Error getting Apple Mail emails: {e}")
            return []