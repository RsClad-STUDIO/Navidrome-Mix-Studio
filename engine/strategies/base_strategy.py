from typing import List, Dict, Any
from models.song import Song
from models.music_score import MusicScore

class BaseStrategy:
    """選曲戦略の基底クラス"""
    def generate(self, scored_list: List[MusicScore], days_map: Dict[str, int], limit: int, clean_pool: List[Song], context: Dict[str, Any]) -> List[Song]:
        raise NotImplementedError