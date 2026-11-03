from typing import Dict, List, Tuple
import random

from models.song import Song
from models.music_score import MusicScore
from engine.filters.album_filter import AlbumFilter
from engine.filters.artist_filter import ArtistFilter
from engine.filters.version_filter import VersionFilter
from engine.strategies.strategy_config import DiscoveryMixConfig, ForgottenMixConfig


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
        history_available: bool = False,
        history_empty: bool = False,
    ) -> Tuple[List[Song], List[Song]]:
        final_list = list(current_songs[:limit])
        if len(final_list) >= limit:
            return final_list, []

        config = filter_config or {}
        available_album_count = len({
            score.album or "Unknown Album" for score in scored_list
        })
        available_artist_count = len({
            score.artist or "Unknown Artist" for score in scored_list
        })
        version_filter = VersionFilter(config)
        album_filter = AlbumFilter(
            level=config.get("album_level", "Normal"),
            filter_versions=config.get("filter_versions", True),
            target_size=limit,
            available_album_count=available_album_count,
        )
        artist_filter = ArtistFilter(
            level=config.get("artist_level", "Normal"),
            target_size=limit,
            available_artist_count=available_artist_count,
        )
        existing_ids = {song.id for song in final_list}
        refilled_list: List[Song] = []

        # Shuffle before the stable score sort: scores stay ranked, while ties
        # no longer inherit the Navidrome API's album/group ordering.
        ranked_scores = list(scored_list)
        random.shuffle(ranked_scores)
        if preset_name == "Favorites Mix":
            # Favorites Mix may have too few previously-played non-favorites.
            # Keep played tracks ahead of never-played discovery fallbacks.
            ranked_scores.sort(
                key=lambda item: (item.play_count == 0, -item.total_score)
            )
        else:
            ranked_scores.sort(key=lambda item: item.total_score, reverse=True)

        for music_score in ranked_scores:
            song = music_score.song
            if song.id in existing_ids or version_filter.is_suppressed(song):
                continue

            if "Discovery" in preset_name:
                eligible = not song.starred and music_score.play_count < DiscoveryMixConfig.PLAY_COUNT_THRESHOLD_INITIAL
                source_tag = "discovery"
            elif "Forgotten" in preset_name:
                days_unplayed = days_map.get(music_score.song_id, 999)
                if song.starred:
                    eligible = days_unplayed > ForgottenMixConfig.RECENT_DAYS_LIMIT
                    source_tag = "forgotten_favorite"
                else:
                    eligible = music_score.play_count >= ForgottenMixConfig.PLAY_COUNT_MIN and days_unplayed > ForgottenMixConfig.NON_FAVORITE_DAYS_LIMIT
                    source_tag = "recent"
            else:
                # Bootstrap never-played tracks only when the history endpoint
                # succeeded and explicitly returned an empty history. Song-level
                # lastPlayed metadata must not block this zero-history fallback.
                allow_unplayed_fallback = (
                    preset_name == "Favorites Mix"
                    or (history_available and history_empty)
                )
                eligible = not song.starred and (
                    music_score.play_count >= 1
                    or (allow_unplayed_fallback and music_score.play_count == 0)
                )
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
