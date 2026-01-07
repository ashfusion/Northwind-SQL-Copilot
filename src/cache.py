import json
import os
from typing import Optional, Dict

class CacheManager:
    def __init__(self, file_path: str = "query_cache.json", enabled: bool = True):
        self.file_path = file_path
        self.enabled = enabled
        self._cache: Dict[str, dict] = {}
        self._load_cache()

    def _load_cache(self):
        """Loads cache from disk if it exists."""
        if not self.enabled:
            return
            
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self._cache = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._cache = {}

    def _save_cache(self):
        """Persists cache to disk."""
        if not self.enabled:
            return
            
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2)
        except IOError:
            pass

    def get(self, question: str) -> Optional[dict]:
        """Retrieves a result if the question exists in cache."""
        if not self.enabled:
            return None
        return self._cache.get(question.strip().lower())

    def set(self, question: str, response_data: dict):
        """Saves a result to the cache."""
        if not self.enabled:
            return
            
        self._cache[question.strip().lower()] = response_data
        self._save_cache()

    def clear(self):
        """Clears the cache file."""
        self._cache = {}
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

# Global instance will be created in pipeline or main