import json
import time
from pathlib import Path
from datetime import datetime
import numpy as np

class TrajectoryRecorder:
    def __init__(self):
        self.base_dir = Path("knowledge_base")
        self.trajectories_dir = self.base_dir / "trajectories"
        self.trajectories_dir.mkdir(parents=True, exist_ok=True)
        self.current_trajectory = []

    def record_step(self, state: dict, thought: str, action: str, tool_result: str, reward: float = 0.0):
        step = {
            "timestamp": datetime.now().isoformat(),
            "state": state,
            "thought": thought,
            "action": action,
            "tool_result": tool_result,
            "reward": reward,
        }
        self.current_trajectory.append(step)

    def save_trajectory(self, task_name: str = "unnamed"):
        if not self.current_trajectory:
            return
        filename = self.trajectories_dir / f"{task_name}_{int(time.time())}.json"
        with open(filename, "w") as f:
            json.dump(self.current_trajectory, f, indent=2)
        print(f"💾 Saved trajectory: {filename} ({len(self.current_trajectory)} steps)")
        self.current_trajectory = []
