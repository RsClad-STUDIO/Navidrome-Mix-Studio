from collections import Counter
from typing import List, Optional
from models.song import Song


class ArtistFilter:
    """同一アーティストの過剰な選出を制限するフィルタ。"""

    def __init__(
        self,
        level: str = "Normal",
        target_size: int = 25,
        available_artist_count: Optional[int] = None,
    ) -> None:
        # Preserve preset ratios; derive the actual artist cap from the requested output size.
        self.max_ratio = 0.6 if level == "Low" else (0.3 if level == "High" else 0.5)
        self.target_size = max(1, target_size)
        self.available_artist_count = available_artist_count

    def apply(self, songs: List[Song]) -> List[Song]:
        if not songs:
            return []

        # Use the full candidate-pool count so a temporary single-artist
        # selection does not prevent refill from adding another artist.
        artist_count = self.available_artist_count
        if artist_count is None:
            artist_count = len({
                song.artist or "Unknown Artist"
                for song in songs
            })
        max_per_artist = (
            self.target_size
            if artist_count <= 1
            else max(1, int(self.target_size * self.max_ratio))
        )

        artist_counts = Counter()
        result = []

        for s in songs:
            artist_key = s.artist or "Unknown Artist"
            if artist_counts[artist_key] >= max_per_artist:
                continue

            result.append(s)
            artist_counts[artist_key] += 1

        return result
