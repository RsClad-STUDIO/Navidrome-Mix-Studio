from collections import Counter
from typing import List
from models.song import Song


class ArtistFilter:
    """同一アーティストの過剰な選出を制限するフィルタ。"""

    def __init__(self, level: str = "Normal", target_size: int = 25) -> None:
        # Preserve preset ratios; derive the actual artist cap from the requested output size.
        self.max_ratio = 0.6 if level == "Low" else (0.3 if level == "High" else 0.5)
        self.target_size = max(1, target_size)

    def apply(self, songs: List[Song]) -> List[Song]:
        if not songs:
            return []

        # If only one artist is available, do not cap the playlist below its target.
        available_artists = {song.artist or "Unknown Artist" for song in songs}
        max_per_artist = (
            self.target_size
            if len(available_artists) <= 1
            else max(1, int(self.target_size * self.max_ratio))
        )

        artist_counts = Counter()
        result = []

        for s in songs:
            if artist_counts[s.artist or "Unknown Artist"] >= max_per_artist:
                continue

            # Candidate filtering must not enforce playback adjacency:
            # final playlist order is randomized later by MixGenerator.
            result.append(s)
            artist_counts[s.artist or "Unknown Artist"] += 1

        return result
