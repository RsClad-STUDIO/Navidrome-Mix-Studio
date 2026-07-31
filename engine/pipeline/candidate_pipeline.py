from typing import List, Dict, Tuple, Any
from datetime import datetime
from models.song import Song
from models.music_score import MusicScore
from engine.scoring.calculator import ScoringCalculator
from .rotation_calculator import RotationCalculator
from .purge_engine import PurgeEngine  # 同一フォルダ内
from utils.title_normalizer import TitleNormalizer # これを追加

class CandidatePipeline:
    def __init__(self, favorites_service, mix_history_service, logger) -> None:
        self._favorites_service = favorites_service
        self._mix_history_service = mix_history_service
        self._logger = logger

    def execute(self, all_songs: List[Song], days_map: Dict[str, int], now: datetime, 
                preset_name: str, config: Dict[str, Any]) -> Tuple[List[Song], List[MusicScore], Dict[str, int]]:
        
        clean_pool = []
        scored_list = []
        calc = ScoringCalculator(mix_type="Daily" if "Daily" in preset_name else "Favorite")
        max_p = max([s.play_count for s in all_songs], default=1)

        for s in all_songs:
            # PurgeEngine で除外判定
            if PurgeEngine.should_purge(s, config):
                continue

            if self._favorites_service:
                s.starred = self._favorites_service.is_song_favorite(s.id)
            
            clean_pool.append(s)

            d_since = days_map.get(s.id)
            score = calc.calculate_base_score(s, max_p, now, d_since)
            ms = MusicScore(song_id=s.id, title=s.title, artist=s.artist, album=s.album, 
                            play_count=s.play_count, total_score=max(0.0, score))
            ms.song = s
            scored_list.append(ms)

        preset_key = preset_name.lower().replace(" ", "_")
        rotation_history = self._mix_history_service.get_song_occurrence_counts(preset=preset_key)
        scored_list = RotationCalculator.apply_rotation(scored_list, rotation_history)

        return clean_pool, scored_list, rotation_history