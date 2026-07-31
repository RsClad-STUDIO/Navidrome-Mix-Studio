"""ライブラリ比率に基づく適応型（Adaptive）期待値および減衰計算モジュール。"""

import math
from typing import Dict, List, Tuple
from models.library_profile import LibraryProfile
from models.song import Song


class AdaptiveEngine:
    """ライブラリの偏りを考慮した適応型スコア調整器。"""

    def __init__(self, profile: LibraryProfile) -> None:
        self._profile = profile

    def calculate_expected_counts(self, target_limit: int) -> Tuple[Dict[str, float], Dict[str, float]]:
        """目標曲数におけるアーティスト／アルバムごとの期待採用数を計算します。"""
        expected_artist: Dict[str, float] = {}
        for artist, ratio in self._profile.artist_distribution.items():
            expected_artist[artist] = max(1.0, (ratio / 100.0) * target_limit)

        expected_album: Dict[str, float] = {}
        for album, ratio in self._profile.album_distribution.items():
            expected_album[album] = max(1.0, (ratio / 100.0) * target_limit)

        return expected_artist, expected_album

    def calculate_soft_decay_penalty(
        self, current_count: int, expected_count: float, base_decay_factor: float = 0.85
    ) -> float:
        """期待値を超過した採用数に対し、指数の緩やかな減衰カーブでペナルティ（0.0〜100.0）を算出します。"""
        if current_count <= expected_count:
            return 0.0

        excess = current_count - expected_count
        # 指数減衰によるペナルティ計算（急激なカットは行わない）
        penalty_factor = 1.0 - math.pow(base_decay_factor, excess)
        return min(100.0, penalty_factor * 100.0)

    def filter_by_year_adaptive(
        self, candidates: List[Song], target_year: int, target_limit: int
    ) -> List[Song]:
        """年代フィルター有効時、指定年代曲を優先し不足分を Unknown Year から動的補填します。"""
        matched: List[Song] = []
        unknown_year: List[Song] = []

        for song in candidates:
            if song.year == target_year:
                matched.append(song)
            elif not song.year or song.year <= 0:
                unknown_year.append(song)

        if len(matched) >= target_limit:
            return matched[:target_limit]

        # 不足分を Unknown Year から補填
        needed = target_limit - len(matched)
        return matched + unknown_year[:needed]