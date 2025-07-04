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

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Usage
```bash
python3 gdao_scraper.py
```

### Advanced Usage with Options
```bash
python3 run_full_scraper.py --max-pages 10 --max-items 100 --delay 2.0
```

## Configuration Options

- `--max-pages`: Maximum number of pages to crawl (default: all pages)
- `--max-items`: Maximum number of items to scrape (default: all items)
- `--delay`: Delay between requests in seconds (default: 1.0)
- `--output-dir`: Output directory path (default: /workspace/GratefulGPT_archive_dataset)

## Output Structure

```
GratefulGPT_archive_dataset/
├── gdao_archive_items.jsonl          # Metadata in JSONL format
└── attachments/                      # Downloaded files
    ├── 101345/                       # Item-specific directories
    │   ├── abc12345_image.jpg
    │   └── def67890_document.pdf
    └── 101346/
        └── ...
```

## Sample Output

Each line in the JSONL file contains a complete item record:

```json
{
  "url": "https://www.gdao.org/items/show/101345",
  "title": "Grateful Dead Live at Charlotte Coliseum on 1992-06-17",
  "description": "- There is a small amount of tape degradation during \"Touch Of Grey\"...",
  "creator": "Grateful Dead",
  "date": "1992-06-17",
  "type": "sound recording-musical",
  "tags": ["Venue: Charlotte Coliseum"],
  "subjects": [],
  "attachments": []
}
```

## File Types Downloaded

**Included:**
- Images: .jpg, .jpeg, .png, .gif, .bmp, .tiff, .webp
- Documents: .pdf, .doc, .docx, .txt, .rtf, .odt

**Excluded:**
- Audio: .mp3, .wav, .flac, .m4a, .aac
- Video: .mp4, .mov, .avi, .mkv, .wmv

## Rate Limiting & Ethics

The scraper includes built-in rate limiting to be respectful of the GDAO servers:
- Default 1-second delay between requests
- Configurable delay settings
- Retry logic for temporary failures
- Connection pooling for efficiency

## Legal & Ethical Considerations

This scraper is designed for:
- ✅ Cultural preservation and research
- ✅ Academic study of the Grateful Dead archive
- ✅ Personal archival purposes
- ✅ Non-commercial use

**Please use responsibly and respect the GDAO's terms of service.**

## Dependencies

- requests >= 2.31.0
- beautifulsoup4 >= 4.12.0
- aiohttp >= 3.8.0
- lxml >= 4.9.0

## Architecture

The scraper consists of several key components:

1. **GDAOScraper Class**: Main scraper logic
2. **Pagination Handler**: Manages multi-page crawling
3. **Metadata Extractor**: Extracts structured data from HTML
4. **Attachment Downloader**: Async download of media files
5. **JSONL Writer**: Streams output to newline-delimited JSON

## Example Usage

### Scrape First 50 Items
```bash
python3 run_full_scraper.py --max-items 50
```

### Scrape with Slower Rate Limiting
```bash
python3 run_full_scraper.py --delay 3.0
```

### Full Archive Scrape (WARNING: This will take many hours)
```bash
python3 run_full_scraper.py
```

## Troubleshooting

- **Connection Errors**: Increase delay time with `--delay 2.0`
- **Large Dataset**: Consider using `--max-items` for testing
- **Disk Space**: Monitor available space when downloading attachments
- **Rate Limiting**: If you encounter 429 errors, increase delay time