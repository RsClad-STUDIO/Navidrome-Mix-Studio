import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from models.song import Song
from models.history import HistoryEntry

class HistoryService:
    """再生履歴の取得およびコンテキスト構築を担当するサービス。"""

    def __init__(self, client, logger: Optional[logging.Logger] = None) -> None:
        self._client = client
        self._logger = logger or logging.getLogger(__name__)

    def fetch_history(self, size: int = 2000) -> List[HistoryEntry]:
        """APIから生の履歴データを取得します。"""
        try:
            raw = self._client.get_history(size=size)
            return [HistoryEntry.from_dict(h) for h in raw]
        except Exception as e:
            self._logger.error(f"Failed to fetch history: {e}")
            return []

    def prepare_context(self, history: List[HistoryEntry], all_songs: List[Song], now: datetime) -> Dict[str, int]:
        """履歴APIと楽曲メタデータから再生経過日数マップを構築します。"""
        days_map: Dict[str, int] = {}

        # A: 履歴APIからの構築
        for h in history:
            sid = getattr(h, "song_id", None) or getattr(h, "id", None)
            p_at = getattr(h, "played_at", None) or getattr(h, "played", None)
            if sid and p_at:
                try:
                    dt = self._make_naive(p_at if isinstance(p_at, datetime) else datetime.fromisoformat(str(p_at).replace('Z', '+00:00')))
                    diff = (now - dt).days
                    if sid not in days_map or diff < days_map[sid]:
                        days_map[sid] = diff
                except Exception: continue

        # B: 楽曲メタデータからの再構築
        for s in all_songs:
            l_played = getattr(s, "last_played", None) or getattr(s, "lastPlayed", None)
            if l_played:
                try:
                    dt = self._make_naive(l_played if isinstance(l_played, datetime) else datetime.fromisoformat(str(l_played).replace('Z', '+00:00')))
                    diff = (now - dt).days
                    if s.id not in days_map or diff < days_map[s.id]:
                        days_map[s.id] = diff
                except Exception: continue

        return days_map

    @staticmethod
    def _make_naive(dt: datetime) -> datetime:
        """タイムゾーン情報を除去して比較可能な naive datetime に変換する。"""
        if dt and dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt