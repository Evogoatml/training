#!/usr/bin/env python3
"""
Pentest Trainer - Uses the 323k dataset to train your AI
"""

import json
import subprocess
from pathlib import Path

# Download the dataset
DATA_URL = "https://huggingface.co/datasets/7h3-R3v3n4n7/pentest-agent-dataset-alpaca/resolve/main/train.json"

class PentestTrainer:
    def __init__(self):
        self.data_dir = Path("~/telegram-bot/training").expanduser()
        self.data_dir.mkdir(exist_ok=True)
    
    def download_dataset(self) -> bool:
        """Download the 323k dataset"""
        print(f"Downloading dataset from HuggingFace...")
        try:
            # Try huggingface-cli first
            result = subprocess.run(
                ["huggingface-cli", "download", "7h3-R3v3n4n7/pentest-agent-dataset-alpaca"],
                capture_output=True, text=True, timeout=300
            )
            if result.returncode == 0:
                print("Downloaded!")
                return True
        except:
            pass
        
        # Manual download
        print("Trying manual download...")
        try:
            import requests
            r = requests.get(DATA_URL, stream=True, timeout=600)
            if r.status_code == 200:
                path = self.data_dir / "train.json"
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"Saved to {path}")
                return True
        except Exception as e:
            print(f"Download failed: {e}")
        return False
    
    def prepare_ollama(self):
        """Convert to Ollama format and train"""
        train_file = self.data_dir / "train.json"
        
        if not train_file.exists():
            print("Dataset not found. Downloading...")
            if not self.download_dataset():
                print("Could not download. Create data manually:")
                print("1. Go to https://huggingface.co/datasets/7h3-R3v3n4n7/pentest-agent-dataset-alpaca")
                print("2. Download train.json")
                print("3. Place in ~/telegram-bot/training/")
                return
        
        print(f"Training data: {train_file}")
        print(f"Size: {train_file.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Count records
        with open(train_file) as f:
            count = sum(1 for line in f)
        print(f"Records: {count}")
        
        print("\nTo train with Ollama:")
        print("1. ollama create pentest-train")
        print("2. Use Modelfile with FROM and ADAPTER")
        print("\nOr use llamafine:")
        print("python3 fine_tune.py --data train.json --output model")

def main():
    trainer = PentestTrainer()
    
    print("="*50)
    print("Pentest Trainer - 323k Dataset")
    print("="*50)
    
    # Check dataset
    trainer.prepare_ollama()
    
    print("\n" + "="*50)
    print("Alternative: Use with LangChain RAG")
    print("="*50)

if __name__ == '__main__':
    main()