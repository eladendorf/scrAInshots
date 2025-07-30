#!/usr/bin/env python3
"""
Gemini Mind Processor - Processes MD files through Gemini to create dynamic mind maps and Gantt charts
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re
from collections import defaultdict
import google.generativeai as genai
from time import sleep

logger = logging.getLogger(__name__)


class GeminiMindProcessor:
    """Process markdown files through Gemini to create evolving mind maps and Gantt charts"""
    
    def __init__(self, api_key: str = None):
        # Initialize Gemini
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("Gemini API key required")
        
        genai.configure(api_key=self.api_key)
        
        # Use Gemini 2.0 Flash for large context processing
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        # Directories
        self.fireflies_dir = Path.home() / 'FirefliesMeetings'
        self.email_dir = Path.home() / 'EmailAnalysis'
        self.output_dir = Path.home() / 'MindMapEvolution'
        self.output_dir.mkdir(exist_ok=True)
        
        # Create output subdirectories
        self.mindmaps_dir = self.output_dir / 'mindmaps'
        self.gantt_dir = self.output_dir / 'gantt_charts'
        self.insights_dir = self.output_dir / 'insights'
        self.cumulative_dir = self.output_dir / 'cumulative'
        
        for dir in [self.mindmaps_dir, self.gantt_dir, self.insights_dir, self.cumulative_dir]:
            dir.mkdir(exist_ok=True)
        
        # Cumulative context storage
        self.cumulative_insights = {
            'people_network': {},
            'concept_evolution': {},
            'task_tracking': {},
            'project_timeline': {},
            'mental_state_progression': {}
        }
    
    def collect_md_files_by_month(self) -> Dict[str, List[Path]]:
        """Collect all MD files organized by month"""
        files_by_month = defaultdict(list)
        
        # Collect from both directories
        all_dirs = [
            self.fireflies_dir / 'meetings',
            self.fireflies_dir / 'summaries',
            self.fireflies_dir / 'action_items',
            self.email_dir / 'threads',
            self.email_dir / 'summaries',
            self.email_dir / 'insights'
        ]
        
        for dir_path in all_dirs:
            if not dir_path.exists():
                continue
                
            for md_file in dir_path.glob('*.md'):
                # Try to extract date from filename or content
                file_date = self._extract_date_from_file(md_file)
                if file_date:
                    month_key = file_date.strftime('%Y-%m')
                    files_by_month[month_key].append(md_file)
        
        return dict(sorted(files_by_month.items()))
    
    def _extract_date_from_file(self, file_path: Path) -> Optional[datetime]:
        """Extract date from filename or file content"""
        # Try filename first (YYYY-MM-DD pattern)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', file_path.stem)
        if date_match:
            try:
                return datetime.strptime(date_match.group(1), '%Y-%m-%d')
            except:
                pass
        
        # Try reading first few lines for date
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # Read first 1000 chars
                
                # Look for date patterns
                date_patterns = [
                    r'Date: (\w+ \d+, \d{4})',
                    r'(\d{4}-\d{2}-\d{2})',
                    r'Generated on (\w+ \d+, \d{4})'
                ]
                
                for pattern in date_patterns:
                    match = re.search(pattern, content)
                    if match:
                        try:
                            return datetime.strptime(match.group(1), '%B %d, %Y')
                        except:
                            try:
                                return datetime.strptime(match.group(1), '%Y-%m-%d')
                            except:
                                pass
        except:
            pass
        
        # Default to file modification time
        return datetime.fromtimestamp(file_path.stat().st_mtime)
    
    def create_monthly_batch(self, month: str, files: List[Path]) -> str:
        """Create a batch of content for a specific month"""
        batch_content = f"# Monthly Data Batch: {month}\n\n"
        batch_content += f"Total files: {len(files)}\n\n"
        
        # Group files by type
        meetings = []
        emails = []
        summaries = []
        action_items = []
        
        for file_path in files:
            if 'meetings' in str(file_path):
                meetings.append(file_path)
            elif 'threads' in str(file_path):
                emails.append(file_path)
            elif 'summaries' in str(file_path):
                summaries.append(file_path)
            elif 'action_items' in str(file_path):
                action_items.append(file_path)
        
        # Add files in logical order
        batch_content += "## Summary Files\n"
        for file_path in summaries:
            batch_content += f"\n### {file_path.name}\n"
            batch_content += file_path.read_text(encoding='utf-8')
            batch_content += "\n---\n"
        
        batch_content += "\n## Action Items\n"
        for file_path in action_items:
            batch_content += f"\n### {file_path.name}\n"
            batch_content += file_path.read_text(encoding='utf-8')
            batch_content += "\n---\n"
        
        batch_content += "\n## Meeting Details\n"
        for file_path in meetings[:10]:  # Limit to avoid context overflow
            batch_content += f"\n### {file_path.name}\n"
            content = file_path.read_text(encoding='utf-8')
            # Truncate very long transcripts
            if len(content) > 5000:
                content = content[:5000] + "\n\n[Transcript truncated...]"
            batch_content += content
            batch_content += "\n---\n"
        
        batch_content += "\n## Email Threads\n"
        for file_path in emails[:10]:  # Limit to avoid context overflow
            batch_content += f"\n### {file_path.name}\n"
            batch_content += file_path.read_text(encoding='utf-8')
            batch_content += "\n---\n"
        
        return batch_content
    
    def generate_mind_map_prompt(self, month: str, batch_content: str, 
                                previous_insights: Dict[str, Any]) -> str:
        """Generate a clever prompt for mind map creation"""
        
        prompt = f"""You are an expert at analyzing communication patterns and creating visual knowledge representations.

## Current Analysis Period: {month}

## Previous Insights Summary:
{json.dumps(previous_insights, indent=2) if previous_insights else "This is the first month being analyzed."}

## Current Month's Data:
{batch_content}

## Your Task:

Create a comprehensive analysis with the following deliverables:

### 1. DYNAMIC MIND MAP
Create a mind map structure showing:
- Central node: Key theme/focus for {month}
- Primary branches: Major projects, initiatives, or concerns
- Secondary branches: Related people, concepts, and tasks
- Use emoji indicators: 🔥 (urgent), ✅ (completed), 🚧 (in progress), ❌ (blocked), 💡 (ideas)
- Show connections between concepts with relationship labels

Format as a structured JSON that can be visualized:
```json
{{
  "central_theme": "...",
  "branches": [
    {{
      "name": "Project X",
      "status": "🚧",
      "sub_branches": [...],
      "connections": [...]
    }}
  ]
}}
```

### 2. GANTT CHART DATA
Extract and track all tasks/projects with:
- Task name and description
- Start date (actual or inferred)
- End date (actual or estimated)
- Status: completed, in_progress, blocked, no_action, open
- Dependencies on other tasks
- Assigned people

Format as structured data for Gantt visualization:
```json
{{
  "tasks": [
    {{
      "id": "task_1",
      "name": "...",
      "start": "YYYY-MM-DD",
      "end": "YYYY-MM-DD",
      "status": "in_progress",
      "dependencies": ["task_0"],
      "people": ["person1"],
      "category": "project_x"
    }}
  ]
}}
```

### 3. CROSS-CUTTING DIMENSIONS

#### People Network Over Time:
- Track who appears in communications
- Relationship strength (frequency of interaction)
- Collaboration patterns
- Key influencers/blockers

#### Concepts Evolution:
- How key concepts/projects evolve
- New concepts introduced
- Concepts that disappeared
- Concept relationships and clusters

### 4. MENTAL STATE & WORKLOAD TRACKING
- Overall stress level (1-10)
- Workload indicators
- Mood progression
- Energy patterns

### 5. ACTIONABLE INSIGHTS
- What needs immediate attention?
- What patterns are concerning?
- What's working well?
- Predictions for next month

### 6. CUMULATIVE UPDATE
Update these tracking objects with new information:
- people_network: Add/update people and interaction counts
- concept_evolution: Track concept lifecycle
- task_tracking: Update task statuses
- project_timeline: Major milestone tracking
- mental_state_progression: Monthly mood/stress data

Please provide a comprehensive analysis with all sections clearly labeled and formatted for programmatic parsing."""
        
        return prompt
    
    def process_month(self, month: str, files: List[Path], 
                     previous_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a single month's data through Gemini"""
        logger.info(f"Processing month: {month} with {len(files)} files")
        
        # Create batch content
        batch_content = self.create_monthly_batch(month, files)
        
        # Save batch for reference
        batch_path = self.cumulative_dir / f"batch_{month}.md"
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        # Generate prompt with previous insights
        previous_insights = {}
        if previous_results:
            previous_insights = {
                'people_network': previous_results.get('cumulative', {}).get('people_network', {}),
                'recent_concepts': previous_results.get('cumulative', {}).get('concept_evolution', {}),
                'ongoing_tasks': [t for t in previous_results.get('gantt', {}).get('tasks', []) 
                                 if t.get('status') != 'completed'],
                'mental_state_trend': previous_results.get('mental_state', {})
            }
        
        prompt = self.generate_mind_map_prompt(month, batch_content, previous_insights)
        
        # Call Gemini
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Parse the response
            parsed_result = self._parse_gemini_response(result_text, month)
            
            # Update cumulative insights
            self._update_cumulative_insights(parsed_result)
            
            # Save outputs
            self._save_month_outputs(month, parsed_result)
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error processing month {month}: {e}")
            return {
                'month': month,
                'error': str(e),
                'mindmap': {},
                'gantt': {},
                'insights': {}
            }
    
    def _parse_gemini_response(self, response_text: str, month: str) -> Dict[str, Any]:
        """Parse Gemini's response into structured data"""
        result = {
            'month': month,
            'mindmap': {},
            'gantt': {'tasks': []},
            'people_network': {},
            'concepts': {},
            'mental_state': {},
            'insights': {},
            'cumulative': {}
        }
        
        # Extract JSON blocks
        json_blocks = re.findall(r'```json\n(.*?)\n```', response_text, re.DOTALL)
        
        # Parse mind map (first JSON block)
        if json_blocks:
            try:
                result['mindmap'] = json.loads(json_blocks[0])
            except:
                logger.error("Failed to parse mind map JSON")
        
        # Parse Gantt data (second JSON block)
        if len(json_blocks) > 1:
            try:
                result['gantt'] = json.loads(json_blocks[1])
            except:
                logger.error("Failed to parse Gantt JSON")
        
        # Extract other sections using regex
        sections = {
            'People Network': 'people_network',
            'Concepts Evolution': 'concepts',
            'Mental State': 'mental_state',
            'Actionable Insights': 'insights',
            'Cumulative Update': 'cumulative'
        }
        
        for section_name, key in sections.items():
            pattern = rf"### {section_name}.*?\n(.*?)(?=###|\Z)"
            match = re.search(pattern, response_text, re.DOTALL)
            if match:
                content = match.group(1).strip()
                # Try to parse as JSON if it looks like JSON
                if content.startswith('{'):
                    try:
                        result[key] = json.loads(content)
                    except:
                        result[key] = {'text': content}
                else:
                    result[key] = {'text': content}
        
        return result
    
    def _update_cumulative_insights(self, monthly_result: Dict[str, Any]):
        """Update cumulative insights with monthly data"""
        # Update people network
        if 'people_network' in monthly_result:
            for person, data in monthly_result['people_network'].items():
                if person not in self.cumulative_insights['people_network']:
                    self.cumulative_insights['people_network'][person] = {
                        'first_seen': monthly_result['month'],
                        'interactions': 0,
                        'roles': set()
                    }
                
                if isinstance(data, dict):
                    self.cumulative_insights['people_network'][person]['interactions'] += data.get('interactions', 1)
                    if 'role' in data:
                        self.cumulative_insights['people_network'][person]['roles'].add(data['role'])
        
        # Update concept evolution
        if 'concepts' in monthly_result:
            month = monthly_result['month']
            for concept, data in monthly_result['concepts'].items():
                if concept not in self.cumulative_insights['concept_evolution']:
                    self.cumulative_insights['concept_evolution'][concept] = {
                        'first_seen': month,
                        'last_seen': month,
                        'frequency': {}
                    }
                
                self.cumulative_insights['concept_evolution'][concept]['last_seen'] = month
                self.cumulative_insights['concept_evolution'][concept]['frequency'][month] = \
                    data.get('count', 1) if isinstance(data, dict) else 1
        
        # Update task tracking
        if 'gantt' in monthly_result and 'tasks' in monthly_result['gantt']:
            for task in monthly_result['gantt']['tasks']:
                task_id = task.get('id', task.get('name', 'unknown'))
                self.cumulative_insights['task_tracking'][task_id] = {
                    'name': task.get('name'),
                    'status': task.get('status'),
                    'month': monthly_result['month'],
                    'people': task.get('people', [])
                }
    
    def _save_month_outputs(self, month: str, result: Dict[str, Any]):
        """Save monthly outputs in various formats"""
        # Save raw result
        result_path = self.cumulative_dir / f"result_{month}.json"
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)
        
        # Generate mind map visualization script
        mindmap_md = self._generate_mindmap_markdown(result['mindmap'], month)
        mindmap_path = self.mindmaps_dir / f"mindmap_{month}.md"
        with open(mindmap_path, 'w', encoding='utf-8') as f:
            f.write(mindmap_md)
        
        # Generate Gantt chart data
        gantt_md = self._generate_gantt_markdown(result['gantt'], month)
        gantt_path = self.gantt_dir / f"gantt_{month}.md"
        with open(gantt_path, 'w', encoding='utf-8') as f:
            f.write(gantt_md)
        
        # Save insights
        insights_md = self._generate_insights_markdown(result, month)
        insights_path = self.insights_dir / f"insights_{month}.md"
        with open(insights_path, 'w', encoding='utf-8') as f:
            f.write(insights_md)
    
    def _generate_mindmap_markdown(self, mindmap_data: Dict[str, Any], month: str) -> str:
        """Generate markdown representation of mind map"""
        md = f"# Mind Map - {month}\n\n"
        
        if not mindmap_data:
            return md + "No mind map data available.\n"
        
        # Mermaid diagram format for visualization
        md += "```mermaid\nmindmap\n"
        md += f"  root(({mindmap_data.get('central_theme', month)}))\n"
        
        for branch in mindmap_data.get('branches', []):
            md += f"    {branch.get('name', 'Unknown')} {branch.get('status', '')}\n"
            for sub in branch.get('sub_branches', []):
                md += f"      {sub}\n"
        
        md += "```\n\n"
        
        # Also create a hierarchical text version
        md += "## Hierarchical View\n\n"
        md += f"* **{mindmap_data.get('central_theme', month)}**\n"
        
        for branch in mindmap_data.get('branches', []):
            md += f"  * {branch.get('status', '')} **{branch.get('name', 'Unknown')}**\n"
            for sub in branch.get('sub_branches', []):
                md += f"    * {sub}\n"
            if branch.get('connections'):
                md += f"    * 🔗 Connections: {', '.join(branch['connections'])}\n"
        
        return md
    
    def _generate_gantt_markdown(self, gantt_data: Dict[str, Any], month: str) -> str:
        """Generate Gantt chart in markdown/mermaid format"""
        md = f"# Gantt Chart - {month}\n\n"
        
        tasks = gantt_data.get('tasks', [])
        if not tasks:
            return md + "No tasks found for this month.\n"
        
        # Mermaid Gantt chart
        md += "```mermaid\ngantt\n"
        md += f"    title Tasks and Projects - {month}\n"
        md += "    dateFormat YYYY-MM-DD\n\n"
        
        # Group by category
        categories = {}
        for task in tasks:
            cat = task.get('category', 'Other')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(task)
        
        for category, cat_tasks in categories.items():
            md += f"    section {category}\n"
            for task in cat_tasks:
                status_label = {
                    'completed': 'done',
                    'in_progress': 'active',
                    'blocked': 'crit',
                    'open': '',
                    'no_action': ''
                }.get(task.get('status', ''), '')
                
                task_line = f"    {task['name']}"
                if status_label:
                    task_line += f" :{status_label}"
                
                # Add task ID and dates
                task_line += f", {task.get('id', 'task')}, {task.get('start', month+'-01')}, {task.get('end', month+'-30')}"
                md += task_line + "\n"
        
        md += "```\n\n"
        
        # Task details table
        md += "## Task Details\n\n"
        md += "| Task | Status | People | Dependencies | Dates |\n"
        md += "|------|--------|---------|--------------|-------|\n"
        
        for task in tasks:
            people = ', '.join(task.get('people', []))
            deps = ', '.join(task.get('dependencies', []))
            dates = f"{task.get('start', 'TBD')} to {task.get('end', 'TBD')}"
            status_emoji = {
                'completed': '✅',
                'in_progress': '🚧',
                'blocked': '❌',
                'open': '📋',
                'no_action': '💤'
            }.get(task.get('status', 'open'), '❓')
            
            md += f"| {task['name']} | {status_emoji} {task.get('status', 'unknown')} | {people} | {deps} | {dates} |\n"
        
        return md
    
    def _generate_insights_markdown(self, result: Dict[str, Any], month: str) -> str:
        """Generate insights markdown"""
        md = f"# Monthly Insights - {month}\n\n"
        
        # Mental state
        if result.get('mental_state'):
            md += "## Mental State & Workload\n"
            if isinstance(result['mental_state'], dict):
                for key, value in result['mental_state'].items():
                    md += f"- **{key}**: {value}\n"
            else:
                md += str(result['mental_state']) + "\n"
            md += "\n"
        
        # Key insights
        if result.get('insights'):
            md += "## Key Insights\n"
            if isinstance(result['insights'], dict):
                for key, value in result['insights'].items():
                    md += f"\n### {key}\n{value}\n"
            else:
                md += str(result['insights']) + "\n"
            md += "\n"
        
        # People network
        if result.get('people_network'):
            md += "## People Network This Month\n"
            for person, data in result['people_network'].items():
                if isinstance(data, dict):
                    md += f"- **{person}**: {data.get('interactions', 'N/A')} interactions\n"
                else:
                    md += f"- **{person}**: {data}\n"
            md += "\n"
        
        # Concepts
        if result.get('concepts'):
            md += "## Key Concepts\n"
            for concept, data in result['concepts'].items():
                if isinstance(data, dict):
                    md += f"- **{concept}**: {data.get('frequency', 'N/A')} mentions\n"
                else:
                    md += f"- **{concept}**: {data}\n"
        
        return md
    
    def generate_evolution_report(self):
        """Generate a final evolution report showing changes over time"""
        md = f"# Mind Evolution Report\n\n"
        md += f"*Generated on {datetime.now().strftime('%B %d, %Y')}*\n\n"
        
        # People network evolution
        md += "## People Network Evolution\n\n"
        people_timeline = defaultdict(list)
        
        for person, data in self.cumulative_insights['people_network'].items():
            if isinstance(data, dict) and 'first_seen' in data:
                people_timeline[data['first_seen']].append(person)
        
        for month in sorted(people_timeline.keys()):
            md += f"- **{month}**: New connections: {', '.join(people_timeline[month])}\n"
        
        # Concept lifecycle
        md += "\n## Concept Lifecycle\n\n"
        
        # Find concepts that appeared and disappeared
        concept_data = self.cumulative_insights['concept_evolution']
        active_concepts = []
        completed_concepts = []
        
        current_month = datetime.now().strftime('%Y-%m')
        
        for concept, data in concept_data.items():
            if isinstance(data, dict):
                last_seen = data.get('last_seen', '')
                if last_seen == current_month:
                    active_concepts.append(concept)
                else:
                    completed_concepts.append((concept, last_seen))
        
        md += f"### Currently Active Concepts\n"
        for concept in active_concepts:
            md += f"- {concept}\n"
        
        md += f"\n### Completed/Dormant Concepts\n"
        for concept, last_seen in completed_concepts:
            md += f"- {concept} (last seen: {last_seen})\n"
        
        # Task evolution
        md += "\n## Task Status Evolution\n\n"
        
        task_stats = {'completed': 0, 'in_progress': 0, 'blocked': 0, 'open': 0}
        for task_id, task_data in self.cumulative_insights['task_tracking'].items():
            if isinstance(task_data, dict):
                status = task_data.get('status', 'unknown')
                if status in task_stats:
                    task_stats[status] += 1
        
        md += "### Overall Task Statistics\n"
        for status, count in task_stats.items():
            md += f"- {status.replace('_', ' ').title()}: {count}\n"
        
        # Save evolution report
        evolution_path = self.output_dir / "evolution_report.md"
        with open(evolution_path, 'w', encoding='utf-8') as f:
            f.write(md)
        
        return evolution_path
    
    def run(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        """Run the complete processing pipeline"""
        logger.info("Starting Gemini mind processing...")
        
        # Collect files by month
        files_by_month = self.collect_md_files_by_month()
        logger.info(f"Found files for {len(files_by_month)} months")
        
        # Filter by date range if specified
        if start_date or end_date:
            filtered_months = {}
            for month, files in files_by_month.items():
                month_date = datetime.strptime(month + '-01', '%Y-%m-%d')
                if (not start_date or month_date >= start_date) and \
                   (not end_date or month_date <= end_date):
                    filtered_months[month] = files
            files_by_month = filtered_months
        
        # Process each month sequentially
        previous_results = None
        all_results = {}
        
        for month, files in files_by_month.items():
            logger.info(f"\nProcessing month: {month}")
            
            # Process month with cumulative context
            result = self.process_month(month, files, previous_results)
            all_results[month] = result
            previous_results = result
            
            # Rate limiting for API
            sleep(2)
        
        # Generate final evolution report
        evolution_path = self.generate_evolution_report()
        logger.info(f"\nEvolution report saved to: {evolution_path}")
        
        # Create visualization index
        self._create_visualization_index(all_results)
        
        logger.info(f"\nProcessing complete! All outputs saved to: {self.output_dir}")
        
        return all_results
    
    def _create_visualization_index(self, all_results: Dict[str, Any]):
        """Create an index file for all visualizations"""
        index_path = self.output_dir / "README.md"
        
        md = f"# Mind Map Evolution Visualizations\n\n"
        md += f"*Generated on {datetime.now().strftime('%B %d, %Y')}*\n\n"
        
        md += "## Monthly Visualizations\n\n"
        
        for month in sorted(all_results.keys()):
            md += f"### {month}\n"
            md += f"- [Mind Map](mindmaps/mindmap_{month}.md)\n"
            md += f"- [Gantt Chart](gantt_charts/gantt_{month}.md)\n"
            md += f"- [Insights](insights/insights_{month}.md)\n"
            md += f"- [Raw Data](cumulative/result_{month}.json)\n\n"
        
        md += "## Overall Reports\n"
        md += "- [Evolution Report](evolution_report.md)\n"
        md += "- [Cumulative Insights](cumulative/)\n"
        
        md += "\n## Visualization Instructions\n"
        md += "The mind maps and Gantt charts are formatted in Mermaid syntax.\n"
        md += "To visualize them:\n"
        md += "1. Use a Markdown viewer that supports Mermaid (e.g., GitHub, VSCode with extension)\n"
        md += "2. Copy the Mermaid code blocks to [Mermaid Live Editor](https://mermaid.live)\n"
        md += "3. Use tools like Obsidian or Notion that render Mermaid diagrams\n"
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(md)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Process MD files through Gemini for mind mapping")
    parser.add_argument('--api-key', help='Gemini API key (or set GEMINI_API_KEY env var)')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse dates
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d') if args.start_date else None
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d') if args.end_date else None
    
    # Run processor
    processor = GeminiMindProcessor(api_key=args.api_key)
    processor.run(start_date, end_date)