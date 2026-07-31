import math
from .base_score import BaseScore
from models.song import Song

class PlayCountScore(BaseScore):
    def calculate(self, song: Song, **kwargs) -> float:
        # kwargs からライブラリの最大再生数を取得
        max_p = kwargs.get("max_play_count", 1)
        if max_p <= 0: max_p = 1
        
        count = song.play_count
        log_max = math.log10(max_p + 1)
        
        # min(log10(count + 1) / log10(max + 1), 1.0) * 100
        score = (math.log10(count + 1) / log_max) * 100.0
        return min(score, 100.0)