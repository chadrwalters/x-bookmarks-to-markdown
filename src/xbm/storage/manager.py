"""Storage manager for XBM."""
from pathlib import Path
import json
from typing import Optional, Dict, Any

class StorageManager:
    """Manages state and storage for XBM."""

    def __init__(self):
        """Initialize storage manager."""
        self.state_dir = Path(".xbm")
        self.state_dir.mkdir(exist_ok=True)
        self.state_file = self.state_dir / "state.json"

    def load_state(self) -> Dict[str, Any]:
        """Load state from storage.

        Returns:
            Dict[str, Any]: Current state
        """
        if not self.state_file.exists():
            return {}
        try:
            return json.loads(self.state_file.read_text())
        except json.JSONDecodeError:
            return {}

    def save_state(self, state: Dict[str, Any]) -> None:
        """Save state to storage.

        Args:
            state: State to save
        """
        self.state_file.write_text(json.dumps(state))
