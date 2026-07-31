"""アーティスト情報を表すデータモデル。"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Artist:
    """アーティストのデータモデルクラス。"""

    id: str
    name: str
    album_count: int = 0
    artist_image_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Artist":
        """APIレスポンスの辞書データからArtistインスタンスを生成します。

        Args:
            data (Dict[str, Any]): Subsonic APIのartistオブジェクト辞書。

        Returns:
            Artist: 生成されたArtistインスタンス。
        """
        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Unknown Artist"),
            album_count=data.get("albumCount", 0),
            artist_image_url=data.get("artistImageUrl"),
        )