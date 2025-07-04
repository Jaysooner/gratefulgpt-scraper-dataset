#!/usr/bin/env python3
"""
Monitor training progress and automatically start follow-up training
"""

import time
import subprocess
import re
from pathlib import Path

def get_training_progress():
    """Parse training log to get current progress"""
    log_file = "/workspace/training.log"
    
    if not Path(log_file).exists():
        return None
    
    try:
        # Read last few lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Look for progress pattern in last 20 lines
        for line in reversed(lines[-20:]):
            # Look for pattern like "100%|██████████| 5571/5571"
            match = re.search(r'(\d+)%\|.*?\|\s*(\d+)/(\d+)', line)
            if match:
                percent, current, total = match.groups()
                return {
                    'percent': int(percent),
                    'current_step': int(current),
                    'total_steps': int(total),
                    'completed': int(percent) >= 100
                }
        
        return None
    except Exception as e:
        print(f"Error parsing log: {e}")
        return None

def check_training_process():
    """Check if training process is still running"""
    try:
        result = subprocess.run(['pgrep', '-f', 'axolotl'], 
                              capture_output=True, text=True)
        return len(result.stdout.strip()) > 0
    except:
        return False

def start_followup_training():
    """Start the follow-up training with enhanced dataset"""
    print("🚀 Starting follow-up training with enhanced dataset...")
    
    # Create output directory
    subprocess.run(['mkdir', '-p', '/workspace/data/axolotl-artifacts/gratefulgpt-followup-outputs'])
    
    # Start training
    cmd = [
        'python', '-m', 'axolotl.cli.train', 
        '/workspace/data/gratefulgpt_followup_config.yml'
    ]
    
    with open('/workspace/followup_training.log', 'w') as f:
        process = subprocess.Popen(cmd, 
                                 stdout=f, 
                                 stderr=subprocess.STDOUT,
                                 cwd='/workspace')
    
    print(f"Follow-up training started with PID {process.pid}")
    print("Monitor with: tail -f /workspace/followup_training.log")
    
    return process

def main():
    """Main monitoring loop"""
    print("📊 Training Monitor Started")
    print("Monitoring current training...")
    
    last_percent = 0
    
    while True:
        # Check if process is running
        if not check_training_process():
            print("❌ Training process not found")
            break
        
        # Get progress
        progress = get_training_progress()
        if progress:
            if progress['percent'] > last_percent:
                print(f"📈 Progress: {progress['percent']}% ({progress['current_step']}/{progress['total_steps']})")
                last_percent = progress['percent']
            
            if progress['completed']:
                print("✅ Training completed!")
                break
        
        # Wait before next check
        time.sleep(30)  # Check every 30 seconds
    
    print("🎯 Preparing for follow-up training...")
    time.sleep(5)  # Give a moment for cleanup
    
    # Start follow-up training
    start_followup_training()

if __name__ == "__main__":
    main()