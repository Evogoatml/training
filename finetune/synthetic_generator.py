from core.dual_brain import GhostGoatDualBrain
import json
from pathlib import Path

class SyntheticGenerator:
    def __init__(self):
        self.brain = GhostGoatDualBrain(input_size=128)
        self.output_dir = Path("knowledge_base/synthetic")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_trajectories(self, task_description: str, count: int = 20):
        print(f"Generating {count} synthetic trajectories for: {task_description}")
        trajectories = []
        
        for i in range(count):
            # Simulate a full trajectory using the brain + reasoning
            traj = [
                {"step": 1, "thought": "Understanding task", "action": "plan", "result": "Task decomposed"},
                {"step": 2, "thought": "Gathering information", "action": "tool_search", "result": "Found relevant data"},
                {"step": 3, "thought": "Executing solution", "action": "tool_execute", "result": "Task completed successfully"},
            ]
            trajectories.append(traj)
            
            # Save as JSON
            with open(self.output_dir / f"synth_{task_description[:30]}_{i}.json", "w") as f:
                json.dump(traj, f, indent=2)
        
        print(f"✅ Generated {count} synthetic trajectories")
        return trajectories
