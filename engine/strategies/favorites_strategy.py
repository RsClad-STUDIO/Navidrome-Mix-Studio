from typing import List, Dict, Any
from .base_strategy import BaseStrategy
from models.song import Song
from models.music_score import MusicScore
from engine.non_favorite_recommender import NonFavoriteRecommender

class FavoritesStrategy(BaseStrategy):
    def generate(self, scored_list: List[MusicScore], days_map: Dict[str, int], limit: int, clean_pool: List[Song], context: Dict[str, Any]) -> List[Song]:
        raw_candidates = []
        favs = [ms for ms in scored_list if ms.song.starred]
        n_fav = int(limit * 0.8)
        
        for ms in favs[:n_fav]:
            ms.song.selection_source = "favorite"
            raw_candidates.append(ms.song)
            
        needed = limit - len(raw_candidates)
        if needed > 0:
            recs, _ = NonFavoriteRecommender.get_recommendations(clean_pool, raw_candidates, needed, context)
            raw_candidates.extend(recs)
            
        return raw_candidates