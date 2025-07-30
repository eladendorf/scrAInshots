#!/usr/bin/env python3
"""
Email Thread Analyzer
Analyzes sent emails and threads to extract insights about mental state, topics, and patterns
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import defaultdict, Counter
import hashlib

from integrations.simple_email_integration import SimpleEmailIntegration
from config_manager import ConfigManager
import requests

logger = logging.getLogger(__name__)


class EmailAnalyzer:
    """Analyze email threads with focus on sent emails and conversations"""
    
    def __init__(self, llm_client=None):
        # Initialize config
        self.config_manager = ConfigManager()
        config = self.config_manager.get_config()
        
        # Initialize email integration
        self.email_client = SimpleEmailIntegration(
            email_address=config.get('email_address'),
            password=config.get('email_password'),
            provider=config.get('email_provider', 'gmail')
        )
        
        # Output directory
        self.output_dir = Path.home() / 'EmailAnalysis'
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.threads_dir = self.output_dir / 'threads'
        self.summaries_dir = self.output_dir / 'summaries'
        self.insights_dir = self.output_dir / 'insights'
        
        for dir in [self.threads_dir, self.summaries_dir, self.insights_dir]:
            dir.mkdir(exist_ok=True)
        
        # LLM client for analysis
        self.llm_client = llm_client
        
        # Mood indicators
        self.mood_indicators = {
            'positive': ['happy', 'excited', 'great', 'excellent', 'wonderful', 'fantastic', 
                        'pleased', 'delighted', 'glad', 'appreciate', 'thanks', 'looking forward'],
            'negative': ['sorry', 'apologize', 'unfortunately', 'concern', 'worried', 'frustrated',
                        'disappointed', 'issue', 'problem', 'difficult', 'challenge', 'unable'],
            'urgent': ['asap', 'urgent', 'immediately', 'critical', 'deadline', 'today', 'now',
                      'quickly', 'priority', 'important', 'rush'],
            'stressed': ['overwhelmed', 'busy', 'swamped', 'hectic', 'crazy', 'backed up',
                        'behind', 'catching up', 'too much', 'bandwidth'],
            'professional': ['per our discussion', 'as discussed', 'following up', 'circling back',
                           'touching base', 'regards', 'sincerely', 'best'],
            'collaborative': ['team', 'together', 'collaborate', 'help', 'assist', 'support',
                            'share', 'input', 'feedback', 'thoughts', 'ideas']
        }
    
    def connect(self):
        """Connect to email server"""
        self.email_client.connect()
    
    def disconnect(self):
        """Disconnect from email server"""
        self.email_client.disconnect()
    
    def get_sent_emails_and_threads(self, days_back: int = 730) -> Tuple[List[Dict], List[Dict]]:
        """Get sent emails and identify threads where user participated"""
        sent_emails = []
        thread_emails = []
        
        try:
            # Get sent emails
            logger.info("Fetching sent emails...")
            sent_emails = self.email_client.get_sent_emails(limit=1000)
            logger.info(f"Found {len(sent_emails)} sent emails")
            
            # Search for emails where we participated in threads
            # This is a simplified approach - ideally we'd use threading headers
            logger.info("Identifying email threads...")
            
            # Get inbox emails to find threads
            inbox_emails = self.email_client.get_emails(folder='INBOX', limit=2000)
            
            # Group by subject (removing Re:, Fwd:, etc.)
            threads = defaultdict(list)
            
            for email in sent_emails + inbox_emails:
                # Normalize subject for threading
                subject = email.get('subject', '')
                clean_subject = re.sub(r'^(Re:|Fwd:|Fw:)\s*', '', subject, flags=re.IGNORECASE).strip()
                
                if clean_subject:
                    thread_key = clean_subject.lower()
                    threads[thread_key].append(email)
            
            # Find threads where we sent at least one email
            our_email = self.config_manager.get_config().get('email_address', '').lower()
            
            for thread_key, emails in threads.items():
                # Check if we sent any emails in this thread
                sent_in_thread = any(
                    our_email in email.get('sender', '').lower() 
                    for email in emails
                )
                
                if sent_in_thread and len(emails) > 1:
                    # Sort by date
                    sorted_emails = sorted(emails, key=lambda x: x['date'])
                    thread_emails.extend(sorted_emails)
            
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
        
        return sent_emails, thread_emails
    
    def analyze_email_thread(self, emails: List[Dict]) -> Dict[str, Any]:
        """Analyze an email thread for patterns and insights"""
        if not emails:
            return {}
        
        # Sort emails by date
        sorted_emails = sorted(emails, key=lambda x: x['date'])
        
        # Thread metadata
        thread_subject = sorted_emails[0].get('subject', 'Unknown Subject')
        clean_subject = re.sub(r'^(Re:|Fwd:|Fw:)\s*', '', thread_subject, flags=re.IGNORECASE).strip()
        
        # Participants
        participants = set()
        for email in sorted_emails:
            participants.add(email.get('sender', ''))
            participants.update(email.get('recipients', []))
        
        # Timeline analysis
        first_email = sorted_emails[0]['date']
        last_email = sorted_emails[-1]['date']
        thread_duration = (last_email - first_email).total_seconds() / 3600  # Hours
        
        # Response time analysis
        our_email = self.config_manager.get_config().get('email_address', '').lower()
        response_times = []
        
        for i in range(1, len(sorted_emails)):
            prev_email = sorted_emails[i-1]
            curr_email = sorted_emails[i]
            
            # If previous email was TO us and current is FROM us
            if (our_email not in prev_email.get('sender', '').lower() and 
                our_email in curr_email.get('sender', '').lower()):
                response_time = (curr_email['date'] - prev_email['date']).total_seconds() / 60  # Minutes
                response_times.append(response_time)
        
        # Analyze content
        thread_content = []
        our_messages = []
        
        for email in sorted_emails:
            content = email.get('body', '')
            thread_content.append(content)
            
            if our_email in email.get('sender', '').lower():
                our_messages.append({
                    'date': email['date'],
                    'content': content,
                    'mood': self.detect_mood(content),
                    'length': len(content.split())
                })
        
        # Thread analysis
        analysis = {
            'subject': clean_subject,
            'thread_id': hashlib.md5(clean_subject.encode()).hexdigest()[:8],
            'participant_count': len(participants),
            'email_count': len(sorted_emails),
            'our_email_count': len(our_messages),
            'thread_duration_hours': thread_duration,
            'first_email': first_email.isoformat(),
            'last_email': last_email.isoformat(),
            'average_response_time_minutes': sum(response_times) / len(response_times) if response_times else 0,
            'quickest_response_minutes': min(response_times) if response_times else 0,
            'thread_status': self.determine_thread_status(sorted_emails),
            'our_messages': our_messages,
            'overall_mood': self.analyze_mood_progression(our_messages),
            'subject_matter': self.categorize_subject_matter(clean_subject, ' '.join(thread_content)),
            'resolution_speed': self.analyze_resolution_speed(sorted_emails, thread_duration)
        }
        
        # Use LLM for deeper analysis if available
        if self.llm_client:
            analysis['llm_insights'] = self.get_llm_insights(sorted_emails)
        
        return analysis
    
    def detect_mood(self, content: str) -> Dict[str, float]:
        """Detect mood indicators in email content"""
        content_lower = content.lower()
        word_count = len(content_lower.split())
        
        mood_scores = {}
        
        for mood, indicators in self.mood_indicators.items():
            score = 0
            for indicator in indicators:
                score += content_lower.count(indicator)
            
            # Normalize by word count
            mood_scores[mood] = (score / max(word_count, 1)) * 100
        
        # Determine primary mood
        primary_mood = max(mood_scores.items(), key=lambda x: x[1])[0] if mood_scores else 'neutral'
        
        return {
            'primary': primary_mood,
            'scores': mood_scores,
            'intensity': sum(mood_scores.values())
        }
    
    def analyze_mood_progression(self, our_messages: List[Dict]) -> Dict[str, Any]:
        """Analyze how mood changes throughout a thread"""
        if not our_messages:
            return {'progression': 'none', 'trend': 'neutral'}
        
        moods = [msg['mood']['primary'] for msg in our_messages]
        
        # Mood transition analysis
        if len(moods) >= 2:
            first_mood = moods[0]
            last_mood = moods[-1]
            
            # Simple progression analysis
            if first_mood in ['negative', 'stressed'] and last_mood in ['positive', 'collaborative']:
                progression = 'improving'
            elif first_mood in ['positive', 'collaborative'] and last_mood in ['negative', 'stressed']:
                progression = 'deteriorating'
            else:
                progression = 'stable'
        else:
            progression = 'single_message'
        
        # Overall trend
        mood_counts = Counter(moods)
        dominant_mood = mood_counts.most_common(1)[0][0] if mood_counts else 'neutral'
        
        return {
            'progression': progression,
            'dominant_mood': dominant_mood,
            'mood_changes': len(set(moods)) - 1,
            'mood_sequence': moods
        }
    
    def determine_thread_status(self, emails: List[Dict]) -> str:
        """Determine if thread was resolved quickly or lingered"""
        if len(emails) <= 2:
            return 'quick_exchange'
        
        # Check time between emails
        time_gaps = []
        for i in range(1, len(emails)):
            gap = (emails[i]['date'] - emails[i-1]['date']).total_seconds() / 3600  # Hours
            time_gaps.append(gap)
        
        avg_gap = sum(time_gaps) / len(time_gaps)
        
        if avg_gap < 2:  # Less than 2 hours average
            return 'active_quick_resolution'
        elif avg_gap < 24:  # Less than a day
            return 'normal_resolution'
        elif avg_gap < 72:  # Less than 3 days
            return 'slow_resolution'
        else:
            return 'lingering_issue'
    
    def categorize_subject_matter(self, subject: str, content: str) -> Dict[str, Any]:
        """Categorize the subject matter of the email thread"""
        combined_text = f"{subject} {content}".lower()
        
        categories = {
            'project': ['project', 'milestone', 'deliverable', 'timeline', 'roadmap'],
            'meeting': ['meeting', 'calendar', 'schedule', 'discuss', 'call', 'sync'],
            'issue': ['issue', 'problem', 'bug', 'error', 'fix', 'resolve'],
            'request': ['request', 'please', 'could you', 'would you', 'need', 'require'],
            'update': ['update', 'status', 'progress', 'report', 'inform'],
            'decision': ['decide', 'decision', 'approve', 'approval', 'confirm'],
            'planning': ['plan', 'planning', 'strategy', 'proposal', 'future'],
            'review': ['review', 'feedback', 'comments', 'thoughts', 'opinion'],
            'social': ['lunch', 'coffee', 'drinks', 'happy hour', 'team', 'celebration'],
            'administrative': ['expense', 'timesheet', 'pto', 'vacation', 'policy', 'process']
        }
        
        detected_categories = []
        
        for category, keywords in categories.items():
            if any(keyword in combined_text for keyword in keywords):
                detected_categories.append(category)
        
        # Extract potential project/product names (capitalized words)
        project_names = re.findall(r'\b[A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*\b', subject)
        
        return {
            'categories': detected_categories if detected_categories else ['general'],
            'primary_category': detected_categories[0] if detected_categories else 'general',
            'potential_projects': project_names
        }
    
    def analyze_resolution_speed(self, emails: List[Dict], duration_hours: float) -> str:
        """Analyze how quickly issues were resolved"""
        email_count = len(emails)
        
        if email_count <= 2 and duration_hours < 24:
            return 'immediate_resolution'
        elif email_count <= 4 and duration_hours < 48:
            return 'quick_resolution'
        elif duration_hours < 168:  # Less than a week
            return 'normal_resolution'
        else:
            return 'extended_discussion'
    
    def get_llm_insights(self, emails: List[Dict]) -> Dict[str, Any]:
        """Use LLM to get deeper insights about the email thread"""
        # This is a placeholder for LLM integration
        # You would implement this based on your LLM setup
        
        prompt = f"""Analyze this email thread and provide insights:
        
1. What was the main topic or issue being discussed?
2. What was the emotional tone and how did it evolve?
3. Was the issue resolved satisfactorily?
4. What does this reveal about the sender's work style and priorities?
5. Any notable patterns or concerns?

Thread summary:
- Subject: {emails[0].get('subject', '')}
- Number of emails: {len(emails)}
- Duration: {(emails[-1]['date'] - emails[0]['date']).days} days

Please provide a brief, insightful analysis.
"""
        
        # Placeholder response
        return {
            'analysis_pending': True,
            'prompt': prompt
        }
    
    def generate_email_markdown(self, thread_analysis: Dict[str, Any]) -> str:
        """Generate markdown for an email thread analysis"""
        md = f"""# Email Thread: {thread_analysis['subject']}

## Thread Overview
- **Duration**: {thread_analysis['thread_duration_hours']:.1f} hours
- **Total Emails**: {thread_analysis['email_count']}
- **My Emails**: {thread_analysis['our_email_count']}
- **Participants**: {thread_analysis['participant_count']}
- **Status**: {thread_analysis['thread_status'].replace('_', ' ').title()}

## Response Patterns
- **Average Response Time**: {thread_analysis['average_response_time_minutes']:.0f} minutes
- **Quickest Response**: {thread_analysis['quickest_response_minutes']:.0f} minutes
- **Resolution Speed**: {thread_analysis['resolution_speed'].replace('_', ' ').title()}

## Subject Matter
- **Primary Category**: {thread_analysis['subject_matter']['primary_category'].title()}
- **All Categories**: {', '.join(thread_analysis['subject_matter']['categories'])}
"""
        
        if thread_analysis['subject_matter']['potential_projects']:
            md += f"- **Related Projects**: {', '.join(thread_analysis['subject_matter']['potential_projects'])}\n"
        
        md += f"\n## Mood Analysis\n"
        mood_data = thread_analysis['overall_mood']
        md += f"- **Dominant Mood**: {mood_data['dominant_mood'].title()}\n"
        md += f"- **Mood Progression**: {mood_data['progression'].replace('_', ' ').title()}\n"
        
        if mood_data['mood_sequence']:
            md += f"- **Mood Sequence**: {' → '.join(mood_data['mood_sequence'])}\n"
        
        md += f"\n## My Messages in Thread\n"
        
        for i, msg in enumerate(thread_analysis['our_messages'], 1):
            msg_date = datetime.fromisoformat(msg['date'].isoformat())
            md += f"\n### Message {i} - {msg_date.strftime('%B %d, %Y at %I:%M %p')}\n"
            md += f"- **Mood**: {msg['mood']['primary'].title()}\n"
            md += f"- **Length**: {msg['length']} words\n"
            
            # Mood intensity indicators
            high_scores = {k: v for k, v in msg['mood']['scores'].items() if v > 5}
            if high_scores:
                md += f"- **Strong Indicators**: {', '.join(f'{k} ({v:.1f}%)' for k, v in high_scores.items())}\n"
        
        if thread_analysis.get('llm_insights'):
            md += f"\n## AI Insights\n"
            md += f"*Analysis pending - would provide deeper insights about communication patterns, emotional intelligence, and work dynamics*\n"
        
        return md
    
    def generate_summary_markdown(self, all_analyses: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive summary of email patterns"""
        total_threads = len(all_analyses)
        total_emails_sent = sum(a['our_email_count'] for a in all_analyses)
        
        # Calculate statistics
        mood_distribution = Counter()
        category_distribution = Counter()
        resolution_distribution = Counter()
        
        response_times = []
        thread_durations = []
        
        for analysis in all_analyses:
            mood_distribution[analysis['overall_mood']['dominant_mood']] += 1
            category_distribution[analysis['subject_matter']['primary_category']] += 1
            resolution_distribution[analysis['thread_status']] += 1
            
            if analysis['average_response_time_minutes'] > 0:
                response_times.append(analysis['average_response_time_minutes'])
            
            thread_durations.append(analysis['thread_duration_hours'])
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        avg_thread_duration = sum(thread_durations) / len(thread_durations) if thread_durations else 0
        
        md = f"""# Email Communication Analysis

## Overview
- **Analysis Period**: 2 years
- **Total Email Threads Analyzed**: {total_threads}
- **Total Emails Sent**: {total_emails_sent}
- **Average Thread Duration**: {avg_thread_duration:.1f} hours
- **Average Response Time**: {avg_response_time:.0f} minutes

## Communication Patterns

### Mood Distribution
"""
        
        for mood, count in mood_distribution.most_common():
            percentage = (count / total_threads) * 100
            md += f"- **{mood.title()}**: {count} threads ({percentage:.1f}%)\n"
        
        md += f"\n### Subject Matter Distribution\n"
        
        for category, count in category_distribution.most_common():
            percentage = (count / total_threads) * 100
            md += f"- **{category.title()}**: {count} threads ({percentage:.1f}%)\n"
        
        md += f"\n### Resolution Patterns\n"
        
        for status, count in resolution_distribution.most_common():
            percentage = (count / total_threads) * 100
            status_display = status.replace('_', ' ').title()
            md += f"- **{status_display}**: {count} threads ({percentage:.1f}%)\n"
        
        # Identify patterns and insights
        md += f"\n## Key Insights\n\n"
        
        # Quick responder analysis
        quick_responses = [a for a in all_analyses if a['average_response_time_minutes'] < 30]
        if quick_responses:
            percentage = (len(quick_responses) / total_threads) * 100
            md += f"### Response Speed\n"
            md += f"- You respond quickly ({percentage:.1f}% of threads have <30min average response time)\n"
            md += f"- This suggests high engagement and availability\n\n"
        
        # Mood insights
        positive_moods = mood_distribution.get('positive', 0) + mood_distribution.get('collaborative', 0)
        negative_moods = mood_distribution.get('negative', 0) + mood_distribution.get('stressed', 0)
        
        if positive_moods > negative_moods * 2:
            md += f"### Emotional Tone\n"
            md += f"- Generally positive communication style\n"
            md += f"- {positive_moods} positive/collaborative threads vs {negative_moods} negative/stressed\n\n"
        elif negative_moods > positive_moods:
            md += f"### Emotional Tone\n"
            md += f"- Higher proportion of challenging communications\n"
            md += f"- May indicate high-pressure environment or challenging period\n\n"
        
        # Work style insights
        urgent_threads = [a for a in all_analyses if 'urgent' in a['overall_mood']['dominant_mood']]
        if urgent_threads:
            md += f"### Work Style\n"
            md += f"- {len(urgent_threads)} threads marked as urgent ({(len(urgent_threads)/total_threads)*100:.1f}%)\n"
            md += f"- Suggests deadline-driven work environment\n\n"
        
        # Long threads analysis
        long_threads = [a for a in all_analyses if a['email_count'] > 10]
        if long_threads:
            md += f"### Complex Discussions\n"
            md += f"- {len(long_threads)} threads with 10+ emails\n"
            md += f"- Topics: {', '.join([t['subject'][:30] + '...' for t in long_threads[:3]])}\n"
            md += f"- These may represent complex projects or challenging issues\n\n"
        
        return md
    
    def export_analysis(self, sent_emails: List[Dict], thread_analyses: List[Dict[str, Any]]):
        """Export all analyses to markdown files"""
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        
        # Export individual thread analyses
        for analysis in thread_analyses:
            filename = f"{analysis['thread_id']}_{analysis['subject'][:30]}.md"
            # Sanitize filename
            filename = re.sub(r'[^\w\s-]', '', filename)
            
            filepath = self.threads_dir / filename
            md_content = self.generate_email_markdown(analysis)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
        
        # Export summary
        summary_path = self.summaries_dir / f"email_summary_{timestamp}.md"
        summary_md = self.generate_summary_markdown(thread_analyses)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_md)
        
        # Export insights
        insights_path = self.insights_dir / f"communication_insights_{timestamp}.md"
        insights_md = self.generate_insights_markdown(thread_analyses)
        
        with open(insights_path, 'w', encoding='utf-8') as f:
            f.write(insights_md)
        
        logger.info(f"Exported {len(thread_analyses)} thread analyses to {self.output_dir}")
        
        return {
            'threads': len(thread_analyses),
            'summary': summary_path,
            'insights': insights_path
        }
    
    def generate_insights_markdown(self, analyses: List[Dict[str, Any]]) -> str:
        """Generate detailed insights about communication patterns"""
        md = f"""# Communication Insights & Patterns

*Generated on {datetime.now().strftime('%B %d, %Y')}*

## Mind Mapping: What You've Been Dealing With

"""
        
        # Group by time periods
        recent = datetime.now() - timedelta(days=30)
        recent_threads = [a for a in analyses if datetime.fromisoformat(a['last_email']) > recent]
        
        md += f"### Last 30 Days Focus Areas\n"
        
        if recent_threads:
            recent_categories = Counter()
            for thread in recent_threads:
                recent_categories[thread['subject_matter']['primary_category']] += 1
            
            for category, count in recent_categories.most_common(5):
                md += f"- **{category.title()}**: {count} threads\n"
        
        # Stress indicators over time
        md += f"\n## Stress & Workload Indicators\n\n"
        
        # Group by month
        monthly_moods = defaultdict(lambda: {'total': 0, 'stressed': 0, 'urgent': 0})
        
        for analysis in analyses:
            month_key = datetime.fromisoformat(analysis['first_email']).strftime('%Y-%m')
            monthly_moods[month_key]['total'] += 1
            
            if analysis['overall_mood']['dominant_mood'] in ['stressed', 'negative']:
                monthly_moods[month_key]['stressed'] += 1
            if analysis['overall_mood']['dominant_mood'] == 'urgent':
                monthly_moods[month_key]['urgent'] += 1
        
        md += "### Monthly Stress Levels\n"
        for month in sorted(monthly_moods.keys(), reverse=True)[:12]:
            data = monthly_moods[month]
            stress_pct = (data['stressed'] / data['total']) * 100 if data['total'] > 0 else 0
            month_date = datetime.strptime(month, '%Y-%m')
            
            md += f"- **{month_date.strftime('%B %Y')}**: "
            md += f"{stress_pct:.0f}% stressed/negative communications "
            md += f"({data['stressed']}/{data['total']} threads)\n"
        
        # Communication network
        md += f"\n## Your Communication Network\n\n"
        
        # This would analyze participants but we'll keep it high-level for privacy
        md += f"- Total unique email threads: {len(analyses)}\n"
        md += f"- Active communication style: Quick responses and engagement\n"
        
        # Project and topic evolution
        md += f"\n## Topic Evolution Over Time\n\n"
        
        # Track how topics change over quarters
        quarterly_topics = defaultdict(Counter)
        
        for analysis in analyses:
            date = datetime.fromisoformat(analysis['first_email'])
            quarter = f"{date.year}-Q{(date.month-1)//3 + 1}"
            
            for category in analysis['subject_matter']['categories']:
                quarterly_topics[quarter][category] += 1
        
        for quarter in sorted(quarterly_topics.keys(), reverse=True)[:8]:
            md += f"### {quarter}\n"
            for topic, count in quarterly_topics[quarter].most_common(3):
                md += f"- {topic.title()}: {count} threads\n"
            md += "\n"
        
        return md
    
    def run(self, days_back: int = 730):
        """Run the complete email analysis"""
        logger.info("Starting email analysis...")
        
        try:
            # Connect to email
            self.connect()
            
            # Get emails
            sent_emails, thread_emails = self.get_sent_emails_and_threads(days_back)
            
            # Group thread emails by subject
            threads = defaultdict(list)
            for email in thread_emails:
                subject = email.get('subject', '')
                clean_subject = re.sub(r'^(Re:|Fwd:|Fw:)\s*', '', subject, flags=re.IGNORECASE).strip()
                if clean_subject:
                    threads[clean_subject.lower()].append(email)
            
            # Analyze each thread
            thread_analyses = []
            for thread_key, emails in threads.items():
                if len(emails) > 1:  # Only analyze actual threads
                    logger.info(f"Analyzing thread: {emails[0].get('subject', 'Unknown')}")
                    analysis = self.analyze_email_thread(emails)
                    thread_analyses.append(analysis)
            
            # Export results
            results = self.export_analysis(sent_emails, thread_analyses)
            
            logger.info(f"Analysis complete! Analyzed {results['threads']} email threads")
            logger.info(f"Results saved to: {self.output_dir}")
            
            return results
            
        finally:
            # Always disconnect
            self.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze email communication patterns")
    parser.add_argument('--days', type=int, default=730, help='Number of days to analyze (default: 730)')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run analyzer
    analyzer = EmailAnalyzer()
    analyzer.run(days_back=args.days)