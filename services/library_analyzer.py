"""全ライブラリを多角的に解析し、LibraryProfile を作成・キャッシュするサービス。"""

from collections import Counter
import logging
from typing import List, Optional
from cache.cache_manager import CacheManager
from models.library_profile import LibraryProfile
from models.song import Song
from utils.title_normalizer import TitleNormalizer


class LibraryAnalyzer:
    """ライブラリの比率構成を算出・分析するアナライザー。"""

    CACHE_KEY = "library_profile_cache"

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._cache_manager = cache_manager
        self._logger = logger or logging.getLogger(__name__)

    def analyze_library(self, songs: List[Song], force_refresh: bool = False) -> LibraryProfile:
        """ライブラリ全体を解析し、キャッシュがあれば再利用してプロファイルを生成します。"""
        if not force_refresh and self._cache_manager:
            cached_data = self._cache_manager.get(self.CACHE_KEY)
            if cached_data and isinstance(cached_data, dict):
                self._logger.info("Retrieved LibraryProfile from cache.")
                return LibraryProfile.from_dict(cached_data)

        self._logger.info(f"Analyzing full library ({len(songs)} songs)...")
        total_songs = len(songs)
        if total_songs == 0:
            return LibraryProfile()

        artist_counts: Counter[str] = Counter()
        album_counts: Counter[str] = Counter()
        fav_count = 0
        year_known = 0
        year_unknown = 0
        version_count = 0
        inst_count = 0
        remix_count = 0
        live_count = 0

        for s in songs:
            artist = s.artist or "Unknown Artist"
            album = s.album or "Unknown Album"
            artist_counts[artist] += 1
            album_counts[album] += 1

            if getattr(s, "starred", False):
                fav_count += 1

            if s.year and s.year > 0:
                year_known += 1
            else:
                year_unknown += 1

            # Version 判定
            ver_info = TitleNormalizer.detect_versions(s.title)
            if any(ver_info.values()):
                version_count += 1
            
            # キー名を TitleNormalizer の戻り値に合わせる (is_ を取る)
            if ver_info.get("instrumental"):  # is_instrumental -> instrumental
                inst_count += 1
            if ver_info.get("remix"):         # is_remix -> remix
                remix_count += 1
            if ver_info.get("live"):          # is_live -> live
                live_count += 1

        artist_dist = {a: round((c / total_songs) * 100.0, 2) for a, c in artist_counts.items()}
        album_dist = {a: round((c / total_songs) * 100.0, 2) for a, c in album_counts.items()}

        profile = LibraryProfile(
            total_songs=total_songs,
            total_albums=len(album_counts),
            total_artists=len(artist_counts),
            favorite_count=fav_count,
            favorite_ratio=round((fav_count / total_songs) * 100.0, 2),
            artist_distribution=artist_dist,
            album_distribution=album_dist,
            artist_song_counts=dict(artist_counts),
            album_song_counts=dict(album_counts),
            year_known_count=year_known,
            year_unknown_count=year_unknown,
            year_known_ratio=round((year_known / total_songs) * 100.0, 2),
            year_unknown_ratio=round((year_unknown / total_songs) * 100.0, 2),
            version_count=version_count,
            version_ratio=round((version_count / total_songs) * 100.0, 2),
            instrumental_count=inst_count,
            remix_count=remix_count,
            live_count=live_count,
        )

        if self._cache_manager:
            self._cache_manager.set(self.CACHE_KEY, profile.to_dict())

        self._logger.info("Library analysis completed.")
        return profile