from typing import List, Dict, Set
from models.song import Song
from .album_filter import AlbumFilter
from .artist_filter import ArtistFilter
from .version_filter import VersionFilter


class DiversityEngine:
    """多様性確保のための統合フィルタリングエンジン。"""

    def __init__(self, **kwargs) -> None:
        self._version_filter = VersionFilter(kwargs)
        target_size = kwargs.get("target_size", 25)
        available_album_count = kwargs.get("available_album_count")
        available_artist_count = kwargs.get("available_artist_count")
        self._album_filter = AlbumFilter(
            level=kwargs.get("album_level", "Normal"),
            filter_versions=kwargs.get("filter_versions", True),
            target_size=target_size,
            available_album_count=available_album_count,
        )
        self._artist_filter = ArtistFilter(
            level=kwargs.get("artist_level", "Normal"),
            target_size=target_size,
            available_artist_count=available_artist_count,
        )
        self._removed_ids: Dict[str, Set[str]] = {
            "version": set(),
            "album": set(),
            "artist": set(),
        }

    def apply(self, songs: List[Song]) -> List[Song]:
        """設定に従ってバージョン・アルバム・アーティストの各フィルターを適用。"""
        step1 = []
        for song in songs:
            if self._version_filter.is_suppressed(song):
                self._removed_ids["version"].add(song.id)
            else:
                step1.append(song)

        step2 = self._album_filter.apply(step1)
        for song in step1:
            if song not in step2:
                self._removed_ids["album"].add(song.id)

        step3 = self._artist_filter.apply(step2)
        for song in step2:
            if song not in step3:
                self._removed_ids["artist"].add(song.id)

        return step3

    def get_summary_log(self) -> str:
        return (
            f"Version Filter Removed   : {len(self._removed_ids['version'])}\\n"
            f"Album Filter Removed     : {len(self._removed_ids['album'])}\\n"
            f"Artist Filter Removed    : {len(self._removed_ids['artist'])}"
        )

    @staticmethod
    def normalize_title(title: str) -> str:
        """Return a normalized title for duplicate-version comparisons."""
        from utils.title_normalizer import TitleNormalizer
        return TitleNormalizer.normalize(title)

    @staticmethod
    def is_version_variant(song: Song) -> bool:
        """Return whether a song title contains a recognized version marker."""
        from utils.title_normalizer import TitleNormalizer
        return any(TitleNormalizer.detect_versions(song.title).values())

    def is_suppressed_version(self, song: Song) -> bool:
        """互換性維持用のバージョン除外判定。"""
        return self._version_filter.is_suppressed(song)
