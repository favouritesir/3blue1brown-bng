import json
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any

KEYS_FILE_PATH = Path(r"C:\Users\Ashik\.config\opencode\google_ai_studio_keys.json")

class GoogleKeyManager:
    """
    Manages round-robin rotation across multiple Google AI Studio projects/keys.
    Handles rate-limits (HTTP 429), tracks RPM, cool-down, and failure states.
    """
    def __init__(self, config_path: Path = KEYS_FILE_PATH):
        self.config_path = config_path

    def _read_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {"keys": [], "current_index": 0}
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_config(self, data: Dict[str, Any]):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_next_key(self) -> Optional[str]:
        data = self._read_config()
        keys = data.get("keys", [])
        if not keys:
            return None

        # Filter active or cooled down keys
        now = time.time()
        available_keys = []
        for idx, k in enumerate(keys):
            cooldown = k.get("cooldown_until", 0)
            if k.get("status") == "active" or (k.get("status") == "rate_limited" and now >= cooldown):
                available_keys.append((idx, k))

        if not available_keys:
            # If all are cooling down, return the one with the closest cooldown
            soonest_idx, soonest_k = min(enumerate(keys), key=lambda x: x[1].get("cooldown_until", 0))
            return soonest_k.get("key")

        # Round robin selection
        current_idx = data.get("current_index", 0)
        selected_idx, selected_k = available_keys[current_idx % len(available_keys)]
        
        # Update usage timestamp and index
        data["current_index"] = (current_idx + 1) % len(available_keys)
        keys[selected_idx]["last_used_timestamp"] = now
        keys[selected_idx]["status"] = "active"
        self._save_config(data)
        
        return selected_k.get("key")

    def report_rate_limit(self, key_str: str, cooldown_seconds: int = 65):
        data = self._read_config()
        now = time.time()
        for k in data.get("keys", []):
            if k.get("key") == key_str:
                k["status"] = "rate_limited"
                k["cooldown_until"] = now + cooldown_seconds
                k["error_count"] = k.get("error_count", 0) + 1
        self._save_config(data)

    def add_key(self, key_str: str, project_name: str = "Additional Project"):
        data = self._read_config()
        keys = data.get("keys", [])
        if any(k.get("key") == key_str for k in keys):
            return
        keys.append({
            "id": f"project_{len(keys) + 1}",
            "project_name": project_name,
            "key": key_str,
            "status": "active",
            "tier": "free",
            "rpm_limit": 10,
            "last_used_timestamp": 0,
            "cooldown_until": 0,
            "error_count": 0
        })
        data["keys"] = keys
        self._save_config(data)

if __name__ == "__main__":
    mgr = GoogleKeyManager()
    key = mgr.get_next_key()
    print("Rotated key fetched:", key[:12] + "..." if key else "None")
