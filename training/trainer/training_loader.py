from pathlib import Path
import numpy as np
from typing import List, Tuple

def load_samples(limit: int = 5000):
    """Load training data for Dual-Brain"""
    folder = Path("knowledge_base/processed/train")
    samples = []
    
    for file in list(folder.glob("*.npy"))[:limit]:
        try:
            data = np.load(file)
            if data.ndim == 1 and len(data) > 1:
                samples.append((data[:-1], int(data[-1])))
        except:
            continue
    print(f"Loaded {len(samples)} samples from knowledge_base")
    return samples
