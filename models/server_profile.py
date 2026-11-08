from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ServerProfile:
    """サーバー接続設定を保持するプロファイルモデル。"""

    name: str
    url: str
    username: str
    password: str
    extra_settings: dict = field(default_factory=dict)
    credential_target: Optional[str] = None

    def to_dict(self) -> dict:
        # passwordはSettings.save()がWindows Credential Managerへ退避します。
        return {
            "name": self.name,
            "url": self.url,
            "username": self.username,
            "password": self.password,
            "credential_target": self.credential_target,
            "extra_settings": self.extra_settings,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ServerProfile":
        return cls(
            name=data.get("name", "Default"),
            url=data.get("url", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
            extra_settings=data.get("extra_settings", {}),
            credential_target=data.get("credential_target"),
        )


@dataclass
class ConnectionResult:
    """接続テストの結果を保持するデータクラス。"""

    success: bool
    version: str = ""
    username: str = ""
    song_count: int = 0
    response_time_ms: int = 0
    error_message: str = ""
