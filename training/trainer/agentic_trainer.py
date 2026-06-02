from core.dual_brain import GhostGoatDualBrain
from pathlib import Path
import json
import numpy as np
from typing import List, Tuple

class AgenticTrainer:
    def __init__(self):
        self.brain = GhostGoatDualBrain(input_size=128)
        self.synthetic_dir = Path("knowledge_base/synthetic")
        self.trajectories_dir = Path("knowledge_base/trajectories")

    def load_samples(self, limit: int = 2000) -> List[Tuple[np.ndarray, int]]:
        """Load both synthetic and real trajectories"""
        samples = []
        
        # Load synthetic data (what the generator creates)
        for file in list(self.synthetic_dir.glob("*.json"))[:limit]:
            try:
                data = json.load(open(file))
                # Simple conversion: success = 1, failure = 0
                for step in data:
                    reward = 1 if "success" in str(step).lower() or "completed" in str(step).lower() else 0
                    # Dummy features for now (we can improve this later)
                    features = np.random.rand(128).astype(np.float32)
                    samples.append((features, reward))
            except:
                continue
                
        print(f"Loaded {len(samples)} samples from synthetic data")
        return samples[:limit]

    def train(self, epochs: int = 5):
        samples = self.load_samples()
        if not samples:
            print("❌ No training data found. Run the generator first.")
            return False
        
        print(f"Training Dual-Brain on {len(samples)} agentic samples...")
        metrics = self.brain.self_improve(samples)
        return metrics
