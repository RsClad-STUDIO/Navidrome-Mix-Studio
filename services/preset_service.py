"""Mix生成パラメータプリセットの永続化・管理を行うサービス。"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from models.mix_preset import MixPreset


class PresetService:
    """MixPresetの読み書きを行うサービスクラス。"""

    def __init__(
        self,
        filepath: str = "config/presets.json",
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._filepath = Path(filepath)
        self._logger = logger or logging.getLogger(__name__)
        self._presets: Dict[str, MixPreset] = {}

        self.load()

    def _get_default_presets(self) -> List[MixPreset]:
        return [
            MixPreset(name="Daily Mix", mix_type="Recent", limit=25, favorite_priority="Medium"),
            MixPreset(name="Favorites Mix", mix_type="Popular", limit=30, favorite_priority="High"),
            MixPreset(name="Discovery Mix", mix_type="Discovery", limit=25, favorite_priority="Low"),
            MixPreset(name="Decade Mix", mix_type="Era", limit=30, favorite_priority="Medium"),
        ]

    def load(self) -> None:
        """ファイルからプリセットを読み込みます。存在しない場合はデフォルトを作成します。"""
        if not self._filepath.exists():
            for p in self._get_default_presets():
                self._presets[p.name] = p
            self.save()
            return

        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._presets.clear()
                for item in data:
                    preset = MixPreset.from_dict(item)
                    self._presets[preset.name] = preset
        except Exception as e:
            self._logger.error(f"Failed to load presets: {e}")

    def save(self) -> None:
        """全プリセットをJSONに保存します。"""
        try:
            self._filepath.parent.mkdir(parents=True, exist_ok=True)
            data = [p.to_dict() for p in self._presets.values()]
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._logger.info("Presets saved successfully.")
        except Exception as e:
            self._logger.error(f"Failed to save presets: {e}")

    def get_all(self) -> List[MixPreset]:
        return list(self._presets.values())

    def get(self, name: str) -> Optional[MixPreset]:
        return self._presets.get(name)

    def save_preset(self, preset: MixPreset) -> None:
        self._presets[preset.name] = preset
        self.save()

    def delete_preset(self, name: str) -> None:
        if name in self._presets:
            del self._presets[name]
            self.save()