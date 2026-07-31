"""アルバム情報を表現するモデルモジュール。"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Album:
    """アルバムの基本データおよびメタデータを保持するクラス。"""

    id: str
    name: str
    artist: Optional[str] = None
    song_count: int = 0
    year: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Album":
        """APIレスポンスの辞書データからAlbumインスタンスを生成します。"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unknown Album"),
            artist=data.get("artist"),
            song_count=data.get("songCount", 0),
            year=data.get("year"),
        )