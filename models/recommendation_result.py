"""推薦結果のコンテナモデル。"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from models.song import Song

@dataclass
class RecommendationScoreDetail:
    favorite_score: float = 0.0
    recency_score: float = 0.0
    popularity_score: float = 0.0
    discovery_score: float = 0.0
    diversity_penalty: float = 0.0
    total_score: float = 0.0
    reasons: List[str] = field(default_factory=list)

@dataclass
class RecommendationItem:
    rank: int
    song: Song
    score_detail: RecommendationScoreDetail

    @property
    def main_reason(self) -> str:
        # スコアの詳細テキストを結合して表示
        return " | ".join(self.score_detail.reasons) if self.score_detail.reasons else "N/A"
@dataclass
class RecommendationResult:
    items: List[RecommendationItem]
    strategy_name: str = "Unknown"
    weights: Dict[str, float] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    candidate_count: int = 0
    processing_time_ms: float = 0.0
    average_score: float = 0.0