"""Mix生成サービスのエントリポイント。"""

from typing import List, Optional, Any  # Any を追加
from models.statistics_data import StatisticsData
from models.library_profile import LibraryProfile
from models.song import Song

class MixService:
    def __init__(self, generator, playlist_service, library_analyzer=None, preset_service=None, logger=None) -> None:
        """
        MixServiceを初期化します。
        """
        self._generator = generator
        self._playlist_service = playlist_service
        self._library_analyzer = library_analyzer
        self._preset_service = preset_service
        self._logger = logger

    def generate_by_preset(self, preset_name: str, limit: int = 25, adaptive: bool = True, **kwargs) -> List[Song]:
        """プリセットに基づき戦略的なMixを生成します。"""
        return self._generator.generate_mix(
            preset_name=preset_name,
            limit=limit,
            adaptive_mode=adaptive,
            **kwargs
        )

    def analyze_library(self, songs: List[Song], force_refresh: bool = False) -> LibraryProfile:
        """
        統計ページから呼ばれるメソッド。
        実際の計算は LibraryAnalyzer に委譲します。
        """
        if self._library_analyzer:
            return self._library_analyzer.analyze_library(songs, force_refresh=force_refresh)
        
        return LibraryProfile()

    def get_last_stats(self) -> Optional[StatisticsData]:
        """直近の生成結果（StatisticsData）を返します。"""
        return getattr(self._generator, "_last_stats", None)

    def get_last_scored_list(self) -> List[Any]:
        """直近の生成で使用された全楽曲のスコア詳細（MusicScoreのリスト）を返します。"""
        return getattr(self._generator, "_last_scored_list", [])

    def save_to_navidrome(self, mix_name: str, songs: List[Song]):
        """生成されたMixをNavidromeのプレイリストとして保存します。"""
        if self._playlist_service:
            return self._playlist_service.create_mix_playlist(mix_name, songs)
        return None