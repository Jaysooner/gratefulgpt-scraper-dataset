#!/usr/bin/env python3
"""
Efficient Deadcast transcript scraper with progress saving
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import os
import random
from urllib.parse import urljoin

class DeadcastScraper:
    def __init__(self):
        self.base_url = "https://www.dead.net"
        self.index_url = "https://www.dead.net/deadcast-index"
        self.output_dir = "/workspace/GratefulGPT_archive_dataset"
        self.progress_file = os.path.join(self.output_dir, "deadcast_progress.json")
        self.transcripts_file = os.path.join(self.output_dir, "deadcast_transcripts.jsonl")
        
        # Create session with realistic headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.dead.net/',
            'Connection': 'keep-alive'
        })
        
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_progress(self):
        """Load previously scraped episodes"""
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                return json.load(f)
        return {"scraped_urls": [], "total_episodes": 0, "successful_scrapes": 0}
    
    def save_progress(self, progress):
        """Save progress to disk"""
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def save_transcript(self, episode_data):
        """Save individual transcript"""
        with open(self.transcripts_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(episode_data, ensure_ascii=False) + '\n')
    
    def get_page(self, url, retries=3):
        """Fetch page with retries and random delays"""
        for attempt in range(retries):
            try:
                # Random delay to be respectful
                time.sleep(random.uniform(1, 3))
                
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 403:
                    print(f"403 Forbidden for {url}")
                    return None
                else:
                    print(f"HTTP {response.status_code} for {url}")
                    
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(random.uniform(2, 5))
                    
        return None
    
    def extract_episode_links(self):
        """Get all episode links from the index page"""
        print("Fetching episode links from index page...")
        
        html = self.get_page(self.index_url)
        if not html:
            print("Failed to fetch index page")
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all deadcast episode links
        episode_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and '/deadcast/' in href:
                full_url = urljoin(self.base_url, href)
                title = link.get_text(strip=True)
                if title and len(title) > 5:
                    episode_links.append({
                        'url': full_url,
                        'title': title
                    })
        
        # Remove duplicates
        seen_urls = set()
        unique_links = []
        for link in episode_links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        print(f"Found {len(unique_links)} unique episode links")
        return unique_links
    
    def scrape_episode(self, episode_url, episode_title):
        """Scrape transcript from episode page"""
        html = self.get_page(episode_url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for transcript content
        transcript_text = ""
        
        # Try different selectors for transcript content
        selectors = [
            '.field-name-field-transcript',
            '.field-name-body',
            '.field-content',
            '.content',
            'article'
        ]
        
        for selector in selectors:
            content_div = soup.select_one(selector)
            if content_div:
                text = content_div.get_text(strip=True)
                if len(text) > 200:  # Ensure we have substantial content
                    transcript_text = text
                    break
        
        if not transcript_text:
            return None
        
        # Extract metadata
        title = soup.find('h1')
        if title:
            episode_title = title.get_text(strip=True)
        
        date = ""
        date_elem = soup.select_one('.date, .published, time')
        if date_elem:
            date = date_elem.get_text(strip=True)
        
        return {
            'title': episode_title,
            'url': episode_url,
            'date': date,
            'transcript': transcript_text,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'word_count': len(transcript_text.split())
        }
    
    def scrape_all(self, max_episodes=None):
        """Main scraping function"""
        print("Starting Deadcast transcript scraper...")
        
        # Load progress
        progress = self.load_progress()
        scraped_urls = set(progress['scraped_urls'])
        
        # Get episode links
        episode_links = self.extract_episode_links()
        if not episode_links:
            print("No episode links found")
            return
        
        # Filter out already scraped episodes
        new_episodes = [ep for ep in episode_links if ep['url'] not in scraped_urls]
        
        print(f"Found {len(episode_links)} total episodes")
        print(f"Already scraped: {len(scraped_urls)}")
        print(f"New episodes to scrape: {len(new_episodes)}")
        
        if max_episodes:
            new_episodes = new_episodes[:max_episodes]
            print(f"Limiting to first {max_episodes} episodes")
        
        # Scrape episodes
        successful_scrapes = 0
        for i, episode in enumerate(new_episodes, 1):
            print(f"\n[{i}/{len(new_episodes)}] Scraping: {episode['title'][:60]}...")
            
            episode_data = self.scrape_episode(episode['url'], episode['title'])
            
            if episode_data:
                self.save_transcript(episode_data)
                successful_scrapes += 1
                scraped_urls.add(episode['url'])
                print(f"✓ Saved transcript ({episode_data['word_count']} words)")
            else:
                print(f"✗ No transcript found")
            
            # Save progress every 10 episodes
            if i % 10 == 0:
                progress['scraped_urls'] = list(scraped_urls)
                progress['total_episodes'] = len(episode_links)
                progress['successful_scrapes'] = len(scraped_urls)
                self.save_progress(progress)
                print(f"Progress saved: {len(scraped_urls)} episodes scraped")
        
        # Final progress save
        progress['scraped_urls'] = list(scraped_urls)
        progress['total_episodes'] = len(episode_links)
        progress['successful_scrapes'] = len(scraped_urls)
        self.save_progress(progress)
        
        print(f"\nScraping complete!")
        print(f"Total episodes found: {len(episode_links)}")
        print(f"Successfully scraped: {len(scraped_urls)}")
        print(f"Transcripts saved to: {self.transcripts_file}")

def main():
    scraper = DeadcastScraper()
    # Scrape all remaining episodes
    scraper.scrape_all()

if __name__ == "__main__":
    main()