from collections import Counter
from typing import List
from models.song import Song

class ArtistFilter:
    """同一アーティストの過剰な選出を制限するフィルタ。
    ライブラリの特性（特定アーティストの占有率が高い）に合わせて最大限に緩和。
    """

    def __init__(self, level: str = "Normal") -> None:
        # 許容比率をさらに引き上げ (Normal 30% -> 50%)
        # HOYO-MiXなどがリストの半分を占めても許容するようにします
        self.max_ratio = 0.6 if level == "Low" else (0.3 if level == "High" else 0.5)

    def apply(self, songs: List[Song]) -> List[Song]:
        if not songs:
            return []

        # ターゲットサイズ（25曲）に対して、同一アーティストが 12〜15曲 程度入るのを許容します。
        # これにより、戦略が選んだ「お気に入り」や「Recent」が削られるのを防ぎます。
        total_capacity = max(len(songs) // 2, 25) 
        max_per_artist = max(12, int(total_capacity * self.max_ratio))
        
        artist_counts = Counter()
        result = []
        last_artist = None

        for s in songs:
            if artist_counts[s.artist] >= max_per_artist:
                continue

            # 連続再生防止 (10曲以上のリスト時のみ有効)
            if s.artist == last_artist and len(songs) > 10:
                continue

            result.append(s)
            artist_counts[s.artist] += 1
            last_artist = s.artist

        return result