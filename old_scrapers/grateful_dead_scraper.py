#!/usr/bin/env python3
"""
Grateful Dead Archive.org Scraper
Searches archive.org for Grateful Dead collection items and extracts metadata.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

import internetarchive as ia
from bs4 import BeautifulSoup
from tqdm import tqdm


def clean_html(text: Optional[str]) -> Optional[str]:
    """Clean HTML tags from text using BeautifulSoup."""
    if not text:
        return text
    
    if isinstance(text, list):
        return [clean_html(item) for item in text]
    
    try:
        soup = BeautifulSoup(str(text), 'html.parser')
        return soup.get_text().strip()
    except Exception:
        return str(text).strip()


def extract_metadata(item: ia.Item) -> Dict[str, Any]:
    """Extract metadata from an Internet Archive item."""
    metadata = {}
    
    try:
        # Get basic metadata
        metadata['identifier'] = item.identifier
        metadata['title'] = item.metadata.get('title', '')
        metadata['date'] = item.metadata.get('date', '')
        metadata['venue'] = item.metadata.get('venue', '')
        metadata['description'] = clean_html(item.metadata.get('description', ''))
        metadata['subject'] = item.metadata.get('subject', [])
        
        # Extract setlist (may be in different fields)
        setlist = item.metadata.get('setlist', '')
        if not setlist:
            setlist = item.metadata.get('tracklist', '')
        if not setlist:
            setlist = item.metadata.get('lineage', '')
        
        metadata['setlist'] = clean_html(setlist)
        
        # Add some additional useful fields
        metadata['creator'] = item.metadata.get('creator', '')
        metadata['collection'] = item.metadata.get('collection', [])
        metadata['mediatype'] = item.metadata.get('mediatype', '')
        metadata['year'] = item.metadata.get('year', '')
        metadata['source'] = item.metadata.get('source', '')
        metadata['uploader'] = item.metadata.get('uploader', '')
        metadata['downloads'] = item.metadata.get('downloads', 0)
        metadata['avg_rating'] = item.metadata.get('avg_rating', 0)
        metadata['num_reviews'] = item.metadata.get('num_reviews', 0)
        
    except Exception as e:
        print(f"Error extracting metadata for {item.identifier}: {e}")
        metadata['error'] = str(e)
    
    return metadata


def search_grateful_dead_items(max_items: Optional[int] = None) -> List[str]:
    """Search archive.org for Grateful Dead items."""
    print("Searching archive.org for Grateful Dead items...")
    
    # Search for items in the Grateful Dead collection
    search_query = 'collection:GratefulDead'
    
    try:
        # Get search results
        search_results = ia.search_items(search_query, sorts=['date desc'])
        
        # Convert to list and limit if specified
        items = list(search_results)
        if max_items:
            items = items[:max_items]
            
        print(f"Found {len(items)} items to process")
        return items
        
    except Exception as e:
        print(f"Error searching archive.org: {e}")
        return []


def main():
    """Main function to scrape Grateful Dead archive data."""
    # Create output directory
    output_dir = Path('/workspace/GratefulGPT_archive_dataset')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Output file
    output_file = output_dir / 'grateful_dead_archive.jsonl'
    
    # Search for items (limit to 100 for testing, remove limit for full scrape)
    # items = search_grateful_dead_items(100)  # For testing
    items = search_grateful_dead_items()  # For full scrape
    
    if not items:
        print("No items found. Exiting.")
        return
    
    # Process items with progress bar
    processed_count = 0
    error_count = 0
    
    print(f"Starting to process {len(items)} items...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for item_id in tqdm(items, desc="Processing items", unit="item"):
            try:
                # Get item details
                item = ia.get_item(item_id)
                
                # Extract metadata
                metadata = extract_metadata(item)
                
                # Write to JSONL file
                f.write(json.dumps(metadata, ensure_ascii=False) + '\n')
                f.flush()  # Ensure data is written immediately
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                tqdm.write(f"Error processing item {item_id}: {e}")
                continue
    
    print(f"\nScraping completed!")
    print(f"Processed: {processed_count} items")
    print(f"Errors: {error_count} items")
    print(f"Output saved to: {output_file}")
    
    # Show sample of data
    if processed_count > 0:
        print("\nSample of extracted data:")
        with open(output_file, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= 3:  # Show first 3 items
                    break
                data = json.loads(line)
                print(f"  {i+1}. {data.get('title', 'No title')} ({data.get('date', 'No date')})")


if __name__ == "__main__":
    main()