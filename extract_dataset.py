#!/usr/bin/env python3
"""
Extract GratefulGPT training dataset from Arrow format to JSONL
"""

import pandas as pd
import json
import os
from pathlib import Path

def extract_dataset():
    """Extract the 8,000 conversation dataset from Arrow format to JSONL"""
    
    # Path to the Arrow dataset
    arrow_path = "/workspace/data/huggingface-cache/datasets/json/default-1205c161578c9c7a/0.0.0/f4e89e8750d5d5ffbef2c078bf0ddfedef29dc2faff52a6255cf513c05eb1092/json-train.arrow"
    
    if not os.path.exists(arrow_path):
        print(f"Arrow file not found at {arrow_path}")
        return
    
    print(f"Loading dataset from {arrow_path}")
    
    # Load the Arrow file using datasets library
    try:
        from datasets import Dataset
        dataset = Dataset.from_file(arrow_path)
        print(f"Dataset loaded successfully: {len(dataset)} examples")
        
        # Convert to pandas for easier manipulation
        df = dataset.to_pandas()
    except ImportError:
        print("datasets library not found, trying pyarrow directly")
        import pyarrow as pa
        with pa.memory_map(arrow_path, 'r') as source:
            batch_reader = pa.ipc.RecordBatchFileReader(source)
            table = batch_reader.read_all()
            df = table.to_pandas()
    
    print(f"Dataset shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Display first few rows to understand structure
    print("\nFirst few rows:")
    print(df.head())
    
    # Extract conversations and convert to JSONL
    output_file = "/workspace/data/gratefulgpt_training_dataset.jsonl"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for idx, row in df.iterrows():
            # Extract conversation data
            if 'conversations' in row:
                conversations = row['conversations']
                
                # Convert numpy array to list if needed
                if hasattr(conversations, 'tolist'):
                    conversations = conversations.tolist()
                
                # Create training example
                training_example = {
                    "conversations": conversations,
                    "id": f"gratefulgpt_{idx:05d}"
                }
                
                # Write to JSONL
                f.write(json.dumps(training_example, ensure_ascii=False) + '\n')
            else:
                # If different structure, adapt accordingly
                training_example = {}
                for key, value in row.items():
                    if hasattr(value, 'tolist'):
                        training_example[key] = value.tolist()
                    else:
                        training_example[key] = value
                training_example["id"] = f"gratefulgpt_{idx:05d}"
                f.write(json.dumps(training_example, ensure_ascii=False) + '\n')
    
    print(f"\nDataset extracted to {output_file}")
    
    # Get file size
    file_size = os.path.getsize(output_file)
    print(f"Output file size: {file_size / (1024*1024):.2f} MB")
    
    # Count lines
    with open(output_file, 'r') as f:
        line_count = sum(1 for _ in f)
    print(f"Total conversations: {line_count}")
    
    return output_file

if __name__ == "__main__":
    extract_dataset()