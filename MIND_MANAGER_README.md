# Mind Manager - Unified Knowledge Integration

The Mind Manager extends ScrAInshots to create a unified timeline that integrates multiple data sources:
- Screenshots (existing functionality)
- MacOS Notes
- Outlook Emails
- Fireflies.ai Meeting Transcripts

## Features

### 1. Multi-Source Timeline
- **Unified View**: All your digital artifacts in one chronological timeline
- **Smart Grouping**: Automatically groups related items from the same time period
- **Cross-Referencing**: Identifies connections between notes, emails, meetings, and screenshots

### 2. Concept Extraction
- **AI-Powered Analysis**: Extracts key concepts, topics, and entities from all content
- **Automatic Categorization**: Classifies items into categories (Project, Meeting, Task, etc.)
- **Concept Clustering**: Groups related concepts across different sources

### 3. Time-Based Intelligence
- **Meeting Context**: Links screenshots to meetings happening at the same time
- **Email Threads**: Connects related emails and their associated content
- **Note Evolution**: Tracks how ideas develop across different notes over time

## Setup

### Prerequisites

1. **MacOS Notes Integration**
   ```bash
   # Install macnotesapp
   pip install macnotesapp
   # Or with the project
   pnpm setup  # This now includes macnotesapp
   ```

2. **Outlook Integration**
   - Register an app in Azure AD
   - Set environment variables:
   ```bash
   export OUTLOOK_CLIENT_ID="your-client-id"
   export OUTLOOK_CLIENT_SECRET="your-client-secret"  
   export OUTLOOK_TENANT_ID="your-tenant-id"
   ```

3. **Fireflies.ai Integration**
   - Get your API key from Fireflies settings
   - Set environment variable:
   ```bash
   export FIREFLIES_API_KEY="your-api-key"
   ```

### Configuration

Create a `.env` file in the project root:

```env
# Outlook Configuration
OUTLOOK_CLIENT_ID=your-client-id
OUTLOOK_CLIENT_SECRET=your-client-secret
OUTLOOK_TENANT_ID=your-tenant-id

# Fireflies Configuration
FIREFLIES_API_KEY=your-api-key

# Screenshot Directory (optional, defaults to ~/Desktop/screenshots)
SCREENSHOT_DIR=/path/to/screenshots
```

## Usage

### Command Line

```python
from mind_manager import MindManager
from datetime import datetime, timedelta

# Initialize the manager
manager = MindManager()
manager.initialize_integrations()

# Fetch data from the last 7 days
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

# Fetch and analyze
items = manager.fetch_all_data(start_date, end_date)
analysis = manager.analyze_timeline()

# View results
print(f"Found {len(items)} items across all sources")
print(f"Top concepts: {analysis['top_concepts'][:5]}")

# Save analysis
manager.save_analysis("mind_analysis.json")
```

### Web Interface

The Mind Manager is integrated into the existing web interface:

1. Start the application:
   ```bash
   pnpm dev
   ```

2. Navigate to the Timeline view to see unified data

3. Use filters to view specific sources or categories

4. Click on concepts to see related items

## Data Sources

### MacOS Notes
- Automatically syncs with your Notes app
- Extracts content, creation date, and modification date
- Preserves folder structure and categories

### Outlook Emails
- Fetches both sent and received emails
- Special handling for Fireflies meeting notifications
- Extracts participants, subjects, and content

### Fireflies Meetings
- Retrieves full meeting transcripts
- Includes participant information
- Extracts action items and key decisions
- Links to original meeting recordings

### Screenshots
- Existing screenshot analysis functionality
- Now integrated into the unified timeline
- Cross-referenced with other activities

## Concept Analysis

The system performs several types of analysis:

### 1. Concept Extraction
- Identifies key terms, project names, and entities
- Uses frequency analysis and AI to determine importance
- Tracks concept evolution over time

### 2. Relationship Mapping
- Finds connections between different items
- Groups items from the same time period
- Identifies recurring themes and topics

### 3. Importance Scoring
- Calculates relevance based on multiple factors
- Considers source type, content length, and connections
- Helps prioritize what to review

## Privacy and Security

- All data processing happens locally
- Credentials are stored in environment variables
- No data is sent to external services except configured APIs
- MacOS Notes access requires user permission

## Troubleshooting

### MacOS Notes Not Working
- Ensure macnotesapp is installed: `pip install macnotesapp`
- Grant terminal access to Notes in System Preferences
- Try running `notes list` in terminal to test

### Outlook Authentication
- Ensure app is registered in Azure AD with correct permissions
- Check that redirect URI matches your configuration
- Verify Mail.Read and User.Read permissions are granted

### Fireflies Connection
- Verify API key is correct
- Check subscription level (some features require Pro/Business)
- Ensure date ranges contain meetings

## Future Enhancements

- Slack integration
- Google Calendar events
- Browser history correlation
- Automatic report generation
- Natural language queries
- Export to mind mapping tools