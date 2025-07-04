# GratefulGPT Dataset Collection

A comprehensive data collection project for building a Grateful Dead-focused language model. This repository contains scrapers and tools to gather text data from multiple sources related to the Grateful Dead for training a specialized GPT model.

## 🎯 Project Overview

GratefulGPT is a defensive data archiving project aimed at preserving and organizing Grateful Dead-related content for historical preservation and AI training purposes.

### Data Sources

1. **GDAO (Grateful Dead Archive Online)** - Official archive items
2. **Archive.org** - Concert recordings and metadata  
3. **GitHub Repositories** - Community projects and tools
4. **Deadcast** - Official Grateful Dead podcast transcripts

## 📊 Current Status

- ✅ **GDAO Archive**: 80 items scraped
- 🔄 **Archive.org**: 5,834+ concert recordings (ongoing)
- ✅ **GitHub Repos**: 165 repositories cloned (6.6M lines)
- ✅ **Deadcast**: 79 podcast transcripts (23,662 words)

## 🛠️ Tools & Scripts

### Core Scrapers
- `run_full_scraper.py` - GDAO archive scraper
- `Gratefuldead_archive_org.py` - Archive.org collection scraper
- `deadcast_scraper_v2.py` - Podcast transcript scraper

### Data Processing
- `clone_grateful_dead_repos.py` - GitHub repository collector
- `extract_git_data.py` - Text extraction from repositories
- `consolidate_deadcast.py` - Dataset consolidation

### Monitoring
- `monitor_and_extract.py` - Progress monitoring

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Running Scrapers

1. **GDAO Archive**:
   ```bash
   python3 run_full_scraper.py
   ```

2. **Archive.org Collection**:
   ```bash
   python3 Gratefuldead_archive_org.py
   ```

3. **GitHub Repositories**:
   ```bash
   python3 clone_grateful_dead_repos.py
   python3 extract_git_data.py
   ```

4. **Deadcast Transcripts**:
   ```bash
   python3 deadcast_scraper_v2.py
   ```

### Background Execution
```bash
nohup python3 <scraper_name>.py &
```

## 📁 Output Structure

```
GratefulGPT_archive_dataset/
├── gdao_archive_items.jsonl          # GDAO items
├── grateful_dead_archive.jsonl       # Archive.org data
├── deadcast_transcripts.jsonl        # Podcast transcripts
├── deadcast_transcripts.txt          # Consolidated transcripts
└── attachments/                      # Downloaded files

GratefulGPT_git_data/                 # Cloned repositories
GratefulGPT_git_dataset.txt           # Consolidated GitHub data
```

## 🔧 Configuration

Key settings are stored in `CLAUDE.md` including:
- Data source URLs
- File type filters
- Output formats
- Progress tracking

## 📋 Data Collection Constraints

- **No audio/video files** - Only text, images, and documents
- **Respectful scraping** - Rate limiting and error handling
- **Defensive archiving** - Historical preservation focus
- **No malicious use** - Educational and preservation purposes only

## 🤝 Contributing

This is a defensive data archiving project. Contributions should focus on:
- Improving scraping reliability
- Adding new legitimate data sources
- Enhancing data cleaning and processing
- Documentation improvements

## ⚖️ Ethics & Legal

- All scraped content is from publicly available sources
- Respects robots.txt and rate limiting
- Educational and historical preservation use
- No copyright infringement intended

## 📈 Progress Tracking

Check `CLAUDE.md` for detailed progress updates and current collection statistics.

## 🔮 Future Plans

- Additional text sources (books, articles, interviews)
- Data quality improvements
- Model training preparation
- Community contribution guidelines

---

*This project is dedicated to preserving Grateful Dead history and culture for future generations through responsible data archiving.*