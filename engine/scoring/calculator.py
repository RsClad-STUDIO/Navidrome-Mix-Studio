from typing import Dict, Optional
from datetime import datetime

from models.song import Song
from .recent_score import RecentScore
from .playcount_score import PlayCountScore
from .favorite_score import FavoriteScore
from .random_score import RandomScore


class ScoringCalculator:
    """各評価成分を計算し、MusicScore用の内訳と総合点を返す。"""

    def __init__(self, mix_type: str = "Favorite") -> None:
        self._recent = RecentScore()
        self._playcount = PlayCountScore()
        self._favorite = FavoriteScore()
        self._random = RandomScore()

        # 既存Phase 10.xの配点を維持する。
        self.w_recent = 0.25
        self.w_play_count = 0.30
        self.w_favorite = 0.35 if mix_type == "Favorite" else 0.15
        self.w_diversity_base = 0.10

    def calculate_components(
        self,
        song: Song,
        max_play_count: int,
        now: datetime,
        days_since_last_play: Optional[int] = None,
    ) -> Dict[str, float]:
        """評価成分を個別に計算し、合計点とともに返す。"""
        recency = self._recent.calculate(
            song, days_since_last_play=days_since_last_play
        )
        popularity = self._playcount.calculate(
            song, max_play_count=max_play_count
        )
        favorite = self._favorite.calculate(song)
        random_value = self._random.calculate(song)

        total = (
            recency * self.w_recent
            + popularity * self.w_play_count
            + favorite * self.w_favorite
            + 100.0 * self.w_diversity_base
            + random_value
        )

        return {
            "recency_score": recency,
            "popularity_score": popularity,
            "favorite_score": favorite,
            "random_score": random_value,
            "total_score": max(0.0, total),
        }

    def calculate_base_score(
        self,
        song: Song,
        max_play_count: int,
        now: datetime,
        days_since_last_play: Optional[int] = None,
    ) -> float:
        """既存呼び出しとの互換性を保つ総合点API。"""
        return self.calculate_components(
            song, max_play_count, now, days_since_last_play
        )["total_score"]
