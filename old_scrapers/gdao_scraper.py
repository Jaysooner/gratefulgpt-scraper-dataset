#!/usr/bin/env python3
"""
Grateful Dead Archive Online (GDAO) Web Scraper
Extracts metadata and downloads visual/written media from https://www.gdao.org
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re
from urllib.parse import urljoin, urlparse
from pathlib import Path
import hashlib
import asyncio
import aiohttp
from typing import Dict, List, Optional, Set

class GDAOScraper:
    def __init__(self, base_url: str = "https://www.gdao.org", output_dir: str = "/workspace/GratefulGPT_archive_dataset"):
        self.base_url = base_url
        self.output_dir = Path(output_dir)
        self.attachments_dir = self.output_dir / "attachments"
        self.jsonl_file = self.output_dir / "gdao_archive_items.jsonl"
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting
        self.delay = 1.0  # seconds between requests
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; GDAO-Scraper/1.0; Cultural Preservation)'
        })
        
        # File extensions to download
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        self.doc_extensions = {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'}
        self.allowed_extensions = self.image_extensions | self.doc_extensions
        
    def get_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch a page with error handling and retries"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Failed to fetch {url} after {retries} attempts")
                    return None
        return None
    
    def extract_item_links(self, soup: BeautifulSoup) -> List[str]:
        """Extract item detail page links from search results"""
        links = []
        
        # Look for item links in search results
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and '/items/show/' in href:
                # Extract numeric ID from URL
                match = re.search(r'/items/show/(\d+)', href)
                if match:
                    full_url = urljoin(self.base_url, href)
                    links.append(full_url)
        
        return list(set(links))  # Remove duplicates
    
    def extract_item_metadata(self, soup: BeautifulSoup, item_url: str) -> Dict:
        """Extract metadata from an item detail page"""
        metadata = {
            'url': item_url,
            'title': '',
            'description': '',
            'creator': '',
            'date': '',
            'type': '',
            'tags': [],
            'subjects': [],
            'attachments': []
        }
        
        # Extract title from h1 first, then clean it up
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Remove the site name repetition from title
            title_text = title_text.replace('· Grateful Dead Archive Online', '').strip()
            if title_text.endswith('· Grateful Dead Archive Online'):
                title_text = title_text[:-len('· Grateful Dead Archive Online')].strip()
            metadata['title'] = title_text
        
        # Extract metadata from JSON-LD structure
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                ld_data = json.loads(json_ld.string)
                if isinstance(ld_data, dict):
                    # Extract from JSON-LD
                    if 'name' in ld_data:
                        metadata['title'] = ld_data['name']
                    if 'description' in ld_data:
                        metadata['description'] = ld_data['description']
                    if 'creator' in ld_data:
                        creator = ld_data['creator']
                        if isinstance(creator, dict) and 'name' in creator:
                            metadata['creator'] = creator['name']
                        elif isinstance(creator, str):
                            metadata['creator'] = creator
                    if 'dateCreated' in ld_data:
                        metadata['date'] = ld_data['dateCreated']
                    if 'datePublished' in ld_data:
                        metadata['date'] = ld_data['datePublished']
                    if 'genre' in ld_data:
                        metadata['type'] = ld_data['genre']
                    if 'keywords' in ld_data:
                        if isinstance(ld_data['keywords'], list):
                            metadata['tags'] = ld_data['keywords']
                        else:
                            metadata['tags'] = [ld_data['keywords']]
            except json.JSONDecodeError:
                pass
        
        # Extract metadata from table structure or definition lists
        # Look for key-value pairs in the page
        for dt in soup.find_all('dt'):
            dd = dt.find_next_sibling('dd')
            if dd:
                key = dt.get_text(strip=True).lower()
                value = dd.get_text(strip=True)
                
                if 'creator' in key:
                    metadata['creator'] = value
                elif 'date' in key:
                    metadata['date'] = value
                elif 'type' in key or 'format' in key:
                    metadata['type'] = value
                elif 'description' in key:
                    metadata['description'] = value
                elif 'tag' in key or 'subject' in key:
                    metadata['tags'].append(value)
        
        # Look for metadata in divs with specific patterns
        for div in soup.find_all('div'):
            div_class = div.get('class', [])
            if any('metadata' in cls.lower() for cls in div_class):
                # Extract from metadata divs
                for elem in div.find_all(['span', 'div', 'p']):
                    text = elem.get_text(strip=True)
                    if 'Grateful Dead' in text and not metadata['creator']:
                        metadata['creator'] = 'Grateful Dead'
                    # Look for dates in format YYYY-MM-DD
                    date_match = re.search(r'\d{4}-\d{2}-\d{2}', text)
                    if date_match and not metadata['date']:
                        metadata['date'] = date_match.group()
        
        # Extract from page text for common patterns
        page_text = soup.get_text()
        
        # Extract date from title if present
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', metadata['title'])
        if date_match and not metadata['date']:
            metadata['date'] = date_match.group(1)
        
        # Set creator to Grateful Dead if not found elsewhere
        if not metadata['creator'] and 'grateful dead' in page_text.lower():
            metadata['creator'] = 'Grateful Dead'
        
        # Extract venue from title
        venue_match = re.search(r'Live at (.+?) on \d{4}-\d{2}-\d{2}', metadata['title'])
        if venue_match:
            venue = venue_match.group(1)
            metadata['tags'].append(f'Venue: {venue}')
        
        # Extract file attachments
        metadata['attachments'] = self.extract_attachments(soup, item_url)
        
        return metadata
    
    def extract_attachments(self, soup: BeautifulSoup, base_url: str) -> List[Dict]:
        """Extract downloadable file attachments from item page"""
        attachments = []
        
        # Look for download links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if not href:
                continue
                
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin(self.base_url, href)
            elif not href.startswith('http'):
                href = urljoin(base_url, href)
            
            # Check if it's a downloadable file
            parsed_url = urlparse(href)
            file_ext = Path(parsed_url.path).suffix.lower()
            
            if file_ext in self.allowed_extensions:
                attachment = {
                    'url': href,
                    'filename': Path(parsed_url.path).name,
                    'extension': file_ext,
                    'type': 'image' if file_ext in self.image_extensions else 'document'
                }
                attachments.append(attachment)
        
        return attachments
    
    def crawl_search_results(self, max_pages: int = None) -> List[str]:
        """Crawl all pages of search results to get item URLs"""
        item_urls = []
        page = 1
        
        while True:
            if max_pages and page > max_pages:
                break
                
            search_url = f"{self.base_url}/solr-search?q=&page={page}"
            print(f"Crawling page {page}: {search_url}")
            
            soup = self.get_page(search_url)
            if not soup:
                break
            
            # Extract item links from this page
            page_links = self.extract_item_links(soup)
            if not page_links:
                print(f"No more items found on page {page}")
                break
            
            item_urls.extend(page_links)
            print(f"Found {len(page_links)} items on page {page}")
            
            # Check if there's a next page - look for pagination links
            next_link = soup.find('a', string='Next') or soup.find('a', string=str(page + 1))
            if not next_link:
                # Alternative: check if current page number is less than total pages
                # Look for total pages info in the page
                page_info = soup.find(text=re.compile(r'of \d+ results'))
                if page_info:
                    # Extract total pages from text like "26–50 of 37,279 results"
                    total_match = re.search(r'of ([\d,]+) results', page_info)
                    if total_match:
                        total_results = int(total_match.group(1).replace(',', ''))
                        items_per_page = 25  # GDAO shows 25 items per page
                        total_pages = (total_results + items_per_page - 1) // items_per_page
                        if page < total_pages:
                            print(f"Page {page} of {total_pages}, continuing...")
                        else:
                            print(f"Reached final page {page} of {total_pages}")
                            break
                    else:
                        print("No pagination info found, stopping")
                        break
                else:
                    print("No next page found, stopping")
                    break
            
            page += 1
            time.sleep(self.delay)
        
        return item_urls
    
    async def download_file(self, session: aiohttp.ClientSession, url: str, filepath: Path) -> bool:
        """Download a file asynchronously"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    return True
                else:
                    print(f"Failed to download {url}: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return False
    
    async def download_attachments(self, attachments: List[Dict], item_id: str) -> List[Dict]:
        """Download all attachments for an item"""
        if not attachments:
            return attachments
        
        # Create item-specific directory
        item_dir = self.attachments_dir / item_id
        item_dir.mkdir(exist_ok=True)
        
        updated_attachments = []
        
        async with aiohttp.ClientSession() as session:
            for attachment in attachments:
                url = attachment['url']
                filename = attachment['filename']
                
                # Generate unique filename to avoid conflicts
                file_hash = hashlib.md5(url.encode()).hexdigest()[:8]
                safe_filename = f"{file_hash}_{filename}"
                filepath = item_dir / safe_filename
                
                print(f"Downloading: {url}")
                success = await self.download_file(session, url, filepath)
                
                if success:
                    attachment['local_path'] = str(filepath)
                    attachment['downloaded'] = True
                else:
                    attachment['downloaded'] = False
                
                updated_attachments.append(attachment)
        
        return updated_attachments
    
    def save_metadata(self, metadata: Dict):
        """Save metadata to JSONL file"""
        with open(self.jsonl_file, 'a', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False)
            f.write('\n')
    
    def scrape_item(self, item_url: str) -> Optional[Dict]:
        """Scrape a single item and return metadata"""
        print(f"Scraping item: {item_url}")
        
        soup = self.get_page(item_url)
        if not soup:
            return None
        
        # Extract metadata
        metadata = self.extract_item_metadata(soup, item_url)
        
        # Extract item ID from URL
        item_id_match = re.search(r'/items/show/(\d+)', item_url)
        item_id = item_id_match.group(1) if item_id_match else str(hash(item_url))
        
        # Download attachments
        if metadata['attachments']:
            metadata['attachments'] = asyncio.run(
                self.download_attachments(metadata['attachments'], item_id)
            )
        
        return metadata
    
    def run(self, max_pages: int = None, max_items: int = None):
        """Run the complete scraping process"""
        print("Starting GDAO scraper...")
        print(f"Output directory: {self.output_dir}")
        
        # Clear existing JSONL file
        if self.jsonl_file.exists():
            self.jsonl_file.unlink()
        
        # Crawl search results to get all item URLs
        print("Crawling search results...")
        item_urls = self.crawl_search_results(max_pages)
        
        if max_items:
            item_urls = item_urls[:max_items]
        
        print(f"Found {len(item_urls)} items to scrape")
        
        # Scrape each item
        scraped_count = 0
        for i, item_url in enumerate(item_urls, 1):
            print(f"\nScraping item {i}/{len(item_urls)}")
            
            metadata = self.scrape_item(item_url)
            if metadata:
                self.save_metadata(metadata)
                scraped_count += 1
            
            time.sleep(self.delay)
        
        print(f"\nScraping complete!")
        print(f"Scraped {scraped_count} items")
        print(f"Metadata saved to: {self.jsonl_file}")
        print(f"Attachments saved to: {self.attachments_dir}")

def main():
    """Main entry point"""
    scraper = GDAOScraper()
    
    # For testing, limit to first 2 pages and 50 items
    # Remove these limits for full scraping
    scraper.run(max_pages=2, max_items=50)

if __name__ == "__main__":
    main()