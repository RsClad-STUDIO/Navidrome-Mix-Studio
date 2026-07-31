from typing import List
from models.song import Song
from models.music_score import MusicScore

class RefillEngine:
    """プレイリストの曲数が不足している場合に、条件に合う楽曲を補充するエンジン。"""

    @staticmethod
    def refill(current_songs: List[Song], scored_list: List[MusicScore], 
               limit: int, preset_name: str, days_map: dict) -> List[Song]:
        """不足分を補充し、補充された曲のリストを別途返します。"""
        if len(current_songs) >= limit:
            return current_songs, []

        existing_ids = {s.id for s in current_songs}
        refilled_list = []
        final_list = list(current_songs)

        # 補充元の決定
        if "Discovery" in preset_name:
            fill_pool = [ms for ms in reversed(scored_list) if ms.play_count < 3]
            source_tag = "discovery"
        elif "Forgotten" in preset_name:
            fill_pool = [ms for ms in reversed(scored_list) if ms.play_count >= 1 and days_map.get(ms.song_id, 999) > 30]
            source_tag = "recent" 
        else:
            fill_pool = scored_list
            source_tag = "discovery"

        for ms in fill_pool:
            if ms.song_id not in existing_ids:
                ms.song.selection_source = source_tag
                final_list.append(ms.song)
                refilled_list.append(ms.song)
                existing_ids.add(ms.song_id)
            if len(final_list) >= limit:
                break
        
        return final_list, refilled_list