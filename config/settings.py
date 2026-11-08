"""設定ファイルの読み書きおよびデフォルト値を管理するモジュール。"""

import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from utils.credential_store import WindowsCredentialStore


class Settings:
    """JSON設定とOS資格情報ストアを連携して管理するクラス。"""

    DEFAULT_SETTINGS: Dict[str, Any] = {
        "language": "ja",
        "connection": {"server_url": "", "username": ""},
        "window": {"width": 1100, "height": 700, "maximized": False},
        "scheduler": {
            "enabled": False, "mode": "daily", "time": "07:00",
            "interval_hours": 6,
        },
        "cache": {"enabled": True, "expire_hours": 24},
        "mix": {
            "default_count": 50, "auto_update": False,
            "default_type": "Recent",
        },
    }

    CREDENTIAL_PREFIX = "NavidromeMixStudio"

    def __init__(self, filepath: str = "config.json", credential_store=None) -> None:
        self._filepath = Path(filepath)
        self._credential_store = credential_store or WindowsCredentialStore()
        self._data: Dict[str, Any] = {}
        self._known_credential_targets = set()
        self.load()

    def load(self) -> None:
        """設定を読み込み、旧形式の平文パスワードを資格情報ストアへ移行します。"""
        self._data = self._deep_copy(self.DEFAULT_SETTINGS)
        self._known_credential_targets.clear()
        if self._filepath.exists():
            try:
                with open(self._filepath, "r", encoding="utf-8") as file:
                    file_data = json.load(file)
                if isinstance(file_data, dict):
                    self._merge_dict(self._data, file_data)
            except (OSError, json.JSONDecodeError):
                # 壊れた設定を空設定で上書きしないよう、読み込み失敗は通知します。
                raise

        migration_needed = False
        profiles = self._data.get("profiles", [])
        if isinstance(profiles, list):
            for profile_index, profile in enumerate(profiles):
                if not isinstance(profile, dict):
                    continue
                target = profile.get("credential_target")
                if "password" in profile:
                    password = str(profile.pop("password") or "")
                    if password:
                        target = target or self._new_target()
                        self._credential_store.set_password(target, password)
                        profile["credential_target"] = target
                    else:
                        profile.pop("credential_target", None)
                    profile["password"] = password
                    migration_needed = True
                elif target:
                    profile["password"] = (
                        self._credential_store.get_password(target) or ""
                    )
                if target:
                    self._known_credential_targets.add(target)

        connection = self._data.setdefault("connection", {})
        if isinstance(connection, dict):
            target = connection.get("credential_target")
            if "password" in connection:
                password = str(connection.pop("password") or "")
                if password:
                    target = target or self._new_target()
                    self._credential_store.set_password(target, password)
                    connection["credential_target"] = target
                else:
                    connection.pop("credential_target", None)
                connection["password"] = password
                migration_needed = True
            elif target:
                connection["password"] = (
                    self._credential_store.get_password(target) or ""
                )
            if target:
                self._known_credential_targets.add(target)

        if migration_needed:
            self.save()

    def save(self) -> None:
        """認証情報を資格情報ストアへ保存し、秘密情報を除いたJSONを原子的に書き込みます。"""
        persisted = self._deep_copy(self._data)
        new_targets = set()

        profiles = persisted.get("profiles", [])
        if isinstance(profiles, list):
            for profile_index, profile in enumerate(profiles):
                if not isinstance(profile, dict):
                    continue
                password = str(profile.pop("password", "") or "")
                target = profile.get("credential_target")
                if password:
                    target = target or self._new_target()
                    self._credential_store.set_password(target, password)
                    profile["credential_target"] = target
                    source_profiles = self._data.get("profiles", [])
                    if isinstance(source_profiles, list) and profile_index < len(source_profiles):
                        source_profiles[profile_index]["credential_target"] = target
                if target:
                    new_targets.add(target)

        connection = persisted.get("connection", {})
        if isinstance(connection, dict):
            password = str(connection.pop("password", "") or "")
            target = connection.get("credential_target")
            if password:
                target = target or self._new_target()
                self._credential_store.set_password(target, password)
                connection["credential_target"] = target
                self._data.setdefault("connection", {})["credential_target"] = target
            if target:
                new_targets.add(target)

        self._filepath.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=self._filepath.parent,
                prefix=f".{self._filepath.name}.", suffix=".tmp",
                delete=False,
            ) as file:
                temp_path = Path(file.name)
                json.dump(persisted, file, indent=2, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_path, self._filepath)
        except Exception:
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise

        # 設定ファイルの更新に成功した後で、削除済みプロファイルの資格情報を整理します。
        for target in self._known_credential_targets - new_targets:
            try:
                self._credential_store.delete_password(target)
            except Exception:
                pass
        self._known_credential_targets = new_targets

    def get(self, key_path: str, default: Any = None) -> Any:
        """ドット区切りのキーパスで値を取得します。"""
        value = self._data
        for key in key_path.split("."):
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def set(self, key_path: str, value: Any) -> None:
        """ドット区切りのキーパスで値を設定します。"""
        keys = key_path.split(".")
        value_dict = self._data
        for key in keys[:-1]:
            if key not in value_dict or not isinstance(value_dict[key], dict):
                value_dict[key] = {}
            value_dict = value_dict[key]
        value_dict[keys[-1]] = value

    def _new_target(self) -> str:
        return f"{self.CREDENTIAL_PREFIX}/{uuid.uuid4()}"

    def _merge_dict(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dict(base[key], value)
            else:
                base[key] = value

    def _deep_copy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return json.loads(json.dumps(data))
