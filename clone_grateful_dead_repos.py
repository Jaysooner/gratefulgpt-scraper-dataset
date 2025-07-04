#!/usr/bin/env python3
"""
GitHub Repository Cloner for Grateful Dead related repositories
Searches GitHub for repositories and clones them to local storage
"""

import os
import json
import requests
import subprocess
from pathlib import Path
import time
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/workspace/clone_grateful_dead_repos.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# GitHub token - should be set via environment variable
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

# Output directory
OUTPUT_DIR = "/workspace/GratefulGPT_git_data"

# Search queries to try
SEARCH_QUERIES = [
    "grateful dead",
    "gratefuldead", 
    "grateful dead setlist",
    "grateful dead data",
    "grateful dead visualizer",
    "grateful dead archive",
    "grateful dead tools"
]

def search_github_repos(query, token, per_page=100, max_pages=10):
    """Search GitHub repositories using the REST API"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    repos = []
    
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/search/repositories"
        params = {
            'q': query,
            'sort': 'stars',
            'order': 'desc',
            'per_page': per_page,
            'page': page
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if 'items' not in data:
                logger.info(f"No items found for query '{query}' on page {page}")
                break
                
            page_repos = data['items']
            if not page_repos:
                logger.info(f"No more repos found for query '{query}' on page {page}")
                break
                
            repos.extend(page_repos)
            
            logger.info(f"Found {len(page_repos)} repos for '{query}' on page {page}")
            
            # Log each repo name and description
            for repo in page_repos:
                logger.info(f"  - {repo['full_name']}: {repo.get('description', 'No description')}")
            
            # Respect rate limits
            time.sleep(1)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error searching for '{query}' on page {page}: {e}")
            break
    
    return repos

def clone_repo(repo_url, clone_dir):
    """Clone a repository to the specified directory"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(clone_dir, exist_ok=True)
        
        # Clone the repository
        result = subprocess.run(
            ['git', 'clone', repo_url, clone_dir],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Successfully cloned: {repo_url}")
            return True
        else:
            logger.error(f"Failed to clone {repo_url}: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout cloning {repo_url}")
        return False
    except Exception as e:
        logger.error(f"Error cloning {repo_url}: {e}")
        return False

def save_manifest(repos, output_dir):
    """Save a detailed manifest of all repositories for auditing"""
    manifest = {
        "timestamp": datetime.now().isoformat(),
        "total_repos": len(repos),
        "repositories": []
    }
    
    for repo in repos:
        repo_info = {
            "name": repo['full_name'],
            "description": repo.get('description', 'No description'),
            "clone_url": repo['clone_url'],
            "stars": repo.get('stargazers_count', 0),
            "forks": repo.get('forks_count', 0),
            "language": repo.get('language', 'Unknown'),
            "created_at": repo.get('created_at', ''),
            "updated_at": repo.get('updated_at', ''),
            "size": repo.get('size', 0),
            "topics": repo.get('topics', []),
            "license": repo.get('license', {}).get('name', 'No license') if repo.get('license') else 'No license',
            "archived": repo.get('archived', False),
            "private": repo.get('private', False)
        }
        manifest["repositories"].append(repo_info)
    
    # Sort by stars descending
    manifest["repositories"].sort(key=lambda x: x['stars'], reverse=True)
    
    manifest_file = os.path.join(output_dir, "repository_manifest.json")
    with open(manifest_file, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Saved detailed manifest to: {manifest_file}")
    return manifest_file

def main():
    """Main function to search and clone repositories"""
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_repos = []
    seen_repos = set()
    query_stats = {}
    
    logger.info("Starting GitHub repository search for Grateful Dead related content...")
    
    # Search for repositories
    for query in SEARCH_QUERIES:
        logger.info(f"\nSearching for: {query}")
        repos = search_github_repos(query, GITHUB_TOKEN)
        
        query_stats[query] = {
            'total_found': len(repos),
            'new_repos': 0
        }
        
        # Deduplicate repos based on repository ID
        for repo in repos:
            repo_id = repo['id']
            if repo_id not in seen_repos:
                seen_repos.add(repo_id)
                all_repos.append(repo)
                query_stats[query]['new_repos'] += 1
    
    logger.info(f"\n=== Search Summary ===")
    total_found = sum(stats['total_found'] for stats in query_stats.values())
    logger.info(f"Total repositories found across all queries: {total_found}")
    logger.info(f"Unique repositories after deduplication: {len(all_repos)}")
    
    for query, stats in query_stats.items():
        logger.info(f"  '{query}': {stats['total_found']} found, {stats['new_repos']} new")
    
    # Save repository metadata (raw GitHub API response)
    metadata_file = os.path.join(OUTPUT_DIR, "repository_metadata.json")
    with open(metadata_file, 'w') as f:
        json.dump(all_repos, f, indent=2)
    
    logger.info(f"Saved raw repository metadata to: {metadata_file}")
    
    # Save detailed manifest for auditing
    manifest_file = save_manifest(all_repos, OUTPUT_DIR)
    
    # Save search statistics
    stats_file = os.path.join(OUTPUT_DIR, "search_statistics.json")
    search_stats = {
        "timestamp": datetime.now().isoformat(),
        "queries": query_stats,
        "total_found": total_found,
        "unique_repos": len(all_repos),
        "deduplication_ratio": f"{len(all_repos)}/{total_found} ({len(all_repos)/total_found*100:.1f}%)" if total_found > 0 else "0/0 (0%)"
    }
    
    with open(stats_file, 'w') as f:
        json.dump(search_stats, f, indent=2)
    
    logger.info(f"Saved search statistics to: {stats_file}")
    
    # Clone repositories
    successful_clones = 0
    failed_clones = 0
    skipped_clones = 0
    
    for i, repo in enumerate(all_repos, 1):
        repo_name = repo['full_name']
        clone_url = repo['clone_url']
        
        logger.info(f"\n[{i}/{len(all_repos)}] Processing: {repo_name}")
        logger.info(f"Description: {repo.get('description', 'No description')}")
        logger.info(f"Stars: {repo.get('stargazers_count', 0)}, Language: {repo.get('language', 'Unknown')}")
        
        # Create safe directory name
        safe_name = repo_name.replace('/', '_')
        clone_dir = os.path.join(OUTPUT_DIR, safe_name)
        
        # Skip if already exists
        if os.path.exists(clone_dir):
            logger.info(f"Directory already exists, skipping: {clone_dir}")
            skipped_clones += 1
            continue
        
        if clone_repo(clone_url, clone_dir):
            successful_clones += 1
        else:
            failed_clones += 1
        
        # Rate limiting
        time.sleep(2)
    
    # Final summary
    logger.info(f"\n=== Final Summary ===")
    logger.info(f"Total unique repositories found: {len(all_repos)}")
    logger.info(f"Successfully cloned: {successful_clones}")
    logger.info(f"Failed to clone: {failed_clones}")
    logger.info(f"Skipped (already exists): {skipped_clones}")
    logger.info(f"Output directory: {OUTPUT_DIR}")
    logger.info(f"Manifest file: {manifest_file}")
    logger.info(f"Statistics file: {stats_file}")

if __name__ == "__main__":
    main()