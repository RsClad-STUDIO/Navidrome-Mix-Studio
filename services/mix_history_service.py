import json
import logging
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

class MixHistoryService:
    """Mix生成履歴をJSONファイルで管理するサービス。"""

    MAX_HISTORY_LIMIT = 100

    def __init__(
        self,
        storage_path: str = "data/mix_history.json",
        namespace: Optional[str] = None,
    ) -> None:
        self._logger = logging.getLogger("MixHistoryService")
        self._load_failed = False
        base_path = Path(storage_path)
        if namespace:
            namespace_hash = hashlib.sha256(namespace.encode("utf-8")).hexdigest()[:16]
            base_path = base_path.with_name(
                f"{base_path.stem}_{namespace_hash}{base_path.suffix}"
            )
        self._storage_path = base_path
        self._ensure_storage_dir_and_file()

    def _ensure_storage_dir_and_file(self) -> None:
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._storage_path.exists():
            initial_data = {"version": 1, "history": []}
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)

    def load_history(self) -> List[Dict]:
        self._load_failed = False
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or not isinstance(data.get("history"), list):
                raise ValueError("Mix history file has an invalid structure")
            return data["history"]
        except FileNotFoundError:
            return []
        except Exception as exc:
            self._load_failed = True
            self._logger.error(
                "Failed to load Mix history from %s: %s",
                self._storage_path,
                exc,
            )
            return []

    @staticmethod
    def _mix_signature(preset: str, songs: List[Dict[str, str]]) -> Optional[tuple]:
        """同じプリセット・同じ楽曲構成を同一Mixとして判定する。"""
        if not isinstance(songs, list):
            return None
        song_ids = sorted({
            str(song.get("id"))
            for song in songs
            if (
                isinstance(song, dict)
                and song.get("id") is not None
                and str(song.get("id")).strip()
            )
        })
        if not song_ids:
            return None
        return (str(preset).strip().casefold(), tuple(song_ids))

    def save_mix(self, preset: str, timestamp: str, songs: List[Dict[str, str]], theme: Optional[str] = None) -> bool:
        self.last_save_was_duplicate = False
        history = self.load_history()
        if self._load_failed:
            self._logger.error(
                "Refusing to overwrite unreadable Mix history: %s",
                self._storage_path,
            )
            return False

        signature = self._mix_signature(preset, songs)
        if signature is not None:
            for existing in history:
                if not isinstance(existing, dict):
                    continue
                existing_signature = self._mix_signature(
                    existing.get("preset", ""),
                    existing.get("songs", []),
                )
                if existing_signature == signature:
                    self.last_save_was_duplicate = True
                    self._logger.info(
                        "Duplicate Mix history skipped: preset=%s, songs=%s",
                        preset,
                        len(signature[1]),
                    )
                    return False

        record = {
            "timestamp": timestamp,
            "preset": preset,
            "songs": songs,
        }
        if theme is not None:
            record["theme"] = theme
        history.insert(0, record)
        history = history[:self.MAX_HISTORY_LIMIT]
        
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self._storage_path.parent,
                prefix=f".{self._storage_path.name}.",
                suffix=".tmp",
                delete=False,
            ) as f:
                temp_path = Path(f.name)
                json.dump(
                    {"version": 1, "history": history},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp_path, self._storage_path)
            return True
        except Exception as e:
            self._logger.error(f"Save failed: {e}")
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            return False

    def get_song_occurrence_counts(self, preset: str, lookback: int = 5) -> Dict[str, int]:
        """Rotation計算用に、指定Mixの直近履歴から曲ごとの出現回数を集計する。"""
        history = self.load_history()
        preset_history = [item for item in history if item.get("preset") == preset][:lookback]

        counts: Dict[str, int] = {}
        for mix in preset_history:
            for s in mix.get("songs", []):
                sid = s.get("id")
                if sid:
                    counts[sid] = counts.get(sid, 0) + 1
        return counts