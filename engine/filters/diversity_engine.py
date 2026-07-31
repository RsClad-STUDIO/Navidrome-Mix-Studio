from typing import List, Dict, Set
from models.song import Song
from .album_filter import AlbumFilter
from .artist_filter import ArtistFilter
from .version_filter import VersionFilter

class DiversityEngine:
    """多様性確保のための統合フィルタリングエンジン。"""

    def __init__(self, **kwargs) -> None:
        self._version_filter = VersionFilter(kwargs)
        self._album_filter = AlbumFilter(
            level=kwargs.get("album_level", "Normal"),
            filter_versions=kwargs.get("filter_versions", True)
        )
        self._artist_filter = ArtistFilter(
            level=kwargs.get("artist_level", "Normal")
        )
        # 実際に「このフィルタによって」除外された楽曲IDの集合
        self._removed_ids: Dict[str, Set[str]] = {
            "version": set(),
            "album": set(),
            "artist": set()
        }

    def apply(self, songs: List[Song]) -> List[Song]:
        """フィルタを適用し、それぞれの段階で『新規に』除外された曲を追跡します。"""
        # 1. Version Filter
        step1 = []
        for s in songs:
            if self._version_filter.is_suppressed(s):
                self._removed_ids["version"].add(s.id)
            else:
                step1.append(s)
        
        # 2. Album Filter
        count_before_alb = len(step1)
        step2 = self._album_filter.apply(step1)
        removed_in_alb = [s for s in step1 if s not in step2]
        for s in removed_in_alb:
            self._removed_ids["album"].add(s.id)
        
        # 3. Artist Filter
        step3 = self._artist_filter.apply(step2)
        removed_in_art = [s for s in step2 if s not in step3]
        for s in removed_in_art:
            self._removed_ids["artist"].add(s.id)
        
        return step3

    def get_summary_log(self) -> str:
        """除外されたユニークな曲数を集計してログを生成。"""
        return (f"Version Filter Removed   : {len(self._removed_ids['version'])}\n"
                f"Album Filter Removed     : {len(self._removed_ids['album'])}\n"
                f"Artist Filter Removed    : {len(self._removed_ids['artist'])}")

    def is_suppressed_version(self, song: Song) -> bool:
        """
        互換性維持のためのメソッド。
        NonFavoriteRecommender がインスト/ライブ盤の除外判定に使用します。
        """
        return self._version_filter.is_suppressed(song)