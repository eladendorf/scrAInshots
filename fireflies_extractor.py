#!/usr/bin/env python3
"""
Fireflies Meeting Extractor
Extracts all meeting information, identifies personal action items, and exports to markdown
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re

from integrations.fireflies_integration import FirefliesIntegration
from config_manager import ConfigManager

logger = logging.getLogger(__name__)


class FirefliesExtractor:
    """Extract and analyze Fireflies meetings with focus on personal action items"""
    
    def __init__(self, user_name: str = None, user_email: str = None):
        # Initialize config
        self.config_manager = ConfigManager()
        config = self.config_manager.get_config()
        
        # Initialize Fireflies integration
        self.fireflies = FirefliesIntegration(api_key=config.get('fireflies_api_key'))
        
        # User identification for action items
        self.user_name = user_name
        self.user_email = user_email or config.get('email_address', '')
        self.user_aliases = self._generate_user_aliases()
        
        # Output directory
        self.output_dir = Path.home() / 'FirefliesMeetings'
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.meetings_dir = self.output_dir / 'meetings'
        self.summaries_dir = self.output_dir / 'summaries'
        self.actions_dir = self.output_dir / 'action_items'
        
        for dir in [self.meetings_dir, self.summaries_dir, self.actions_dir]:
            dir.mkdir(exist_ok=True)
    
    def _generate_user_aliases(self) -> List[str]:
        """Generate possible aliases for the user"""
        aliases = []
        
        if self.user_email:
            # Extract name from email
            email_name = self.user_email.split('@')[0]
            aliases.append(email_name.lower())
            aliases.append(email_name.replace('.', ' ').title())
            
        if self.user_name:
            aliases.append(self.user_name.lower())
            aliases.append(self.user_name)
            # First name only
            first_name = self.user_name.split()[0] if ' ' in self.user_name else self.user_name
            aliases.append(first_name.lower())
            aliases.append(first_name)
        
        # Common variations
        aliases.extend(['me', 'i', 'my', 'mine'])
        
        return list(set(aliases))
    
    def extract_all_meetings(self, days_back: int = 730) -> List[Dict[str, Any]]:
        """Extract all meetings from the past N days (default 2 years)"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Extracting meetings from {start_date.date()} to {end_date.date()}")
        
        # Get full transcript data with enhanced query
        query = """
        query GetDetailedTranscripts($dateMin: DateTime, $dateMax: DateTime, $limit: Int, $skip: Int) {
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
                    notes
                }
                sentences {
                    text
                    speaker_name
                    start_time
                    end_time
                }
                speakers {
                    name
                    email
                    talk_time
                }
                sentiments {
                    sentiment
                    score
                }
                topics {
                    topic
                    score
                }
            }
        }
        """
        
        variables = {
            'dateMin': start_date.isoformat() + 'Z',
            'dateMax': end_date.isoformat() + 'Z',
            'limit': 50,
            'skip': 0
        }
        
        all_meetings = []
        
        while True:
            try:
                result = self.fireflies._make_graphql_request(query, variables)
                meetings = result.get('transcripts', [])
                
                if not meetings:
                    break
                
                all_meetings.extend(meetings)
                logger.info(f"Fetched {len(meetings)} meetings (total: {len(all_meetings)})")
                
                if len(meetings) < variables['limit']:
                    break
                
                variables['skip'] += variables['limit']
                
            except Exception as e:
                logger.error(f"Error fetching meetings: {e}")
                break
        
        return all_meetings
    
    def analyze_meeting(self, meeting: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a single meeting for key information and personal action items"""
        analysis = {
            'id': meeting['id'],
            'title': meeting['title'],
            'date': meeting['date'],
            'duration_minutes': meeting.get('duration', 0) / 60,
            'participants': meeting.get('participants', []),
            'my_action_items': [],
            'all_action_items': [],
            'my_speaking_time': 0,
            'total_speaking_time': 0,
            'sentiment_summary': {},
            'key_topics': [],
            'meeting_type': self._classify_meeting(meeting),
            'my_contributions': []
        }
        
        # Extract action items assigned to me
        if meeting.get('summary', {}).get('action_items'):
            for action in meeting['summary']['action_items']:
                action_lower = action.lower()
                is_mine = False
                
                # Check if action item is assigned to me
                for alias in self.user_aliases:
                    if alias in action_lower:
                        is_mine = True
                        break
                
                # Also check for assignment patterns
                assignment_patterns = [
                    r'@\w+',  # @mentions
                    r'assigned to (\w+)',
                    r'(\w+) will',
                    r'(\w+) to',
                    r'(\w+) should'
                ]
                
                for pattern in assignment_patterns:
                    matches = re.findall(pattern, action_lower)
                    for match in matches:
                        if match in self.user_aliases:
                            is_mine = True
                            break
                
                if is_mine:
                    analysis['my_action_items'].append(action)
                
                analysis['all_action_items'].append({
                    'action': action,
                    'assigned_to_me': is_mine
                })
        
        # Analyze my contributions
        if meeting.get('sentences'):
            for sentence in meeting['sentences']:
                speaker = sentence.get('speaker_name', '').lower()
                
                # Check if I'm the speaker
                is_me = any(alias in speaker for alias in self.user_aliases)
                
                if is_me:
                    analysis['my_contributions'].append({
                        'text': sentence['text'],
                        'time': sentence.get('start_time', 0)
                    })
        
        # Calculate speaking times
        if meeting.get('speakers'):
            for speaker in meeting['speakers']:
                speaker_name = speaker.get('name', '').lower()
                talk_time = speaker.get('talk_time', 0)
                
                analysis['total_speaking_time'] += talk_time
                
                if any(alias in speaker_name for alias in self.user_aliases):
                    analysis['my_speaking_time'] = talk_time
        
        # Sentiment analysis
        if meeting.get('sentiments'):
            sentiments = {}
            for item in meeting['sentiments']:
                sentiment = item.get('sentiment', 'neutral')
                sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            analysis['sentiment_summary'] = sentiments
        
        # Key topics
        if meeting.get('topics'):
            analysis['key_topics'] = [
                topic['topic'] for topic in 
                sorted(meeting['topics'], key=lambda x: x.get('score', 0), reverse=True)[:5]
            ]
        elif meeting.get('summary', {}).get('keywords'):
            analysis['key_topics'] = meeting['summary']['keywords'][:5]
        
        return analysis
    
    def _classify_meeting(self, meeting: Dict[str, Any]) -> str:
        """Classify the type of meeting based on title and content"""
        title = meeting.get('title', '').lower()
        
        # Common meeting type patterns
        patterns = {
            'standup': ['standup', 'stand-up', 'daily', 'scrum'],
            'one_on_one': ['1:1', '1-1', 'one on one', 'one-on-one'],
            'review': ['review', 'retro', 'retrospective', 'demo'],
            'planning': ['planning', 'sprint', 'roadmap', 'strategy'],
            'interview': ['interview', 'screening', 'hiring'],
            'client': ['client', 'customer', 'sales', 'pitch'],
            'team': ['team', 'all hands', 'all-hands', 'department'],
            'project': ['project', 'kickoff', 'kick-off', 'update']
        }
        
        for meeting_type, keywords in patterns.items():
            if any(keyword in title for keyword in keywords):
                return meeting_type
        
        return 'general'
    
    def generate_meeting_markdown(self, meeting: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate detailed markdown for a single meeting"""
        md = f"""# {meeting['title']}

## Meeting Information
- **Date**: {datetime.fromisoformat(meeting['date'].replace('Z', '+00:00')).strftime('%B %d, %Y at %I:%M %p')}
- **Duration**: {analysis['duration_minutes']:.0f} minutes
- **Type**: {analysis['meeting_type'].replace('_', ' ').title()}
- **Participants**: {', '.join(meeting.get('participants', []))}

## Summary
{meeting.get('summary', {}).get('overview', 'No summary available')}

## Key Topics
"""
        
        for topic in analysis['key_topics']:
            md += f"- {topic}\n"
        
        # My participation metrics
        if analysis['total_speaking_time'] > 0:
            my_percentage = (analysis['my_speaking_time'] / analysis['total_speaking_time']) * 100
            md += f"\n## My Participation\n"
            md += f"- **Speaking Time**: {analysis['my_speaking_time'] / 60:.1f} minutes ({my_percentage:.1f}% of meeting)\n"
            md += f"- **Contributions**: {len(analysis['my_contributions'])} statements\n"
        
        # Action items
        if analysis['my_action_items']:
            md += f"\n## My Action Items ⚡\n"
            for i, action in enumerate(analysis['my_action_items'], 1):
                md += f"{i}. {action}\n"
        
        if analysis['all_action_items']:
            md += f"\n## All Action Items\n"
            for item in analysis['all_action_items']:
                prefix = "✓" if item['assigned_to_me'] else "•"
                md += f"{prefix} {item['action']}\n"
        
        # Meeting outline
        if meeting.get('summary', {}).get('outline'):
            md += f"\n## Meeting Outline\n{meeting['summary']['outline']}\n"
        
        # Key points
        if meeting.get('summary', {}).get('shorthand_bullet'):
            md += f"\n## Key Points\n"
            bullets = meeting['summary']['shorthand_bullet']
            if isinstance(bullets, list):
                for bullet in bullets:
                    md += f"- {bullet}\n"
            else:
                md += f"{bullets}\n"
        
        # Notes
        if meeting.get('summary', {}).get('notes'):
            md += f"\n## Additional Notes\n{meeting['summary']['notes']}\n"
        
        # Sentiment
        if analysis['sentiment_summary']:
            md += f"\n## Meeting Sentiment\n"
            total_sentiments = sum(analysis['sentiment_summary'].values())
            for sentiment, count in sorted(analysis['sentiment_summary'].items(), 
                                         key=lambda x: x[1], reverse=True):
                percentage = (count / total_sentiments) * 100
                md += f"- {sentiment.title()}: {percentage:.1f}%\n"
        
        # Full transcript (optional - can be very long)
        md += f"\n## Transcript\n"
        md += f"<details>\n<summary>Click to expand full transcript</summary>\n\n"
        
        if meeting.get('sentences'):
            current_speaker = None
            for sentence in meeting['sentences']:
                speaker = sentence.get('speaker_name', 'Unknown')
                text = sentence.get('text', '')
                
                if speaker != current_speaker:
                    md += f"\n**{speaker}**: "
                    current_speaker = speaker
                
                md += f"{text} "
        
        md += f"\n</details>\n"
        
        return md
    
    def generate_summary_markdown(self, analyses: List[Dict[str, Any]]) -> str:
        """Generate a summary of all meetings"""
        total_meetings = len(analyses)
        total_action_items = sum(len(a['my_action_items']) for a in analyses)
        total_speaking_time = sum(a['my_speaking_time'] for a in analyses) / 3600  # Convert to hours
        
        # Group by meeting type
        meeting_types = {}
        for analysis in analyses:
            mtype = analysis['meeting_type']
            meeting_types[mtype] = meeting_types.get(mtype, 0) + 1
        
        # Group action items by status (this is a simple heuristic)
        recent_actions = []
        older_actions = []
        
        for analysis in analyses:
            meeting_date = datetime.fromisoformat(analysis['date'].replace('Z', '+00:00'))
            days_ago = (datetime.now() - meeting_date).days
            
            for action in analysis['my_action_items']:
                if days_ago <= 7:
                    recent_actions.append((action, analysis['title'], meeting_date))
                else:
                    older_actions.append((action, analysis['title'], meeting_date))
        
        md = f"""# Fireflies Meeting Analysis Summary

## Overview
- **Total Meetings**: {total_meetings}
- **Total Action Items Assigned to Me**: {total_action_items}
- **Total Speaking Time**: {total_speaking_time:.1f} hours
- **Analysis Period**: {analyses[-1]['date'][:10]} to {analyses[0]['date'][:10]}

## Meeting Types
"""
        
        for mtype, count in sorted(meeting_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_meetings) * 100
            md += f"- **{mtype.replace('_', ' ').title()}**: {count} meetings ({percentage:.1f}%)\n"
        
        # Recent action items
        if recent_actions:
            md += f"\n## Recent Action Items (Last 7 Days) 🔥\n"
            for action, meeting, date in recent_actions:
                md += f"- [ ] {action}\n"
                md += f"  - From: *{meeting}* on {date.strftime('%b %d')}\n"
        
        # Older action items
        if older_actions:
            md += f"\n## Older Action Items (May Need Follow-up) ⚠️\n"
            for action, meeting, date in older_actions[:10]:  # Limit to 10
                md += f"- [ ] {action}\n"
                md += f"  - From: *{meeting}* on {date.strftime('%b %d')}\n"
        
        # Key topics across all meetings
        all_topics = []
        for analysis in analyses:
            all_topics.extend(analysis['key_topics'])
        
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        md += f"\n## Most Discussed Topics\n"
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
            md += f"- **{topic}**: {count} meetings\n"
        
        # Meeting participation trends
        md += f"\n## Participation Trends\n"
        
        # Calculate average participation by meeting type
        participation_by_type = {}
        for analysis in analyses:
            mtype = analysis['meeting_type']
            if mtype not in participation_by_type:
                participation_by_type[mtype] = []
            
            if analysis['total_speaking_time'] > 0:
                percentage = (analysis['my_speaking_time'] / analysis['total_speaking_time']) * 100
                participation_by_type[mtype].append(percentage)
        
        for mtype, percentages in participation_by_type.items():
            if percentages:
                avg_participation = sum(percentages) / len(percentages)
                md += f"- **{mtype.replace('_', ' ').title()}**: {avg_participation:.1f}% average participation\n"
        
        return md
    
    def export_to_markdown(self, meetings: List[Dict[str, Any]], 
                          analyses: List[Dict[str, Any]]) -> Dict[str, Path]:
        """Export all meetings and summaries to markdown files"""
        exported_files = {
            'meetings': [],
            'summary': None,
            'action_items': None
        }
        
        # Export individual meeting files
        for meeting, analysis in zip(meetings, analyses):
            # Create filename from date and title
            meeting_date = datetime.fromisoformat(meeting['date'].replace('Z', '+00:00'))
            safe_title = re.sub(r'[^\w\s-]', '', meeting['title'])[:50]
            filename = f"{meeting_date.strftime('%Y-%m-%d')}_{safe_title}.md"
            
            filepath = self.meetings_dir / filename
            
            # Generate and save markdown
            md_content = self.generate_meeting_markdown(meeting, analysis)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            exported_files['meetings'].append(filepath)
            logger.info(f"Exported meeting: {filename}")
        
        # Export summary
        summary_path = self.summaries_dir / f"summary_{datetime.now().strftime('%Y-%m-%d')}.md"
        summary_md = self.generate_summary_markdown(analyses)
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_md)
        exported_files['summary'] = summary_path
        
        # Export consolidated action items
        action_items_md = self.generate_action_items_markdown(analyses)
        actions_path = self.actions_dir / f"action_items_{datetime.now().strftime('%Y-%m-%d')}.md"
        with open(actions_path, 'w', encoding='utf-8') as f:
            f.write(action_items_md)
        exported_files['action_items'] = actions_path
        
        # Create index file
        self.create_index_file(exported_files)
        
        return exported_files
    
    def generate_action_items_markdown(self, analyses: List[Dict[str, Any]]) -> str:
        """Generate a dedicated action items tracking document"""
        md = f"""# My Action Items Tracker

*Generated on {datetime.now().strftime('%B %d, %Y')}*

## Overview
Total action items assigned to me: **{sum(len(a['my_action_items']) for a in analyses)}**

## Action Items by Date

"""
        
        # Group by month
        items_by_month = {}
        
        for analysis in analyses:
            meeting_date = datetime.fromisoformat(analysis['date'].replace('Z', '+00:00'))
            month_key = meeting_date.strftime('%Y-%m')
            
            if month_key not in items_by_month:
                items_by_month[month_key] = []
            
            for action in analysis['my_action_items']:
                items_by_month[month_key].append({
                    'action': action,
                    'meeting': analysis['title'],
                    'date': meeting_date,
                    'meeting_id': analysis['id']
                })
        
        # Sort by date (newest first)
        for month_key in sorted(items_by_month.keys(), reverse=True):
            items = items_by_month[month_key]
            month_date = datetime.strptime(month_key, '%Y-%m')
            md += f"### {month_date.strftime('%B %Y')}\n\n"
            
            for item in sorted(items, key=lambda x: x['date'], reverse=True):
                md += f"- [ ] **{item['action']}**\n"
                md += f"  - Meeting: {item['meeting']}\n"
                md += f"  - Date: {item['date'].strftime('%B %d, %Y')}\n"
                md += f"  - Status: _To be updated_\n\n"
        
        return md
    
    def create_index_file(self, exported_files: Dict[str, Any]):
        """Create an index file linking to all exported content"""
        index_path = self.output_dir / 'README.md'
        
        md = f"""# Fireflies Meeting Archive

*Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*

## Quick Links
- [📊 Summary Report]({exported_files['summary'].name})
- [✅ Action Items Tracker]({exported_files['action_items'].name})

## Meeting Files
Total meetings exported: **{len(exported_files['meetings'])}**

### Recent Meetings
"""
        
        # List recent meetings (last 20)
        recent_meetings = sorted(exported_files['meetings'], reverse=True)[:20]
        
        for filepath in recent_meetings:
            # Extract date and title from filename
            filename = filepath.stem
            parts = filename.split('_', 1)
            if len(parts) == 2:
                date_str, title = parts
                md += f"- [{title.replace('-', ' ')}](meetings/{filepath.name}) - {date_str}\n"
            else:
                md += f"- [{filename}](meetings/{filepath.name})\n"
        
        if len(exported_files['meetings']) > 20:
            md += f"\n*... and {len(exported_files['meetings']) - 20} more meetings in the meetings/ directory*\n"
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(md)
    
    def run(self, days_back: int = 730):
        """Run the complete extraction and export process"""
        logger.info("Starting Fireflies extraction process...")
        
        # Extract all meetings
        meetings = self.extract_all_meetings(days_back)
        logger.info(f"Found {len(meetings)} meetings")
        
        if not meetings:
            logger.warning("No meetings found")
            return
        
        # Analyze each meeting
        analyses = []
        for i, meeting in enumerate(meetings):
            logger.info(f"Analyzing meeting {i+1}/{len(meetings)}: {meeting['title']}")
            analysis = self.analyze_meeting(meeting)
            analyses.append(analysis)
        
        # Export to markdown
        exported_files = self.export_to_markdown(meetings, analyses)
        
        logger.info(f"Export complete! Files saved to: {self.output_dir}")
        logger.info(f"- Summary: {exported_files['summary']}")
        logger.info(f"- Action items: {exported_files['action_items']}")
        logger.info(f"- Individual meetings: {len(exported_files['meetings'])} files")
        
        return exported_files


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract Fireflies meetings to markdown")
    parser.add_argument('--name', help='Your name for action item detection')
    parser.add_argument('--email', help='Your email for action item detection')
    parser.add_argument('--days', type=int, default=730, help='Number of days to look back (default: 730)')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run extractor
    extractor = FirefliesExtractor(user_name=args.name, user_email=args.email)
    extractor.run(days_back=args.days)