"""楽曲スコアと、選曲パイプライン内で共有する評価情報を保持するモデル。"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from models.song import Song


@dataclass
class MusicScore:
    """1曲の評価値・補正値・元Songをまとめて保持する。"""

    song_id: str
    title: str
    artist: str
    song: Song
    album: Optional[str] = None
    play_count: int = 0
    last_played: Optional[datetime] = None

    # ScoringCalculator が設定する未補正の評価成分。
    # recency / popularity / favorite は0～100、randomは0～10。
    recency_score: float = 0.0
    popularity_score: float = 0.0
    favorite_score: float = 0.0
    random_score: float = 0.0

    # ScoringCalculatorの合計点をRotationCalculatorが補正する。
    total_score: float = 0.0
    rotation_penalty: float = 0.0
    rotation_exempt: bool = False
