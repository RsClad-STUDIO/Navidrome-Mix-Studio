"""再生履歴情報を表すデータモデル。"""

from dataclasses import dataclass
from datetime import datetime, timezone
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
        # getRecentPlayed uses "played"; getHistory commonly uses "time".
        time_val = data.get("played")
        if time_val is None:
            time_val = data.get("time")
        if time_val is not None:
            try:
                if isinstance(time_val, (int, float)):
                    # Subsonic timestamps are Unix milliseconds.
                    played_at_val = datetime.fromtimestamp(
                        time_val / 1000.0, tz=timezone.utc
                    )
                elif isinstance(time_val, str):
                    parsed = datetime.fromisoformat(
                        time_val.replace("Z", "+00:00")
                    )
                    played_at_val = (
                        parsed.replace(tzinfo=timezone.utc)
                        if parsed.tzinfo is None
                        else parsed.astimezone(timezone.utc)
                    )
            except (TypeError, ValueError, OverflowError):
                played_at_val = None

        return cls(
            song_id=str(data.get("id") or data.get("songId") or ""),
            title=data.get("title", "Unknown Title"),
            artist=data.get("artist", "Unknown Artist"),
            album=data.get("album"),
            played_at=played_at_val,
            play_count=data.get("playCount", 1),
        )