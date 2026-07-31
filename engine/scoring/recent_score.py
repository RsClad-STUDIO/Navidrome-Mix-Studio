import math
from .base_score import BaseScore
from models.song import Song

class RecentScore(BaseScore):
    def calculate(self, song: Song, **kwargs) -> float:
        # kwargs から経過日数を取得（なければデフォルト90日）
        days = kwargs.get("days_since_last_play")
        if days is None:
            days = 90.0
        
        # 100 * exp(-days / 30)
        return 100.0 * math.exp(-days / 30.0)