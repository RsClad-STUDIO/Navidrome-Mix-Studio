import random
from typing import List, Dict, Any
from .base_strategy import BaseStrategy
from models.song import Song
from models.music_score import MusicScore

class DailyStrategy(BaseStrategy):
    def generate(self, scored_list: List[MusicScore], days_map: Dict[str, int], limit: int, clean_pool: List[Song], context: Dict[str, Any]) -> List[Song]:
        raw_candidates = []
        # 比率の計算
        n_fav = int(limit * 0.32)
        n_recent = int(limit * 0.28)
        n_boost = int(limit * 0.16)
        n_past = int(limit * 0.12)
        
        # 好みの核を特定 (上位10曲から)
        core_pool = [ms for ms in scored_list if ms.song.starred or days_map.get(ms.song_id, 999) <= 30][:10]
        core_artists = {ms.artist for ms in core_pool}
        core_albums = {ms.album for ms in core_pool}

        # 1. お気に入り枠
        fav_pool = [ms for ms in scored_list if ms.song.starred]
        for ms in fav_pool[:n_fav]:
            ms.song.selection_source = "favorite"
            raw_candidates.append(ms.song)

        # 2. 最近聴いた非お気に入り枠
        recent_pool = [ms for ms in scored_list if not ms.song.starred and days_map.get(ms.song_id, 999) <= 30]
        for ms in recent_pool[:n_recent]:
            ms.song.selection_source = "recent"
            raw_candidates.append(ms.song)

        # 3. ブースト枠 (関連曲)
        boost_pool = [ms for ms in scored_list if (ms.artist in core_artists or ms.album in core_albums) 
                      and ms.song_id not in [s.id for s in raw_candidates] and days_map.get(ms.song_id, 999) > 30]
        for ms in boost_pool[:n_boost]:
            ms.song.selection_source = "similarity_album" if ms.album in core_albums else "similarity_artist"
            raw_candidates.append(ms.song)

        # 4. 懐かしのヘビロテ枠
        past_pool = [ms for ms in scored_list if ms.play_count >= 15 and days_map.get(ms.song_id, 999) > 60 
                     and ms.song_id not in [s.id for s in raw_candidates]]
        for ms in past_pool[:n_past]:
            ms.song.selection_source = "play_count"
            raw_candidates.append(ms.song)

        # 5. 発見枠 (残りを中堅スコアから)
        needed = limit - len(raw_candidates)
        if needed > 0:
            disc_pool = [ms for ms in scored_list[50:1000] if ms.song_id not in [s.id for s in raw_candidates]]
            for ms in disc_pool[:needed]:
                ms.song.selection_source = "discovery"
                raw_candidates.append(ms.song)

        return raw_candidates