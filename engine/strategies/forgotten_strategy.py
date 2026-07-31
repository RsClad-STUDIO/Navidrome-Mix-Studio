from typing import List, Dict, Any
from .base_strategy import BaseStrategy
from models.song import Song
from models.music_score import MusicScore

class ForgottenStrategy(BaseStrategy):
    """
    Forgotten Favorites 戦略 (再生済みの曲のみに限定):
    1. お気に入りの中で、30日以上聴いていない曲を最優先。
    2. お気に入り以外で、再生回数が 1回以上 かつ 60日以上聴いていない曲を補充。
    """
    def generate(self, scored_list: List[MusicScore], days_map: Dict[str, int], limit: int, clean_pool: List[Song], context: Dict[str, Any]) -> List[Song]:
        raw_candidates = []
        
        # --- レイヤー1: 忘れ去られたお気に入り (Starあり) ---
        forgotten_favs = [
            ms for ms in scored_list 
            if ms.song.starred and days_map.get(ms.song_id, 999) > 30
        ]
        # 古い順にソート
        forgotten_favs.sort(key=lambda x: days_map.get(x.song_id, 0), reverse=True)
        
        for ms in forgotten_favs[:limit]:
            ms.song.selection_source = "forgotten_favorite"
            raw_candidates.append(ms.song)

        # --- レイヤー2: 昔聴いたことのある曲 (Starなし・再生数1以上) ---
        if len(raw_candidates) < limit:
            needed = limit - len(raw_candidates)
            # 再生数が1回以上あるものに限定 (ここがポイント)
            nostalgic_gems = [
                ms for ms in scored_list 
                if not ms.song.starred 
                and ms.play_count >= 1 # 0回は絶対に含めない
                and days_map.get(ms.song_id, 999) > 60
                and ms.song not in raw_candidates
            ]
            nostalgic_gems.sort(key=lambda x: days_map.get(x.song_id, 0), reverse=True)
            
            for ms in nostalgic_gems[:needed]:
                ms.song.selection_source = "recent" # レポート上で Nostalgic Gems になる
                raw_candidates.append(ms.song)

        return raw_candidates