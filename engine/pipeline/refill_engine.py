from typing import Dict, List, Tuple
from models.song import Song
from models.music_score import MusicScore
from engine.filters.version_filter import VersionFilter


class RefillEngine:
    """プレイリストの不足分を、除外設定に合う楽曲で補充するエンジン。"""

    @staticmethod
    def refill(
        current_songs: List[Song],
        scored_list: List[MusicScore],
        limit: int,
        preset_name: str,
        days_map: dict,
        filter_config: Dict = None,
    ) -> Tuple[List[Song], List[Song]]:
        """除外済み候補を補充元からも除き、補充曲を別途返す。"""
        if len(current_songs) >= limit:
            return current_songs[:limit], []

        version_filter = VersionFilter(filter_config or {})
        existing_ids = {song.id for song in current_songs}
        refilled_list: List[Song] = []
        final_list = list(current_songs)

        if "Discovery" in preset_name:
            fill_pool = [ms for ms in reversed(scored_list) if ms.play_count < 3]
            source_tag = "discovery"
        elif "Forgotten" in preset_name:
            fill_pool = [
                ms for ms in reversed(scored_list)
                if ms.play_count >= 1 and days_map.get(ms.song_id, 999) > 30
            ]
            source_tag = "recent"
        else:
            fill_pool = scored_list
            source_tag = "discovery"

        for music_score in fill_pool:
            song = music_score.song
            if song.id in existing_ids or version_filter.is_suppressed(song):
                continue

            song.selection_source = source_tag
            final_list.append(song)
            refilled_list.append(song)
            existing_ids.add(song.id)

            if len(final_list) >= limit:
                break

        return final_list, refilled_list
