from typing import List, Dict, Tuple, Any
from datetime import datetime

from models.song import Song
from models.music_score import MusicScore
from engine.scoring.calculator import ScoringCalculator
from .rotation_calculator import RotationCalculator
from .purge_engine import PurgeEngine


class CandidatePipeline:
    """ライブラリ曲の除外・評価・ローテーション補正を担当する。"""

    def __init__(self, favorites_service, mix_history_service, logger) -> None:
        self._favorites_service = favorites_service
        self._mix_history_service = mix_history_service
        self._logger = logger

    def execute(
        self,
        all_songs: List[Song],
        days_map: Dict[str, int],
        now: datetime,
        preset_name: str,
        config: Dict[str, Any],
        adaptive_mode: bool = True,
    ) -> Tuple[List[Song], List[MusicScore], Dict[str, int]]:
        clean_pool: List[Song] = []
        scored_list: List[MusicScore] = []

        mix_type = "Daily" if "Daily" in preset_name else "Favorite"
        eligible_songs = []
        for song in all_songs:
            if PurgeEngine.should_purge(song, config):
                continue
            if self._favorites_service:
                song.starred = self._favorites_service.is_song_favorite(song.id)
            eligible_songs.append(song)

        total_eligible = len(eligible_songs)
        favorite_ratio = (
            sum(1 for song in eligible_songs if song.starred) / total_eligible
            if total_eligible else 0.0
        )
        history_coverage = (
            sum(1 for song in eligible_songs if song.id in days_map) / total_eligible
            if total_eligible else 0.0
        )
        calculator = ScoringCalculator(
            mix_type=mix_type,
            adaptive_mode=adaptive_mode,
            favorite_ratio=favorite_ratio,
            history_coverage=history_coverage,
        )
        max_play_count = max((song.play_count for song in eligible_songs), default=1)

        for song in eligible_songs:
            clean_pool.append(song)
            days_since = days_map.get(song.id)
            components = calculator.calculate_components(
                song, max_play_count, now, days_since
            )

            scored_list.append(
                MusicScore(
                    song_id=song.id,
                    title=song.title,
                    artist=song.artist,
                    album=song.album,
                    play_count=song.play_count,
                    last_played=song.last_played,
                    song=song,
                    **components,
                )
            )

        preset_key = preset_name.lower().replace(" ", "_")
        rotation_history = self._mix_history_service.get_song_occurrence_counts(
            preset=preset_key
        )
        scored_list = RotationCalculator.apply_rotation(
            scored_list, rotation_history
        )

        return clean_pool, scored_list, rotation_history
