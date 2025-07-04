#!/usr/bin/env python3
"""
Archive.org Grateful Dead Collection Scraper
Searches and extracts metadata from all items in the Grateful Dead collection on Archive.org
"""

import json
import os
import logging
import time
from pathlib import Path
from typing import Dict, List, Set, Optional
import requests
from bs4 import BeautifulSoup

# Try to import internetarchive, make it optional
try:
    import internetarchive as ia
    IA_AVAILABLE = True
except ImportError:
    IA_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/GratefulGPT_archive_dataset/archive_org_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ArchiveOrgScraper:
    def __init__(self, output_dir: str = "/workspace/GratefulGPT_archive_dataset"):
        self.output_dir = Path(output_dir)
        self.scraped_ids_file = self.output_dir / "scraped_ids.json"
        self.metadata_file = self.output_dir / "grateful_dead_metadata.jsonl"
        self.error_log_file = self.output_dir / "error.log"
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing scraped IDs
        self.scraped_ids = self.load_scraped_ids()
        
        # Collection identifier
        self.collection = "GratefulDead"
        
        # Rate limiting
        self.delay = 1.0  # seconds between requests
        
    def load_scraped_ids(self) -> Set[str]:
        """Load previously scraped item IDs"""
        if self.scraped_ids_file.exists():
            try:
                with open(self.scraped_ids_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('scraped_ids', []))
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Failed to load scraped IDs: {e}")
        return set()
    
    def save_scraped_ids(self):
        """Save scraped IDs to file"""
        data = {
            'scraped_ids': list(self.scraped_ids),
            'total_scraped': len(self.scraped_ids),
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(self.scraped_ids_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def log_error(self, identifier: str, error_message: str):
        """Log error to error file"""
        with open(self.error_log_file, 'a') as f:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{timestamp} | {identifier} | {error_message}\n")
    
    def clean_html(self, text: str) -> str:
        """Clean HTML from text using BeautifulSoup"""
        if not text:
            return ""
        
        try:
            # Parse HTML and extract text
            soup = BeautifulSoup(text, 'html.parser')
            cleaned = soup.get_text(separator=' ', strip=True)
            # Remove excessive whitespace
            cleaned = ' '.join(cleaned.split())
            return cleaned
        except Exception as e:
            logger.warning(f"Failed to clean HTML: {e}")
            return str(text) if text else ""
    
    def extract_metadata(self, item) -> Dict:
        """Extract metadata from an Archive.org item"""
        metadata = {
            'identifier': '',
            'title': '',
            'date': '',
            'venue': '',
            'setlist': '',
            'description': '',
            'subject': []
        }
        
        try:
            # Basic metadata
            metadata['identifier'] = getattr(item, 'identifier', '')
            metadata['title'] = getattr(item, 'metadata', {}).get('title', '')
            
            # Date handling - try multiple date fields
            item_metadata = getattr(item, 'metadata', {})
            date_fields = ['date', 'performance_date', 'year', 'coverage']
            for field in date_fields:
                if field in item_metadata and item_metadata[field]:
                    metadata['date'] = str(item_metadata[field])
                    break
            
            # Venue - try multiple venue fields
            venue_fields = ['venue', 'location', 'coverage', 'spatial']
            for field in venue_fields:
                if field in item_metadata and item_metadata[field]:
                    metadata['venue'] = str(item_metadata[field])
                    break
            
            # Description
            description = item_metadata.get('description', '')
            if isinstance(description, list):
                description = ' '.join(str(d) for d in description)
            metadata['description'] = self.clean_html(description)
            
            # Setlist - look for setlist in description or notes
            setlist_fields = ['setlist', 'notes', 'lineage', 'track']
            setlist_text = ""
            for field in setlist_fields:
                if field in item_metadata and item_metadata[field]:
                    field_value = item_metadata[field]
                    if isinstance(field_value, list):
                        field_value = ' '.join(str(v) for v in field_value)
                    setlist_text += f" {field_value}"
            
            metadata['setlist'] = self.clean_html(setlist_text.strip())
            
            # Subject/tags
            subject = item_metadata.get('subject', [])
            if isinstance(subject, str):
                subject = [subject]
            elif not isinstance(subject, list):
                subject = []
            metadata['subject'] = [str(s) for s in subject]
            
            # Additional useful fields
            metadata['creator'] = item_metadata.get('creator', '')
            metadata['source'] = item_metadata.get('source', '')
            metadata['taper'] = item_metadata.get('taper', '')
            metadata['transferer'] = item_metadata.get('transferer', '')
            metadata['runtime'] = item_metadata.get('runtime', '')
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata for {metadata.get('identifier', 'unknown')}: {e}")
            self.log_error(metadata.get('identifier', 'unknown'), str(e))
            return metadata
    
    def save_metadata(self, metadata: Dict):
        """Save metadata to JSONL file"""
        with open(self.metadata_file, 'a', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False)
            f.write('\n')
    
    def search_archive_org_api(self, start: int = 0, rows: int = 1000) -> List[Dict]:
        """Search Archive.org using the REST API as fallback"""
        items = []
        
        try:
            url = "https://archive.org/advancedsearch.php"
            params = {
                'q': f'collection:{self.collection}',
                'fl': 'identifier,title,date,description,creator,subject,venue,coverage,spatial,performance_date',
                'sort[]': 'identifier asc',
                'rows': rows,
                'start': start,
                'output': 'json'
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            docs = data.get('response', {}).get('docs', [])
            
            for doc in docs:
                # Convert API response to item-like object
                class MockItem:
                    def __init__(self, doc_data):
                        self.identifier = doc_data.get('identifier', '')
                        self.metadata = doc_data
                
                items.append(MockItem(doc))
            
            logger.info(f"Retrieved {len(docs)} items from API (start={start})")
            return items
            
        except Exception as e:
            logger.error(f"Error searching Archive.org API: {e}")
            return []
    
    def scrape_with_internetarchive(self) -> int:
        """Scrape using the internetarchive library"""
        scraped_count = 0
        
        try:
            logger.info("Searching Archive.org collection using internetarchive library...")
            
            # Search the collection using the correct query format
            search_query = f'collection:{self.collection}'
            search = ia.search_items(search_query)
            
            # Iterate through search results
            for result in search:
                # Handle both string identifiers and dict results
                if isinstance(result, dict):
                    item_id = result.get('identifier', '')
                else:
                    item_id = str(result)
                
                if not item_id:
                    continue
                    
                if item_id in self.scraped_ids:
                    logger.debug(f"Skipping already scraped item: {item_id}")
                    continue
                
                try:
                    logger.info(f"Processing item: {item_id}")
                    
                    # Get the item
                    item = ia.get_item(item_id)
                    
                    # Extract metadata
                    metadata = self.extract_metadata(item)
                    
                    if metadata['identifier']:
                        # Save metadata
                        self.save_metadata(metadata)
                        
                        # Mark as scraped
                        self.scraped_ids.add(item_id)
                        scraped_count += 1
                        
                        # Save progress periodically
                        if scraped_count % 100 == 0:
                            self.save_scraped_ids()
                            logger.info(f"Processed {scraped_count} items so far...")
                    
                except Exception as e:
                    error_msg = f"Error processing item {item_id}: {e}"
                    logger.error(error_msg)
                    self.log_error(item_id, str(e))
                
                # Rate limiting
                time.sleep(self.delay)
        
        except Exception as e:
            logger.error(f"Error in internetarchive scraping: {e}")
        
        return scraped_count
    
    def scrape_with_api(self) -> int:
        """Scrape using the Archive.org REST API"""
        scraped_count = 0
        start = 0
        rows = 1000
        
        try:
            logger.info("Searching Archive.org collection using REST API...")
            
            while True:
                items = self.search_archive_org_api(start=start, rows=rows)
                
                if not items:
                    logger.info("No more items found")
                    break
                
                for item in items:
                    item_id = item.identifier
                    
                    if item_id in self.scraped_ids:
                        logger.debug(f"Skipping already scraped item: {item_id}")
                        continue
                    
                    try:
                        logger.info(f"Processing item: {item_id}")
                        
                        # Extract metadata
                        metadata = self.extract_metadata(item)
                        
                        if metadata['identifier']:
                            # Save metadata
                            self.save_metadata(metadata)
                            
                            # Mark as scraped
                            self.scraped_ids.add(item_id)
                            scraped_count += 1
                            
                            # Save progress periodically
                            if scraped_count % 100 == 0:
                                self.save_scraped_ids()
                                logger.info(f"Processed {scraped_count} items so far...")
                    
                    except Exception as e:
                        error_msg = f"Error processing item {item_id}: {e}"
                        logger.error(error_msg)
                        self.log_error(item_id, str(e))
                    
                    # Rate limiting
                    time.sleep(self.delay)
                
                # Move to next page
                start += rows
                
                # Break if we got fewer items than requested (last page)
                if len(items) < rows:
                    break
        
        except Exception as e:
            logger.error(f"Error in API scraping: {e}")
        
        return scraped_count
    
    def run(self):
        """Main scraping process"""
        logger.info("Starting Archive.org Grateful Dead collection scraper...")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"Already scraped: {len(self.scraped_ids)} items")
        
        scraped_count = 0
        
        # Try using internetarchive library first
        if IA_AVAILABLE:
            logger.info("Using internetarchive library...")
            scraped_count = self.scrape_with_internetarchive()
        else:
            logger.info("internetarchive library not available, using REST API...")
            scraped_count = self.scrape_with_api()
        
        # Save final progress
        self.save_scraped_ids()
        
        # Final summary
        logger.info("=== Scraping Complete ===")
        logger.info(f"Items processed in this run: {scraped_count}")
        logger.info(f"Total items scraped: {len(self.scraped_ids)}")
        logger.info(f"Metadata file: {self.metadata_file}")
        logger.info(f"Scraped IDs file: {self.scraped_ids_file}")
        logger.info(f"Error log: {self.error_log_file}")

def main():
    """Main function"""
    scraper = ArchiveOrgScraper()
    scraper.run()

if __name__ == "__main__":
    if not IA_AVAILABLE:
        print("Warning: internetarchive library not found. Install with: pip install internetarchive")
        print("Falling back to REST API method...")
    
    main()