import random
from .base_score import BaseScore
from models.song import Song

class RandomScore(BaseScore):
    def calculate(self, song: Song, **kwargs) -> float:
        # 0.0 - 10.0 の範囲で乱数を付与
        return random.uniform(0.0, 10.0)