"""再生履歴情報を表すデータモデル。"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class HistoryEntry:
    """再生履歴（Scrobble / Play History）エントリーを表すクラス。"""

    song_id: str
    title: str
    artist: str
    album: Optional[str] = None
    played_at: Optional[datetime] = None
    play_count: int = 1

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        """APIレスポンスの辞書データからHistoryEntryインスタンスを生成します。

        Args:
            data (Dict[str, Any]): Subsonic APIのplaylog/scrobble等オブジェクト辞書。

        Returns:
            HistoryEntry: 生成されたHistoryEntryインスタンス。
        """
        played_at_val: Optional[datetime] = None
        if "time" in data:
            try:
                # Subsonic APIのタイムスタンプ (ミリ秒単位 Unix Time または ISO文字列)
                time_val = data["time"]
                if isinstance(time_val, (int, float)):
                    played_at_val = datetime.fromtimestamp(time_val / 1000.0)
                elif isinstance(time_val, str):
                    played_at_val = datetime.fromisoformat(
                        time_val.replace("Z", "+00:00")
                    )
            except Exception:
                played_at_val = None

        return cls(
            song_id=data.get("id", data.get("songId", "")),
            title=data.get("title", "Unknown Title"),
            artist=data.get("artist", "Unknown Artist"),
            album=data.get("album"),
            played_at=played_at_val,
            play_count=data.get("playCount", 1),
        )