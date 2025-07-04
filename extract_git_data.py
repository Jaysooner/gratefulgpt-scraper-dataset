#!/usr/bin/env python3
"""
GitHub Repository Data Extractor for GratefulGPT Training
Extracts and cleans text content from cloned repositories
"""

import os
import json
import csv
from pathlib import Path
from typing import Set, List, Dict, Optional
import logging
import re

# Try to import yaml, make it optional
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/extract_git_data.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
INPUT_DIR = "/workspace/GratefulGPT_git_data"
OUTPUT_FILE = "/workspace/GratefulGPT_git_dataset.txt"

# File extensions to process
ALLOWED_EXTENSIONS = {'.md', '.txt', '.csv', '.json', '.yaml', '.yml'}

# Files to ignore (case-insensitive)
IGNORE_FILES = {
    'license', 'license.txt', 'license.md',
    '.gitignore', '.gitattributes',
    'package-lock.json', 'yarn.lock',
    'requirements.txt'  # Common but not usually content-rich
}

# Extensions to completely ignore
IGNORE_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
    '.wav', '.mp3', '.flac', '.ogg', '.m4a',
    '.exe', '.dll', '.so', '.dylib',
    '.class', '.jar', '.war'
}

class GitDataExtractor:
    def __init__(self, input_dir: str, output_file: str):
        self.input_dir = Path(input_dir)
        self.output_file = Path(output_file)
        self.stats = {
            'repos_processed': 0,
            'files_processed': 0,
            'files_skipped': 0,
            'errors': 0
        }
        
    def clean_content(self, content: str, file_extension: str) -> str:
        """Clean and normalize content"""
        if not content.strip():
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)
        
        # For markdown files, remove some common noise
        if file_extension == '.md':
            # Remove badge lines (shields.io, etc.)
            content = re.sub(r'^\s*\[!\[.*?\]\(.*?\)\]\(.*?\)\s*$', '', content, flags=re.MULTILINE)
            # Remove HTML comments
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        return content.strip()
    
    def process_json_file(self, file_path: Path) -> Optional[str]:
        """Process JSON files with special handling"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
            
            # If it's a structured data file, format it nicely
            if isinstance(data, dict):
                # Check if it looks like meaningful data
                if any(key in str(data).lower() for key in ['grateful', 'dead', 'setlist', 'song', 'show', 'date', 'venue']):
                    return json.dumps(data, indent=2, ensure_ascii=False)
                else:
                    # Skip configuration files
                    return None
            elif isinstance(data, list) and len(data) > 0:
                # Check if it's a list of meaningful objects
                first_item = data[0] if data else {}
                if isinstance(first_item, dict) and any(key in str(first_item).lower() for key in ['grateful', 'dead', 'setlist', 'song', 'show', 'date', 'venue']):
                    return json.dumps(data, indent=2, ensure_ascii=False)
                else:
                    return None
            else:
                return None
                
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to parse JSON file {file_path}: {e}")
            return None
    
    def process_csv_file(self, file_path: Path) -> Optional[str]:
        """Process CSV files"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # Read first few lines to check if it's meaningful
                sample = f.read(1000)
                if not any(keyword in sample.lower() for keyword in ['grateful', 'dead', 'setlist', 'song', 'show', 'date', 'venue']):
                    return None
                
                # Reset file pointer
                f.seek(0)
                
                # Try to parse as CSV
                try:
                    reader = csv.reader(f)
                    rows = list(reader)
                    
                    if len(rows) > 1:  # Has header and data
                        # Format as readable text
                        result = []
                        headers = rows[0]
                        for row in rows[1:]:
                            if len(row) == len(headers):
                                row_data = dict(zip(headers, row))
                                result.append(json.dumps(row_data, ensure_ascii=False))
                        
                        return '\n'.join(result)
                    else:
                        return None
                        
                except csv.Error:
                    # If CSV parsing fails, treat as regular text
                    f.seek(0)
                    return f.read()
                    
        except (UnicodeDecodeError, Exception) as e:
            logger.warning(f"Failed to process CSV file {file_path}: {e}")
            return None
    
    def process_yaml_file(self, file_path: Path) -> Optional[str]:
        """Process YAML files"""
        if not YAML_AVAILABLE:
            # Treat as regular text file if YAML not available
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                return content if content.strip() else None
            except UnicodeDecodeError:
                return None
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = yaml.safe_load(f)
            
            if data and isinstance(data, (dict, list)):
                # Check if it contains meaningful data
                data_str = str(data).lower()
                if any(keyword in data_str for keyword in ['grateful', 'dead', 'setlist', 'song', 'show', 'date', 'venue']):
                    return yaml.dump(data, default_flow_style=False, allow_unicode=True)
                else:
                    return None
            else:
                return None
                
        except (yaml.YAMLError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to parse YAML file {file_path}: {e}")
            return None
    
    def process_file(self, file_path: Path, repo_name: str) -> Optional[str]:
        """Process a single file and return formatted content"""
        try:
            file_extension = file_path.suffix.lower()
            relative_path = file_path.relative_to(self.input_dir / repo_name)
            
            # Skip ignored files
            if file_path.name.lower() in IGNORE_FILES:
                return None
                
            # Skip ignored extensions
            if file_extension in IGNORE_EXTENSIONS:
                return None
            
            # Process based on file type
            if file_extension == '.json':
                content = self.process_json_file(file_path)
            elif file_extension == '.csv':
                content = self.process_csv_file(file_path)
            elif file_extension in {'.yaml', '.yml'}:
                content = self.process_yaml_file(file_path)
            else:
                # Regular text files
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                        content = f.read()
            
            if not content:
                return None
                
            # Clean content
            clean_content = self.clean_content(content, file_extension)
            
            if not clean_content or len(clean_content) < 50:  # Skip very short files
                return None
            
            # Format with header
            header = f"[{repo_name}] :: [{relative_path}]"
            formatted_content = f"{header}\n{clean_content}\n"
            
            return formatted_content
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            self.stats['errors'] += 1
            return None
    
    def extract_repo_data(self, repo_path: Path) -> List[str]:
        """Extract all relevant data from a repository"""
        repo_name = repo_path.name
        extracted_contents = []
        
        logger.info(f"Processing repository: {repo_name}")
        
        # Walk through all files in the repository
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                file_extension = file_path.suffix.lower()
                
                if file_extension in ALLOWED_EXTENSIONS:
                    content = self.process_file(file_path, repo_name)
                    if content:
                        extracted_contents.append(content)
                        self.stats['files_processed'] += 1
                        logger.debug(f"Processed: {file_path.relative_to(repo_path)}")
                    else:
                        self.stats['files_skipped'] += 1
                else:
                    self.stats['files_skipped'] += 1
        
        return extracted_contents
    
    def run(self):
        """Main extraction process"""
        logger.info("Starting GitHub repository data extraction...")
        logger.info(f"Input directory: {self.input_dir}")
        logger.info(f"Output file: {self.output_file}")
        
        all_contents = []
        
        # Process each repository
        for repo_path in self.input_dir.iterdir():
            if repo_path.is_dir() and not repo_path.name.startswith('.'):
                repo_contents = self.extract_repo_data(repo_path)
                all_contents.extend(repo_contents)
                self.stats['repos_processed'] += 1
        
        # Write all content to output file
        logger.info(f"Writing extracted data to: {self.output_file}")
        with open(self.output_file, 'w', encoding='utf-8') as f:
            for content in all_contents:
                f.write(content)
                f.write('\n')  # Separator between entries
        
        # Log final statistics
        logger.info("=== Extraction Complete ===")
        logger.info(f"Repositories processed: {self.stats['repos_processed']}")
        logger.info(f"Files processed: {self.stats['files_processed']}")
        logger.info(f"Files skipped: {self.stats['files_skipped']}")
        logger.info(f"Errors encountered: {self.stats['errors']}")
        logger.info(f"Total entries in output: {len(all_contents)}")
        logger.info(f"Output file: {self.output_file}")
        
        return self.stats

def main():
    """Main function"""
    extractor = GitDataExtractor(INPUT_DIR, OUTPUT_FILE)
    stats = extractor.run()
    
    print(f"\nExtraction completed successfully!")
    print(f"Output saved to: {OUTPUT_FILE}")
    print(f"Statistics: {stats}")

if __name__ == "__main__":
    main()