#!/usr/bin/env python3
"""
Consolidate Deadcast transcripts into training dataset format
"""
import json
import os

def consolidate_transcripts():
    """Convert JSONL transcripts to consolidated text format"""
    
    jsonl_file = "/workspace/GratefulGPT_archive_dataset/deadcast_transcripts.jsonl"
    txt_file = "/workspace/GratefulGPT_archive_dataset/deadcast_transcripts.txt"
    
    if not os.path.exists(jsonl_file):
        print("No transcript file found")
        return
    
    transcripts = []
    
    # Read all transcripts
    with open(jsonl_file, 'r', encoding='utf-8') as f:
        for line in f:
            transcript = json.loads(line.strip())
            transcripts.append(transcript)
    
    print(f"Found {len(transcripts)} transcripts")
    
    # Sort by title for consistent ordering
    transcripts.sort(key=lambda x: x.get('title', ''))
    
    # Create consolidated text file
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("=== GRATEFUL DEAD DEADCAST TRANSCRIPTS ===\n\n")
        f.write("Source: https://www.dead.net/deadcast-index\n")
        f.write("Description: Official Grateful Dead podcast transcripts\n")
        f.write("Scraped: 2025-07-04\n\n")
        f.write("="*80 + "\n\n")
        
        for i, transcript in enumerate(transcripts, 1):
            # Header
            f.write(f"EPISODE {i}: {transcript['title']}\n")
            f.write(f"URL: {transcript['url']}\n")
            if transcript.get('date'):
                f.write(f"Date: {transcript['date']}\n")
            f.write(f"Word Count: {transcript.get('word_count', 0)}\n\n")
            
            # Content
            f.write(transcript['transcript'])
            f.write("\n\n" + "="*80 + "\n\n")
    
    # Calculate stats
    total_words = sum(t.get('word_count', 0) for t in transcripts)
    
    print(f"Consolidated {len(transcripts)} transcripts")
    print(f"Total words: {total_words:,}")
    print(f"Output file: {txt_file}")

if __name__ == "__main__":
    consolidate_transcripts()