from collections import Counter
from typing import List, Optional
from models.song import Song
from utils.title_normalizer import TitleNormalizer


class AlbumFilter:
    """同一アルバムからの重複選曲を制限するフィルタ。"""

    def __init__(
        self,
        level: str = "Normal",
        filter_versions: bool = True,
        target_size: int = 25,
        available_album_count: Optional[int] = None,
    ) -> None:
        # Keep the established 25-track behavior, but scale the cap with the requested mix size.
        ratio = 0.32 if level == "Low" else (0.12 if level == "High" else 0.24)
        self.target_size = max(1, target_size)
        self.max_per_album = max(1, int(self.target_size * ratio))
        self.filter_versions = filter_versions
        self.available_album_count = available_album_count

    def apply(self, songs: List[Song]) -> List[Song]:
        # Base the fallback on the complete available pool, not the current
        # trial list. Otherwise adding a second album could suddenly invalidate
        # already-selected tracks from the first album during refill.
        album_count = self.available_album_count
        if album_count is None:
            album_count = len({
                song.album or "Unknown Album"
                for song in songs
            })
        max_per_album = (
            self.target_size if album_count <= 1 else self.max_per_album
        )

        album_counts = Counter()
        seen_titles = set()
        selected = []

        for s in songs:
            if self.filter_versions:
                norm_title = TitleNormalizer.normalize(s.title)
                if norm_title in seen_titles:
                    continue
                seen_titles.add(norm_title)

            album_key = s.album or "Unknown Album"
            if album_counts[album_key] >= max_per_album:
                continue

            selected.append(s)
            album_counts[album_key] += 1

        return selected
