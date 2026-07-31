"""設定ファイルの読み書きおよびデフォルト値を管理するモジュール。"""

import json
from pathlib import Path
from typing import Any, Dict


class Settings:
    """JSON形式の設定ファイルを管理するクラス。"""

    DEFAULT_SETTINGS: Dict[str, Any] = {
        "language": "ja",


        "connection": {
            "server_url": "",
            "username": "",
            "password": "",
        },
        "window": {
            "width": 1100,
            "height": 700,
            "maximized": False,
        },
        "scheduler": {
            "enabled": False,
            "mode": "daily",  # "daily", "interval", "startup"
            "time": "07:00",
            "interval_hours": 6,
        },
        "cache": {
            "enabled": True,
            "expire_hours": 24,
        },
        "mix": {
            "default_count": 50,
            "auto_update": False,
            "default_type": "Recent",
        },
    }

    def __init__(self, filepath: str = "config.json") -> None:
        """Settingsを初期化します。

        Args:
            filepath (str): 設定ファイルの保存パス
        """
        self._filepath = Path(filepath)
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """設定ファイルを読み込みます。ファイルがない、または壊れている場合はデフォルトを適用します。"""
        self._data = self._deep_copy(self.DEFAULT_SETTINGS)

        if self._filepath.exists():
            try:
                with open(self._filepath, "r", encoding="utf-8") as f:
                    file_data = json.load(f)
                    self._merge_dict(self._data, file_data)
            except Exception:
                self.save()
        else:
            self.save()

    def save(self) -> None:
        """現在の設定をファイルに保存します。"""
        try:
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def get(self, key_path: str, default: Any = None) -> Any:
        """ドット区切りのキーパスで値を取得します（例: "scheduler.enabled"）。"""
        keys = key_path.split(".")
        val = self._data
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, key_path: str, value: Any) -> None:
        """ドット区切りのキーパスで値を設定します。"""
        keys = key_path.split(".")
        val = self._data
        for k in keys[:-1]:
            if k not in val or not isinstance(val[k], dict):
                val[k] = {}
            val = val[k]
        val[keys[-1]] = value

    def _merge_dict(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """再帰的に辞書をマージします。"""
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._merge_dict(base[k], v)
            else:
                base[k] = v

    def _deep_copy(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """辞書のディープコピーを作成します。"""
        return json.loads(json.dumps(d))