# Project Memory

## Project Overview
You are helping maintain an existing Python scraper project called `run_full_scraper.py`. The script is already working and tested. It scrapes the Grateful Dead Archive Online (GDAO) from https://www.gdao.org/items.

Project Summary:
- The script scrapes all paginated item listings from https://www.gdao.org/items
- For each item, it extracts:
  - Title, Description, Creator, Date, Type, Tags
  - URLs to attachments (images, PDFs, DOCs — NO audio or video)
- It saves metadata as JSONL to:
  /workspace/GratefulGPT_archive_dataset/gdao_archive_items.jsonl
- It downloads attachments (images and documents only) to:
  /workspace/GratefulGPT_archive_dataset/attachments/

## Constraints
- Audio and video files are ignored (e.g., mp3, mp4, wav, mov, etc.)
- Only image and document file extensions are downloaded (jpg, png, gif, pdf, doc, txt)
- Script uses aiohttp for async downloading, and BeautifulSoup + requests for scraping
- Metadata is appended to a JSONL file
- Background runs use: `nohup python3 run_full_scraper.py &`

## Coding Standards
- Python 3.x
- Async/await patterns with aiohttp
- BeautifulSoup for HTML parsing
- JSONL format for data storage

## Common Workflows
- Run scraper: `python3 run_full_scraper.py`
- Background run: `nohup python3 run_full_scraper.py &`
- Check logs: `tail -f nohup.out`

## Dependencies and Tools
- aiohttp (async HTTP client)
- BeautifulSoup (HTML parsing)
- requests (HTTP requests)
- Standard Python libraries

## Notes
- This is a defensive data archiving project for historical preservation
- Focus on maintaining existing functionality, not adding new features
- Only image and document files are downloaded, no audio/video

## GitHub Personal Access Token
# Token stored securely - not committed to repository
# Set via environment variable: GITHUB_TOKEN

## 🧠 Additional Context: GitHub Repositories for GratefulGPT

You are helping build a custom dataset for the **GratefulGPT** project, which focuses on Grateful Dead-related content (setlists, community tools, audio metadata, visualizations, etc.). In addition to scraping from `archive.org` and other sources, you now also include content from public **GitHub repositories**.

### 🎯 Task:
Automatically find and extract content from relevant GitHub repositories using GitHub's Search API.

### ✅ Workflow:
1. Use GitHub search queries like:
   - `grateful dead setlist`
   - `grateful dead data`
   - `grateful dead visualizer`
   - `grateful dead archive tools`

2. For each result:
   - Save the `clone_url` and repo name.
   - Clone the repo into the local `/workspace/GratefulGPT_git_data` folder.

3. Clean the data:
   - Extract `.md`, `.txt`, `.csv`, `.json`, `.yaml` files.
   - Ignore `LICENSE`, `.gitignore`, and other boilerplate unless meaningful.
   - Optionally tag extracted blocks with filename and source repository

## 🧠 Task: Extract and clean GitHub repo data for GratefulGPT fine-tuning

You are working on converting cloned GitHub repositories into training data for GratefulGPT.

### Input
All Git repos are in: `/workspace/GratefulGPT_git_data/`

Extract and process only the following file types:
- `.md`, `.txt`, `.csv`, `.json`, `.yaml`

### Instructions
For each relevant file:
1. Read the text content
2. Add a header like:
3. Append the file contents (stripped of blank lines or markdown noise)
4. Separate entries with a blank line

Ignore:
- `LICENSE`, `.gitignore`, `.png`, `.jpg`, `.zip`, `.mp4`, `.wav`, and code files unless specifically requested

### Output Format
One clean `.txt` file (or JSONL if structured), saved to:
/workspace/GratefulGPT_git_dataset.txt  **
This file will be added to the model's training corpus alongside scraped data from archive.org and other sources.

## 📊 Current Project Progress (Updated 2025-07-04)

### ✅ Data Collection Status:

**1. GDAO Archive (Grateful Dead Archive Online)**
- **Status**: ✅ Complete
- **Items scraped**: 80 archive items
- **Output**: `/workspace/GratefulGPT_archive_dataset/gdao_archive_items.jsonl`
- **Attachments**: Downloaded to `/workspace/GratefulGPT_archive_dataset/attachments/`

**2. Archive.org Grateful Dead Collection**
- **Status**: 🔄 Running (PID 17209, started 06:57)
- **Items scraped**: 5,834+ concert recordings and metadata
- **Output**: `/workspace/GratefulGPT_archive_dataset/grateful_dead_archive.jsonl`
- **Progress**: Currently processing 1977 shows

**3. GitHub Repositories**
- **Status**: ✅ Complete
- **Repositories cloned**: 165 Grateful Dead-related repos
- **Location**: `/workspace/GratefulGPT_git_data/`
- **Dataset created**: `/workspace/GratefulGPT_git_dataset.txt` (6.6M lines)
- **Notable finds**: DeadBase XI complete text, setlist databases, analysis tools

**4. Deadcast Transcripts (Official Podcast)**
- **Status**: ✅ Complete
- **Episodes scraped**: 79 out of 109 total episodes (72% success rate)
- **Word count**: 23,662 words of transcript content
- **Output**: `/workspace/GratefulGPT_archive_dataset/deadcast_transcripts.jsonl`
- **Consolidated**: `/workspace/GratefulGPT_archive_dataset/deadcast_transcripts.txt`
- **Content**: Album deep-dives, band history, musical analysis from official podcast

### 📈 Dataset Summary:
- **Total data sources**: 4 major collections
- **GDAO items**: 80
- **Archive.org items**: 5,834+ (growing)
- **GitHub repos**: 165 repositories
- **Podcast episodes**: 79 transcripts
- **Total text content**: 6.6M+ lines + 23,662 words + ongoing archive.org collection

### 🔧 Tools Created:
- `run_full_scraper.py` - GDAO scraper
- `Gratefuldead_archive_org.py` - Archive.org scraper (currently running)
- `clone_grateful_dead_repos.py` - GitHub repository collector
- `extract_git_data.py` - Text extraction from repositories
- `deadcast_scraper_v2.py` - Podcast transcript scraper
- `consolidate_deadcast.py` - Dataset consolidation tool