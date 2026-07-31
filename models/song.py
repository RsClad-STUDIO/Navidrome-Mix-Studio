"""楽曲情報を表現するモデルモジュール。"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class Song:
    """楽曲の基本データおよびメタデータを保持するクラス。"""

    id: str
    title: str
    artist: str
    album: Optional[str] = None
    year: Optional[int] = None
    play_count: int = 0
    starred: bool = False
    duration: int = 0
    last_played: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Song":
        """APIレスポンスの辞書データからSongインスタンスを生成します。"""
        starred_raw = data.get("starred") or data.get("isStarred")
        starred = bool(starred_raw)

        # 再生日時のパース ＆ タイムゾーン情報の除去 (tzinfo=None)
        last_played_raw = data.get("played") or data.get("lastPlayed")
        last_played = None
        if last_played_raw:
            try:
                dt = datetime.fromisoformat(str(last_played_raw).replace("Z", "+00:00"))
                # タイムゾーンを除去して naive datetime 化
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                last_played = dt
            except Exception:
                last_played = None

        return cls(
            id=str(data.get("id", "")),
            title=str(data.get("title", "Unknown Title")),
            artist=str(data.get("artist", "Unknown Artist")),
            album=data.get("album"),
            year=data.get("year"),
            play_count=int(data.get("playCount", 0)),
            starred=starred,
            duration=int(data.get("duration", 0)),
            last_played=last_played,
        )