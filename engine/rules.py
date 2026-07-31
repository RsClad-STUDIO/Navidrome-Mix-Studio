"""Mix生成における選曲ルール（フィルタリング・スコアリング）を定義するモジュール。"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from models.song import Song
from engine.filters.diversity_engine import DiversityEngine


class IMixRule(ABC):
    """Mix選曲ルールの抽象インターフェースクラス。"""

    @abstractmethod
    def apply(
        self, songs: List[Song], context_data: Dict[str, Any]
    ) -> List[Song]:
        pass


class RecentRule(IMixRule):
    """最近再生された楽曲を優先選曲するルール。"""

    def apply(
        self, songs: List[Song], context_data: Dict[str, Any]
    ) -> List[Song]:
        recent_ids: List[str] = context_data.get("recent_ids", [])
        if not recent_ids:
            return songs

        song_map = {s.id: s for s in songs}
        result = [song_map[sid] for sid in recent_ids if sid in song_map]
        remaining = [s for s in songs if s.id not in set(recent_ids)]
        return result + remaining


class PopularRule(IMixRule):
    """よく聴かれている（再生回数が多い）楽曲を優先選曲するルール。"""

    def apply(
        self, songs: List[Song], context_data: Dict[str, Any]
    ) -> List[Song]:
        play_counts: Dict[str, int] = context_data.get("play_counts", {})
        return sorted(
            songs, key=lambda s: play_counts.get(s.id, s.play_count), reverse=True
        )


class DiscoveryRule(IMixRule):
    """あまり再生されていない（または未再生の）楽曲を優先抽出するルール。"""

    def apply(
        self, songs: List[Song], context_data: Dict[str, Any]
    ) -> List[Song]:
        play_counts: Dict[str, int] = context_data.get("play_counts", {})
        return sorted(
            songs,
            key=lambda s: (
                play_counts.get(s.id, s.play_count),
                not getattr(s, "starred", False),
            ),
        )


class EraRule(IMixRule):
    """特定の年代・範囲の年で楽曲をフィルターするルール。"""

    def __init__(self, start_year: int, end_year: Optional[int] = None) -> None:
        self.start_year = start_year
        self.end_year = end_year or start_year

    def apply(
        self, songs: List[Song], context_data: Dict[str, Any]
    ) -> List[Song]:
        return [
            s for s in songs if s.year and self.start_year <= s.year <= self.end_year
        ]


class VersionFilterRule(IMixRule):
    """Instrumental / Remix 等の同一楽曲バリエーションをフィルタリング・抑制するルール。"""

    def apply(
        self, songs: List[Song], context_data: Dict[str, Any]
    ) -> List[Song]:
        seen_titles = set()
        filtered = []
        for s in songs:
            norm_title = DiversityEngine.normalize_title(s.title)
            if norm_title not in seen_titles or not DiversityEngine.is_version_variant(s):
                filtered.append(s)
                seen_titles.add(norm_title)
        return filtered


class NoDuplicateRule(IMixRule):
    """重複した楽曲IDを除外するルール。"""

    def apply(
        self, songs: List[Song], context_data: Dict[str, Any]
    ) -> List[Song]:
        seen = set()
        unique_songs = []
        for s in songs:
            if s.id not in seen:
                unique_songs.append(s)
                seen.add(s.id)
        return unique_songs