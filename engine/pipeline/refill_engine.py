from typing import Dict, List, Tuple

from models.song import Song
from models.music_score import MusicScore
from engine.filters.album_filter import AlbumFilter
from engine.filters.artist_filter import ArtistFilter
from engine.filters.version_filter import VersionFilter


class RefillEngine:
    """Refill missing tracks using the same ranking and diversity rules."""

    @staticmethod
    def refill(
        current_songs: List[Song],
        scored_list: List[MusicScore],
        limit: int,
        preset_name: str,
        days_map: dict,
        filter_config: Dict = None,
    ) -> Tuple[List[Song], List[Song]]:
        final_list = list(current_songs[:limit])
        if len(final_list) >= limit:
            return final_list, []

        config = filter_config or {}
        version_filter = VersionFilter(config)
        album_filter = AlbumFilter(
            level=config.get("album_level", "Normal"),
            filter_versions=config.get("filter_versions", True),
        )
        artist_filter = ArtistFilter(level=config.get("artist_level", "Normal"))
        existing_ids = {song.id for song in final_list}
        refilled_list: List[Song] = []

        # CandidatePipeline ranks scores descending; make refill order explicit too.
        ranked_scores = sorted(scored_list, key=lambda item: item.total_score, reverse=True)

        for music_score in ranked_scores:
            song = music_score.song
            if song.id in existing_ids or version_filter.is_suppressed(song):
                continue

            if "Discovery" in preset_name:
                eligible = not song.starred and music_score.play_count < 3
                source_tag = "discovery"
            elif "Forgotten" in preset_name:
                days_unplayed = days_map.get(music_score.song_id, 999)
                if song.starred:
                    eligible = days_unplayed > 30
                    source_tag = "forgotten_favorite"
                else:
                    eligible = music_score.play_count >= 1 and days_unplayed > 60
                    source_tag = "recent"
            else:
                eligible = not song.starred and music_score.play_count >= 1
                source_tag = "discovery"

            if not eligible:
                continue

            # Reject a refill candidate if it would displace an existing selection.
            trial_list = final_list + [song]
            trial_ids = [item.id for item in trial_list]
            if [item.id for item in album_filter.apply(trial_list)] != trial_ids:
                continue
            if [item.id for item in artist_filter.apply(trial_list)] != trial_ids:
                continue

            song.selection_source = source_tag
            final_list.append(song)
            refilled_list.append(song)
            existing_ids.add(song.id)
            if len(final_list) >= limit:
                break

        return final_list, refilled_list
