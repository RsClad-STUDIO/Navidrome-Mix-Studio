"""楽曲のスコアリング・評価データを保持するモデル。"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class MusicScore:
    """楽曲ごとの各種評価スコアおよび総合スコアを保持するクラス。"""

    song_id: str
    title: str
    artist: str
    album: Optional[str] = None
    play_count: int = 0
    last_played: Optional[datetime] = None
    recency_score: float = 0.0
    popularity_score: float = 0.0
    favorite_score: float = 0.0
    total_score: float = 0.0