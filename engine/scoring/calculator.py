from typing import Dict, Optional
from datetime import datetime

from models.song import Song
from .recent_score import RecentScore
from .playcount_score import PlayCountScore
from .favorite_score import FavoriteScore
from .random_score import RandomScore


class ScoringCalculator:
    """各評価成分を計算し、MusicScore用の内訳と総合点を返す。"""

    def __init__(
        self,
        mix_type: str = "Favorite",
        adaptive_mode: bool = True,
        favorite_ratio: float = 0.0,
        history_coverage: float = 0.0,
    ) -> None:
        self._recent = RecentScore()
        self._playcount = PlayCountScore()
        self._favorite = FavoriteScore()
        self._random = RandomScore()

        # Fixed mode preserves the existing preset-specific scoring profile.
        if not adaptive_mode:
            self.w_recent = 0.25
            self.w_play_count = 0.30
            self.w_favorite = 0.35 if mix_type == "Favorite" else 0.15
            self.w_diversity_base = 0.10
        else:
            # Adapt weights to the actual library: avoid overvaluing favorites
            # in libraries with very few starred tracks and reduce recency
            # dependence when play-history coverage is sparse.
            self.w_favorite = min(0.35, max(0.15, favorite_ratio + 0.10))
            if mix_type == "Favorite":
                self.w_favorite = max(self.w_favorite, 0.30)
            self.w_recent = 0.25 if history_coverage >= 0.5 else 0.10
            self.w_play_count = 0.20
            self.w_diversity_base = 0.10
            total_weight = (
                self.w_recent
                + self.w_play_count
                + self.w_favorite
                + self.w_diversity_base
            )
            self.w_recent /= total_weight
            self.w_play_count /= total_weight
            self.w_favorite /= total_weight
            self.w_diversity_base /= total_weight

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
