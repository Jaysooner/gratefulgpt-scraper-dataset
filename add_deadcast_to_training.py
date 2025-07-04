#!/usr/bin/env python3
"""
Add Deadcast transcripts to the GratefulGPT training dataset
"""

import json
import re
from pathlib import Path

def process_deadcast_transcripts(input_file: str, output_file: str):
    """Process Deadcast transcripts and add to existing JSONL training dataset"""
    
    print(f"Processing Deadcast transcripts from {input_file}...")
    
    # Read the deadcast transcripts
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into episodes by the separator
    episodes = content.split('================================================================================')
    
    new_entries = 0
    
    # Append to existing JSONL file
    with open(output_file, 'a', encoding='utf-8') as f:
        for episode in episodes:
            episode = episode.strip()
            if not episode or len(episode) < 100:
                continue
                
            # Extract episode info
            lines = episode.split('\n')
            episode_title = None
            url = None
            word_count = None
            episode_content = []
            
            for i, line in enumerate(lines):
                if line.startswith('EPISODE '):
                    episode_title = line
                elif line.startswith('URL: '):
                    url = line.replace('URL: ', '')
                elif line.startswith('Word Count: '):
                    word_count = line.replace('Word Count: ', '')
                elif i > 5:  # Content starts after the metadata
                    episode_content.append(line)
            
            if not episode_title or not episode_content:
                continue
                
            # Clean content
            content_text = '\n'.join(episode_content).strip()
            
            # Skip very short episodes (likely just comments)
            if len(content_text) < 200:
                continue
            
            # Create training example
            prompt = f"The following is from the official Grateful Dead podcast 'Deadcast' - {episode_title.strip()}:\n\n"
            
            training_example = {
                "text": prompt + content_text
            }
            
            # Write to JSONL
            f.write(json.dumps(training_example, ensure_ascii=False) + '\n')
            new_entries += 1
    
    print(f"Added {new_entries} Deadcast episodes to training dataset")
    print(f"Updated dataset saved to: {output_file}")

def main():
    input_file = "/workspace/data/GratefulGPT_archive_dataset/deadcast_transcripts.txt"
    output_file = "/workspace/data/gratefulgpt_dataset.jsonl"
    
    # Check if files exist
    if not Path(input_file).exists():
        print(f"Error: {input_file} not found")
        return
        
    if not Path(output_file).exists():
        print(f"Error: {output_file} not found")
        return
    
    # Get original count
    with open(output_file, 'r') as f:
        original_count = sum(1 for line in f)
    
    print(f"Original dataset has {original_count} examples")
    
    process_deadcast_transcripts(input_file, output_file)
    
    # Get new count
    with open(output_file, 'r') as f:
        new_count = sum(1 for line in f)
    
    print(f"Enhanced dataset now has {new_count} examples (+{new_count - original_count})")

if __name__ == "__main__":
    main()