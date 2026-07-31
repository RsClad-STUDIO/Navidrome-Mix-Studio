"""APIレスポンスや計算結果のJSONキャッシュを管理するモジュール。"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from core.exceptions import CacheError


class CacheManager:
    """JSONファイルベースのキャッシュ管理クラス。"""

    def __init__(
        self,
        cache_dir: str = "cache",
        expire_hours: int = 24,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Args:
            cache_dir (str): キャッシュ保存先フォルダ
            expire_hours (int): キャッシュのデフォルト有効期間（時間）
            logger (Optional[logging.Logger]): ロガー
        """
        self._cache_dir = Path(cache_dir)
        self._expire_hours = expire_hours
        self._logger = logger or logging.getLogger(__name__)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Optional[Any]:
        """指定されたキーのデータ（有効期限内）を取得します。破損時は自動削除します。"""
        file_path = self._cache_dir / f"{key}.json"
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            created_at_str = data.get("_created_at")
            if not created_at_str:
                self.delete(key)
                return None

            created_at = datetime.fromisoformat(created_at_str)
            if datetime.now() - created_at > timedelta(hours=self._expire_hours):
                self._logger.debug(f"Cache expired for key: {key}")
                self.delete(key)
                return None

            return data.get("payload")
        except Exception as e:
            self._logger.warning(f"Failed to read cache '{key}', deleting: {e}")
            self.delete(key)
            return None

    def set(self, key: str, payload: Any) -> bool:
        """指定されたキーでデータをJSON形式で保存します。"""
        file_path = self._cache_dir / f"{key}.json"
        data = {
            "_created_at": datetime.now().isoformat(),
            "payload": payload,
        }
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            self._logger.error(f"Failed to write cache '{key}': {e}")
            return False

    def delete(self, key: str) -> None:
        """指定されたキーのキャッシュファイルを削除します。"""
        file_path = self._cache_dir / f"{key}.json"
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                self._logger.error(f"Failed to delete cache '{key}': {e}")

    def clear_all(self) -> None:
        """全キャッシュファイルを削除します。"""
        for file in self._cache_dir.glob("*.json"):
            try:
                file.unlink()
            except Exception as e:
                self._logger.error(f"Failed to delete {file}: {e}")