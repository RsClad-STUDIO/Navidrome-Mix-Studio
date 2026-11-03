from typing import List, Dict, Any
from .base_strategy import BaseStrategy
from models.song import Song
from models.music_score import MusicScore
from .strategy_config import DailyMixConfig

class DailyStrategy(BaseStrategy):
    def generate(self, scored_list: List[MusicScore], days_map: Dict[str, int], limit: int, clean_pool: List[Song], context: Dict[str, Any]) -> List[Song]:
        raw_candidates = []
        # 比率の計算
        n_fav = int(limit * DailyMixConfig.RATIO_FAVORITE)
        n_recent = int(limit * DailyMixConfig.RATIO_RECENT)
        n_boost = int(limit * DailyMixConfig.RATIO_BOOST)
        n_past = int(limit * DailyMixConfig.RATIO_PAST)
        
        # 好みの核を特定 (上位10曲から)
        core_pool_size = max(1, int(context.get("requested_limit", limit // 2) * DailyMixConfig.CORE_POOL_RATIO))
        core_pool = [ms for ms in scored_list if ms.song.starred or days_map.get(ms.song_id, 999) <= DailyMixConfig.RECENT_DAYS_THRESHOLD][:core_pool_size]
        core_artists = {ms.artist for ms in core_pool}
        core_albums = {ms.album for ms in core_pool}

        # 1. お気に入り枠
        fav_pool = [ms for ms in scored_list if ms.song.starred]
        for ms in fav_pool[:n_fav]:
            ms.song.selection_source = "favorite"
            raw_candidates.append(ms.song)

        # 2. 最近聴いた非お気に入り枠
        recent_pool = [ms for ms in scored_list if not ms.song.starred and days_map.get(ms.song_id, 999) <= DailyMixConfig.RECENT_DAYS_THRESHOLD]
        for ms in recent_pool[:n_recent]:
            ms.song.selection_source = "recent"
            raw_candidates.append(ms.song)

        # 3. ブースト枠 (関連曲)
        boost_pool = [ms for ms in scored_list if (ms.artist in core_artists or ms.album in core_albums) 
                      and ms.song_id not in [s.id for s in raw_candidates] and days_map.get(ms.song_id, 999)  > DailyMixConfig.RECENT_DAYS_THRESHOLD]
        for ms in boost_pool[:n_boost]:
            ms.song.selection_source = "similarity_album" if ms.album in core_albums else "similarity_artist"
            raw_candidates.append(ms.song)

        # 4. 懐かしのヘビロテ枠
        past_pool = [ms for ms in scored_list if ms.play_count >= DailyMixConfig.PAST_PLAY_COUNT_MIN and days_map.get(ms.song_id, 999)  > DailyMixConfig.PAST_DAYS_THRESHOLD 
                     and ms.song_id not in [s.id for s in raw_candidates]]
        for ms in past_pool[:n_past]:
            ms.song.selection_source = "play_count"
            raw_candidates.append(ms.song)

        # 5. 発見枠 (残りを中堅スコアから)
        needed = limit - len(raw_candidates)
        if needed > 0:
            start = int(len(scored_list) * DailyMixConfig.DISCOVERY_START_RATIO)
            end = max(start + 1, int(len(scored_list) * DailyMixConfig.DISCOVERY_END_RATIO))
            disc_pool = [ms for ms in scored_list[start:end] if ms.song_id not in [s.id for s in raw_candidates]]
            for ms in disc_pool[:needed]:
                ms.song.selection_source = "discovery"
                raw_candidates.append(ms.song)

        return raw_candidates