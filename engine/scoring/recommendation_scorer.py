import math
import random
from typing import Dict, List

from models.song import Song


class RecommendationScorer:
    """非お気に入り推薦候補の評価・順位付けだけを担当する。"""

    @staticmethod
    def rank(
        candidates: List[Song],
        selected_favorites: List[Song],
        limit: int,
        context: Dict,
    ) -> List[Song]:
        is_discovery_mode = context.get("discovery_mode", False)
        favorite_artists = {
            song.artist for song in selected_favorites if song.artist
        }
        favorite_albums = {
            song.album for song in selected_favorites if song.album
        }

        max_play_count = max(
            (song.play_count for song in candidates), default=1
        ) or 1
        log_max_play = math.log10(max_play_count + 1)
        days_map = context.get("days_since_last_play", {})

        if context.get("adaptive_mode", True):
            favorite_ratio = min(1.0, max(0.0, context.get("favorite_ratio", 0.0)))
            history_coverage = min(1.0, max(0.0, context.get("history_coverage", 0.0)))
            weight_similarity = min(0.25, max(0.10, favorite_ratio + 0.10))
            if is_discovery_mode:
                weight_play_count = 0.05
                weight_recency = 0.05
            else:
                weight_play_count = 0.35
                weight_recency = 0.25 if history_coverage >= 0.5 else 0.10
            weight_random = max(
                0.0,
                1.0 - weight_play_count - weight_recency - weight_similarity,
            )
        elif is_discovery_mode:
            weight_play_count = 0.05
            weight_recency = 0.05
            weight_similarity = 0.20
            weight_random = 0.70
        else:
            weight_play_count = 0.45
            weight_recency = 0.25
            weight_similarity = 0.20
            weight_random = 0.10

        ranked = []
        for song in candidates:
            popularity_raw = (
                math.log10(song.play_count + 1) / log_max_play
            ) * 100.0
            popularity = popularity_raw * weight_play_count

            days_since = days_map.get(song.id, 180)
            recency_raw = 100.0 * math.exp(-days_since / 30.0)
            recency = recency_raw * weight_recency

            similarity_raw = 0
            if song.artist in favorite_artists:
                similarity_raw = 100
            elif song.album in favorite_albums:
                similarity_raw = 80
            similarity = similarity_raw * weight_similarity

            random_value = random.uniform(0.0, 100.0) * weight_random
            total = popularity + recency + similarity + random_value

            if is_discovery_mode:
                song.selection_source = (
                    "similarity" if similarity_raw > 0 else "discovery"
                )
            else:
                components = {
                    "recent": recency,
                    "play_count": popularity,
                    "similarity": similarity,
                    "discovery": random_value,
                }
                song.selection_source = max(
                    components, key=components.get
                )

            ranked.append((song, total))

        ranked.sort(key=lambda item: item[1], reverse=True)
        return [song for song, _ in ranked[:limit]]
