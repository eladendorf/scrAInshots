#!/usr/bin/env python3
"""
Test script for Mind Manager with Fireflies integration
"""
import os
from datetime import datetime, timedelta
from mind_manager import MindManager
import json

# Set the Fireflies API key
os.environ['FIREFLIES_API_KEY'] = 'a781cdb8-26a6-49fd-be05-9ce2a0f9e4cc'

def test_fireflies_integration():
    """Test Fireflies integration"""
    print("Testing Fireflies integration...")
    
    from integrations.fireflies_integration import FirefliesIntegration
    
    fireflies = FirefliesIntegration()
    
    # Get transcripts from the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    try:
        transcripts = fireflies.get_transcripts(start_date, end_date, limit=10)
        print(f"\nFound {len(transcripts)} Fireflies meetings")
        
        for transcript in transcripts[:3]:  # Show first 3
            print(f"\n- Meeting: {transcript.get('title', 'Untitled')}")
            print(f"  Date: {transcript.get('date', 'Unknown')}")
            print(f"  Duration: {transcript.get('duration', 0) / 60:.1f} minutes")
            if transcript.get('participants'):
                print(f"  Participants: {', '.join(transcript['participants'][:3])}...")
            
            summary = transcript.get('summary', {})
            if summary.get('keywords'):
                print(f"  Keywords: {', '.join(summary['keywords'][:5])}")
        
        return True
    except Exception as e:
        print(f"Error testing Fireflies: {e}")
        return False

def test_mind_manager():
    """Test the full Mind Manager integration"""
    print("\n\nTesting Mind Manager...")
    
    # Initialize Mind Manager
    manager = MindManager()
    manager.initialize_integrations()
    
    # Fetch data from the last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print(f"\nFetching data from {start_date.date()} to {end_date.date()}...")
    
    # Fetch all data
    items = manager.fetch_all_data(start_date, end_date)
    print(f"\nTotal items found: {len(items)}")
    
    # Show breakdown by source
    source_counts = {}
    for item in items:
        source_counts[item.source_type.value] = source_counts.get(item.source_type.value, 0) + 1
    
    print("\nBreakdown by source:")
    for source, count in source_counts.items():
        print(f"  - {source}: {count} items")
    
    # Analyze timeline
    print("\nAnalyzing timeline...")
    analysis = manager.analyze_timeline()
    
    print("\nAnalysis results:")
    print(f"  - Timeline items: {analysis['timeline_items']}")
    print(f"  - Concept clusters: {analysis['concept_clusters']}")
    print(f"  - Time windows: {analysis['time_windows']}")
    
    # Show top concepts
    print("\nTop concepts:")
    for concept_info in analysis['top_concepts'][:10]:
        print(f"  - {concept_info['concept']}: {concept_info['frequency']} occurrences")
    
    # Save analysis
    output_file = "mind_manager_test_results.json"
    manager.save_analysis(output_file)
    print(f"\nFull analysis saved to: {output_file}")
    
    # Show sample timeline items
    print("\n\nSample timeline items:")
    timeline_display = manager.get_timeline_for_display()
    
    for item in timeline_display[:5]:
        print(f"\n{'-' * 50}")
        print(f"Source: {item['source_type']}")
        print(f"Title: {item['title']}")
        print(f"Time: {item['timestamp']}")
        if item.get('extracted_concepts'):
            print(f"Concepts: {', '.join(item['extracted_concepts'][:5])}")
        if item.get('summary'):
            print(f"Summary: {item['summary'][:100]}...")

if __name__ == "__main__":
    print("=" * 60)
    print("Mind Manager Test Script")
    print("=" * 60)
    
    # Test Fireflies first
    fireflies_ok = test_fireflies_integration()
    
    if fireflies_ok:
        # Test full Mind Manager
        test_mind_manager()
    else:
        print("\nSkipping Mind Manager test due to Fireflies error")
        print("You may need to check your API key or network connection")