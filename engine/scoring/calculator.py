from typing import Optional
from datetime import datetime
from models.song import Song
from .recent_score import RecentScore
from .playcount_score import PlayCountScore
from .favorite_score import FavoriteScore
from .random_score import RandomScore

class ScoringCalculator:
    """
    各スコア成分を統合して最終的な楽曲スコアを算出するオーケストレーター。
    アルゴリズム（重み付け）の変更なしに、構成要素のみを分離。
    """

    def __init__(self, mix_type: str = "Favorite") -> None:
        # インスタンスの保持
        self._recent = RecentScore()
        self._playcount = PlayCountScore()
        self._favorite = FavoriteScore()
        self._random = RandomScore()

        # 重み設定 (Phase 10.x 仕様を厳守)
        self.w_recent = 0.25
        self.w_play_count = 0.30
        self.w_favorite = 0.35 if mix_type == "Favorite" else 0.15
        self.w_diversity_base = 0.10  # 基礎点
        
    def calculate_base_score(self, song: Song, max_play_count: int, now: datetime, 
                             days_since_last_play: Optional[int] = None) -> float:
        """
        全成分を合算して 0.0 - 100.0+ のスコアを算出します。
        """
        # 各成分の計算
        s_recent = self._recent.calculate(song, days_since_last_play=days_since_last_play)
        s_pc = self._playcount.calculate(song, max_play_count=max_play_count)
        s_fav = self._favorite.calculate(song)
        s_rand = self._random.calculate(song)
        
        # 加重合計 (アルゴリズム不変)
        final_score = (
            (s_recent * self.w_recent) +
            (s_pc * self.w_play_count) +
            (s_fav * self.w_favorite) +
            (100.0 * self.w_diversity_base) + # 基礎多様性スコア
            s_rand  # Randomは仕様通り直接加算
        )
        
        return max(0.0, final_score)