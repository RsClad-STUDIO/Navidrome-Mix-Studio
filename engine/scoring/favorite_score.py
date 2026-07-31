from .base_score import BaseScore
from models.song import Song

class FavoriteScore(BaseScore):
    def calculate(self, song: Song, **kwargs) -> float:
        return 100.0 if song.starred else 0.0