"""推薦エンジンのスコア計算重み（Weight）を自動適応・管理するモジュール。"""

from dataclasses import asdict, dataclass
from typing import Any, Dict
from models.library_profile import LibraryProfile
from dataclasses import dataclass

@dataclass
class RecommendationWeights:
    """各種スコアリングの重みパラメーター。"""

    weight_favorite: float = 0.25
    weight_recency: float = 0.20
    weight_popularity: float = 0.20
    weight_discovery: float = 0.20
    weight_random: float = 0.15

    # Rotation 用ペナルティ率（追加）
    rotation_penalty_recent: float = -0.15  # 直近1回 (-15%)
    rotation_penalty_old: float = -0.08    # 2〜3回前 (-8%)

    def normalize(self) -> "RecommendationWeights":
        """合計値が 1.0 になるよう正規化します。"""
        total = (
            self.weight_favorite
            + self.weight_recency
            + self.weight_popularity
            + self.weight_discovery
            + self.weight_random
        )
        if total <= 0:
            return RecommendationWeights()
        return RecommendationWeights(
            weight_favorite=self.weight_favorite / total,
            weight_recency=self.weight_recency / total,
            weight_popularity=self.weight_popularity / total,
            weight_discovery=self.weight_discovery / total,
            weight_random=self.weight_random / total,
        )

    @classmethod
    def create_adaptive_weights(cls, profile: LibraryProfile) -> "RecommendationWeights":
        """ライブラリプロファイルから自動適応した最適な重みを生成します。"""
        # Discovery は補助要素とし、Favorite や Recency を上回らないよう自動算出
        fav_w = min(0.35, max(0.15, profile.favorite_ratio / 100.0 + 0.1))
        rec_w = 0.25
        pop_w = 0.20
        disc_w = min(0.15, max(0.05, 1.0 - (profile.favorite_ratio / 100.0)))
        rand_w = 0.10

        weights = cls(
            weight_favorite=fav_w,
            weight_recency=rec_w,
            weight_popularity=pop_w,
            weight_discovery=disc_w,
            weight_random=rand_w,
        )
        return weights.normalize()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecommendationWeights":
        return cls(
            weight_favorite=data.get("weight_favorite", 0.25),
            weight_recency=data.get("weight_recency", 0.20),
            weight_popularity=data.get("weight_popularity", 0.20),
            weight_discovery=data.get("weight_discovery", 0.20),
            weight_random=data.get("weight_random", 0.15),
        )