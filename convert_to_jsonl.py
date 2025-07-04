#!/usr/bin/env python3
"""
Convert GratefulGPT GitHub dataset to JSONL format for Axolotl training
"""

import json
import re
from pathlib import Path
from typing import List, Dict

def chunk_text(text: str, max_length: int = 1500) -> List[str]:
    """Split text into chunks of approximately max_length characters"""
    # Split on double newlines first (paragraph breaks)
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed max_length, start a new chunk
        if len(current_chunk) + len(paragraph) + 2 > max_length:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add the last chunk if it's not empty
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

def process_git_dataset(input_file: str, output_file: str):
    """Convert the raw GitHub dataset to JSONL format"""
    
    print(f"Processing {input_file}...")
    
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into entries by looking for the pattern [repo_name] :: [file_path]
    entries = re.split(r'\n(?=\[.+?\] :: \[.+?\]\n)', content)
    
    total_entries = 0
    processed_entries = 0
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in entries:
            if not entry.strip():
                continue
                
            total_entries += 1
            
            # Extract header and content
            lines = entry.strip().split('\n')
            if len(lines) < 2:
                continue
                
            header = lines[0]
            content_text = '\n'.join(lines[1:])
            
            # Skip very short entries
            if len(content_text) < 100:
                continue
            
            # Parse the header to extract repo and file info
            header_match = re.match(r'\[(.+?)\] :: \[(.+?)\]', header)
            if not header_match:
                continue
                
            repo_name = header_match.group(1)
            file_path = header_match.group(2)
            
            # Chunk the content if it's too long
            chunks = chunk_text(content_text)
            
            for i, chunk in enumerate(chunks):
                # Create a training example
                if len(chunks) > 1:
                    prompt = f"The following is content from {file_path} in the {repo_name} repository (part {i+1} of {len(chunks)}):\n\n"
                else:
                    prompt = f"The following is content from {file_path} in the {repo_name} repository:\n\n"
                
                # Create the completion training format
                training_example = {
                    "text": prompt + chunk
                }
                
                # Write to JSONL
                f.write(json.dumps(training_example, ensure_ascii=False) + '\n')
                processed_entries += 1
    
    print(f"Processed {total_entries} raw entries into {processed_entries} training examples")
    print(f"Output saved to: {output_file}")

def main():
    input_file = "/workspace/data/GratefulGPT_git_dataset.txt"
    output_file = "/workspace/data/gratefulgpt_dataset.jsonl"
    
    # Create output directory if it doesn't exist
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    process_git_dataset(input_file, output_file)

if __name__ == "__main__":
    main()