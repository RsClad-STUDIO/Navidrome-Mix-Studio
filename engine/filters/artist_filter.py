from collections import Counter
from typing import List
from models.song import Song

class ArtistFilter:
    """同一アーティストの過剰な選出を制限するフィルタ。
    ライブラリの特性（特定アーティストの占有率が高い）に合わせて最大限に緩和。
    """

    def __init__(self, level: str = "Normal", target_size: int = 25) -> None:
        # Preserve preset ratios; derive the actual artist cap from the requested output size.
        self.max_ratio = 0.6 if level == "Low" else (0.3 if level == "High" else 0.5)
        self.target_size = max(1, target_size)

    def apply(self, songs: List[Song]) -> List[Song]:
        if not songs:
            return []

        # The cap is proportional to the requested playlist size; no fixed 12-track floor.
        max_per_artist = max(1, int(self.target_size * self.max_ratio))
        
        artist_counts = Counter()
        result = []

        for s in songs:
            if artist_counts[s.artist] >= max_per_artist:
                continue

            # Candidate filtering must not enforce playback adjacency:
            # final playlist order is randomized later by MixGenerator.
            result.append(s)
            artist_counts[s.artist] += 1

        return result