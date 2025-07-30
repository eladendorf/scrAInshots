#!/usr/bin/env python3
"""Verify that MD files are properly indexed in the ChromaDB database"""

from database_manager import ScreenshotDatabase
from pathlib import Path
import json

def verify_database():
    db = ScreenshotDatabase()
    
    # Get all documents
    all_docs = db.get_all()
    
    print(f"Total documents in database: {len(all_docs)}")
    
    if all_docs:
        # Show first document as example
        print("\nExample document:")
        doc = all_docs[0]
        print(f"ID: {doc['id']}")
        print(f"Metadata: {json.dumps(doc['metadata'], indent=2)}")
        print(f"Content preview: {doc['content'][:200]}...")
        
        # Test search functionality
        print("\n\nTesting search functionality...")
        test_query = "screenshot"
        results = db.search(test_query, n_results=3)
        print(f"Search results for '{test_query}': {len(results)} documents found")
        
        if results:
            print(f"First result distance: {results[0].get('distance', 'N/A')}")
            
        # Test specific word search
        print("\n\nTesting word-based search...")
        # Extract a word from first document content
        if all_docs:
            words = all_docs[0]['content'].split()
            # Find a meaningful word (not a common word)
            test_word = None
            for word in words:
                if len(word) > 5 and word.isalpha():
                    test_word = word.lower()
                    break
            
            if test_word:
                print(f"Searching for word: '{test_word}'")
                word_results = db.search(test_word, n_results=5)
                print(f"Found {len(word_results)} documents containing '{test_word}'")
    else:
        print("\nNo documents found in database. Please run the screenshot processor first.")

if __name__ == "__main__":
    verify_database()