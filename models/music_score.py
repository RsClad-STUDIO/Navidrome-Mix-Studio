"""楽曲スコアと、選曲パイプライン内で共有する評価情報を保持するモデル。"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from models.song import Song


@dataclass
class MusicScore:
    """1曲の評価値・補正値・元Songをまとめて保持する。"""

    song_id: str
    title: str
    artist: str
    album: Optional[str] = None
    play_count: int = 0
    last_played: Optional[datetime] = None

    # ScoringCalculator が設定する未補正の評価成分（各0～100、randomは0～10）。
    recency_score: float = 0.0
    popularity_score: float = 0.0
    favorite_score: float = 0.0
    random_score: float = 0.0

    # ScoringCalculator の合計点。RotationCalculator が補正する。
    total_score: float = 0.0
    rotation_penalty: float = 0.0
    rotation_exempt: bool = False

    # 選曲戦略がSong本体を参照するための明示的な関連。
    song: Optional[Song] = field(default=None, repr=False, compare=False)
