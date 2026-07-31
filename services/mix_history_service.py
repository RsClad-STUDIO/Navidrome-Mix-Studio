import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

class MixHistoryService:
    """Mix生成履歴の管理サービス (Phase 10.0 対応)"""

    MAX_HISTORY_LIMIT = 100

    def __init__(self, storage_path: str = "data/mix_history.json") -> None:
        self._logger = logging.getLogger("MixHistoryService")
        self._storage_path = Path(storage_path)
        self._ensure_storage_dir_and_file()

    def _ensure_storage_dir_and_file(self) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._storage_path.exists():
            initial_data = {"version": 1, "history": []}
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)

    def load_history(self) -> List[Dict]:
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("history", [])
        except Exception:
            return []

    def save_mix(self, preset: str, timestamp: str, songs: List[Dict[str, str]], theme: Optional[str] = None) -> bool:
        history = self.load_history()
        record = {
            "timestamp": timestamp,
            "preset": preset,
            "songs": songs
        }
        history.insert(0, record)
        history = history[:self.MAX_HISTORY_LIMIT]
        
        try:
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump({"version": 1, "history": history}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self._logger.error(f"Save failed: {e}")
            return False

    def get_song_occurrence_counts(self, preset: str, lookback: int = 5) -> Dict[str, int]:
        """Section 6 の Rotation 用に過去の出現回数を集計"""
        history = self.load_history()
        preset_history = [item for item in history if item.get("preset") == preset][:lookback]

        counts: Dict[str, int] = {}
        for mix in preset_history:
            for s in mix.get("songs", []):
                sid = s.get("id")
                if sid:
                    counts[sid] = counts.get(sid, 0) + 1
        return counts