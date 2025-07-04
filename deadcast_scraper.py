#!/usr/bin/env python3
"""
Scraper for Grateful Dead Deadcast episode transcripts from https://www.dead.net/deadcast-index
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os
from urllib.parse import urljoin, urlparse

class DeadcastScraper:
    def __init__(self):
        self.base_url = "https://www.dead.net"
        self.index_url = "https://www.dead.net/deadcast-index"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Referer': 'https://www.dead.net/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.episodes = []
        self.transcripts = []
        
    def get_page(self, url):
        """Fetch a page with error handling"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_episode_links(self, html):
        """Extract episode links from the index page"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for the podcasts view container
        podcast_view = soup.find('div', class_='view-podcasts')
        if not podcast_view:
            print("Could not find podcast view container")
            return []
        
        episode_links = []
        
        # Look for episode links within the podcast view
        selectors = [
            'a[href*="deadcast"]',
            'a[href*="episode"]', 
            'a[href*="podcast"]',
            'a[href*="/node/"]',
            '.views-row a',
            '.episode-title a',
            'h3 a',
            'h4 a'
        ]
        
        for selector in selectors:
            links = podcast_view.select(selector)
            for link in links:
                href = link.get('href')
                if href and href not in [l['url'] for l in episode_links]:
                    full_url = urljoin(self.base_url, href)
                    title = link.get('title', '') or link.get_text(strip=True)
                    # Skip if title is too short or generic
                    if len(title) > 5 and not title.lower() in ['more', 'read more', 'listen']:
                        episode_links.append({
                            'url': full_url,
                            'title': title,
                            'text': link.get_text(strip=True)
                        })
        
        # Also look for transcript links in brackets
        transcript_pattern = r'\[([^\]]+)\]'
        transcript_links = re.findall(transcript_pattern, html)
        for transcript_text in transcript_links:
            if 'transcript' in transcript_text.lower():
                # Find the corresponding link
                transcript_soup = BeautifulSoup(html, 'html.parser')
                for link in transcript_soup.find_all('a'):
                    if transcript_text in link.get_text():
                        href = link.get('href')
                        if href:
                            full_url = urljoin(self.base_url, href)
                            episode_links.append({
                                'url': full_url,
                                'title': f"Transcript: {transcript_text}",
                                'text': link.get_text(strip=True)
                            })
        
        return episode_links
    
    def scrape_episode_page(self, episode_url):
        """Scrape an individual episode page for transcript"""
        print(f"Scraping episode: {episode_url}")
        
        html = self.get_page(episode_url)
        if not html:
            return None
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract episode metadata
        title = soup.find('h1') or soup.find('title')
        title = title.get_text(strip=True) if title else "Unknown Title"
        
        # Look for transcript content
        transcript_selectors = [
            '.transcript',
            '.episode-transcript',
            '.content-transcript',
            '[id*="transcript"]',
            '[class*="transcript"]'
        ]
        
        transcript_content = ""
        for selector in transcript_selectors:
            transcript_div = soup.select_one(selector)
            if transcript_div:
                transcript_content = transcript_div.get_text(strip=True)
                break
        
        # If no specific transcript div, try to find main content
        if not transcript_content:
            main_content = soup.select_one('.content, .main-content, .article-content, .field-content')
            if main_content:
                transcript_content = main_content.get_text(strip=True)
        
        # Extract other metadata
        date = ""
        date_selectors = ['.date', '.published', '.episode-date', 'time']
        for selector in date_selectors:
            date_elem = soup.select_one(selector)
            if date_elem:
                date = date_elem.get_text(strip=True)
                break
        
        episode_data = {
            'title': title,
            'url': episode_url,
            'date': date,
            'transcript': transcript_content,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return episode_data
    
    def scrape_all_episodes(self):
        """Main scraping method"""
        print("Fetching Deadcast index page...")
        
        # Get the main index page
        index_html = self.get_page(self.index_url)
        if not index_html:
            print("Failed to fetch index page")
            return
        
        # Extract episode links
        episode_links = self.extract_episode_links(index_html)
        print(f"Found {len(episode_links)} potential episode links")
        
        # Print found links for debugging
        for i, link in enumerate(episode_links[:10]):  # Show first 10
            print(f"{i+1}. {link['title'][:50]}... -> {link['url']}")
        
        # Scrape each episode
        for i, episode_link in enumerate(episode_links, 1):
            print(f"\nScraping episode {i}/{len(episode_links)}")
            
            episode_data = self.scrape_episode_page(episode_link['url'])
            if episode_data and episode_data['transcript']:
                self.transcripts.append(episode_data)
                print(f"✓ Scraped transcript for: {episode_data['title'][:50]}...")
            else:
                print(f"✗ No transcript found for: {episode_link['title'][:50]}...")
            
            # Be respectful - add delay between requests
            time.sleep(2)
    
    def save_transcripts(self, output_dir="GratefulGPT_archive_dataset"):
        """Save transcripts to files"""
        if not self.transcripts:
            print("No transcripts to save")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save as JSONL
        jsonl_file = os.path.join(output_dir, "deadcast_transcripts.jsonl")
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for transcript in self.transcripts:
                f.write(json.dumps(transcript, ensure_ascii=False) + '\n')
        
        # Save as single text file for training
        txt_file = os.path.join(output_dir, "deadcast_transcripts.txt")
        with open(txt_file, 'w', encoding='utf-8') as f:
            for transcript in self.transcripts:
                f.write(f"=== {transcript['title']} ===\n")
                f.write(f"Date: {transcript['date']}\n")
                f.write(f"URL: {transcript['url']}\n\n")
                f.write(transcript['transcript'])
                f.write("\n\n" + "="*80 + "\n\n")
        
        print(f"Saved {len(self.transcripts)} transcripts to:")
        print(f"  - {jsonl_file}")
        print(f"  - {txt_file}")

def main():
    scraper = DeadcastScraper()
    scraper.scrape_all_episodes()
    scraper.save_transcripts()

if __name__ == "__main__":
    main()