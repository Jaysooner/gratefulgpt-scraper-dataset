#!/usr/bin/env python3
"""
Monitor GitHub cloning process and run extraction when complete
"""

import subprocess
import time
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_cloning_running():
    """Check if the cloning process is still running"""
    try:
        result = subprocess.run(
            ['ps', 'aux'], 
            capture_output=True, 
            text=True
        )
        return 'clone_grateful_dead_repos.py' in result.stdout
    except Exception as e:
        logger.error(f"Error checking process: {e}")
        return False

def run_extraction():
    """Run the data extraction script"""
    logger.info("Starting data extraction...")
    try:
        result = subprocess.run(
            ['python3', '/workspace/extract_git_data.py'],
            capture_output=True,
            text=True,
            cwd='/workspace'
        )
        
        if result.returncode == 0:
            logger.info("Data extraction completed successfully!")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"Data extraction failed: {result.stderr}")
            
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error running extraction: {e}")
        return False

def main():
    """Main monitoring loop"""
    logger.info("Starting monitor for GitHub cloning completion...")
    
    while True:
        if is_cloning_running():
            logger.info("Cloning still in progress... checking again in 30 seconds")
            time.sleep(30)
        else:
            logger.info("Cloning process completed! Starting extraction...")
            success = run_extraction()
            if success:
                logger.info("All done! Check /workspace/GratefulGPT_git_dataset.txt for results")
            else:
                logger.error("Extraction failed. Check logs for details.")
            break

if __name__ == "__main__":
    main()