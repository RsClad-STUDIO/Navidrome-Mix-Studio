from typing import List, Dict, Any
from .base_strategy import BaseStrategy
from models.song import Song
from models.music_score import MusicScore
from engine.non_favorite_recommender import NonFavoriteRecommender

class DiscoveryStrategy(BaseStrategy):
    def generate(self, scored_list: List[MusicScore], days_map: Dict[str, int], limit: int, clean_pool: List[Song], context: Dict[str, Any]) -> List[Song]:
        # 候補：再生回数 3回未満
        unheard_pool = [s for s in clean_pool if s.play_count < 3 and not s.starred]
        actual_favorites = [ms.song for ms in scored_list if ms.song.starred]
        fav_artists = {s.artist for s in actual_favorites if s.artist}

        discovery_context = context.copy()
        discovery_context["discovery_mode"] = True 
        
        # 大量に候補を取得 (余裕を持って 5倍)
        recs, stats = NonFavoriteRecommender.get_recommendations(unheard_pool, actual_favorites, limit * 5, discovery_context)
        
        raw_candidates = []
        n_similarity_limit = int(limit * 0.4) 
        sim_count = 0
        
        # 高速化のための Set
        seen_ids = set()

        for s in recs:
            if s.id in seen_ids: continue
            is_sim = s.artist in fav_artists
            
            if is_sim:
                if sim_count < n_similarity_limit:
                    s.selection_source = "similarity"
                    raw_candidates.append(s)
                    seen_ids.add(s.id)
                    sim_count += 1
            else:
                s.selection_source = "discovery"
                raw_candidates.append(s)
                seen_ids.add(s.id)
            
            if len(raw_candidates) >= limit * 3:
                break

        context["disc_stats"] = stats
        return raw_candidates