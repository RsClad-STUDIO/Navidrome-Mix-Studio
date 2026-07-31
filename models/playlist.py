"""プレイリスト情報を表すデータモデル。"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from models.song import Song


@dataclass
class Playlist:
    """プレイリストのデータモデルクラス。"""

    id: str
    name: str
    song_count: int = 0
    duration: int = 0
    public: bool = False
    owner: Optional[str] = None
    songs: List[Song] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Playlist":
        """APIレスポンスの辞書データからPlaylistインスタンスを生成します。

        Args:
            data (Dict[str, Any]): Subsonic APIのplaylistオブジェクト辞書。

        Returns:
            Playlist: 生成されたPlaylistインスタンス。
        """
        raw_songs = data.get("entry", [])
        songs = [Song.from_dict(s) for s in raw_songs] if raw_songs else []

        return cls(
            id=data.get("id", ""),
            name=data.get("name", "Untitled Playlist"),
            song_count=data.get("songCount", len(songs)),
            duration=data.get("duration", 0),
            public=data.get("public", False),
            owner=data.get("owner"),
            songs=songs,
        )