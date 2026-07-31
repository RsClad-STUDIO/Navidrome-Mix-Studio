from collections import Counter
from typing import List, Set
from models.song import Song
from utils.title_normalizer import TitleNormalizer

class AlbumFilter:
    """同一アルバムからの重複選曲を制限するフィルタ。"""

    def __init__(self, level: str = "Normal", filter_versions: bool = True) -> None:
        # 上限を 4 -> 6 へ緩和。シリーズものやライブアルバムの楽曲が残りやすくします。
        self.max_per_album = 8 if level == "Low" else (3 if level == "High" else 6)
        self.filter_versions = filter_versions

    def apply(self, songs: List[Song]) -> List[Song]:
        album_counts = Counter()
        seen_titles = set()
        selected = []

        for s in songs:
            # バージョン重複のチェック (normalizeを使用)
            if self.filter_versions:
                norm_title = TitleNormalizer.normalize(s.title)
                if norm_title in seen_titles:
                    continue
                seen_titles.add(norm_title)

            # アルバム枚数制限
            album_key = s.album or "Unknown Album"
            if album_counts[album_key] >= self.max_per_album:
                continue

            selected.append(s)
            album_counts[album_key] += 1
            
        return selected