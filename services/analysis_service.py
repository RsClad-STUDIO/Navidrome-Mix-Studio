"""ライブラリおよび再生傾向の統計・分析を行うサービス。"""

from collections import Counter
import logging
from typing import Any, Dict, List, Optional
from models.song import Song
from utils.title_normalizer import TitleNormalizer


class AnalysisService:
    """楽曲ライブラリの多様性や傾向分析を担当するクラス。"""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def analyze_album_song_counts(self, songs: List[Song]) -> Dict[str, int]:
        """アルバムごとの収録楽曲数を集計します。"""
        counts: Counter[str] = Counter()
        for song in songs:
            album_key = song.album or "Unknown Album"
            counts[album_key] += 1
        return dict(counts)

    def analyze_recommendation_metrics(self, songs: List[Song]) -> Dict[str, Any]:
        """Mixリストに対する多角的指標（Favorite率、Discovery率、年代割合等）を計算します。"""
        if not songs:
            return {}

        total = len(songs)
        fav_count = sum(1 for s in songs if getattr(s, "starred", False))
        disc_count = sum(1 for s in songs if s.play_count == 0)

        # 年代割合
        era_counts: Counter[str] = Counter()
        for s in songs:
            if s.year and s.year > 0:
                decade = f"{(s.year // 10) * 10}s"
                era_counts[decade] += 1
            else:
                era_counts["Unknown"] += 1

        # バージョン割合
        version_count = sum(
            1 for s in songs if any(TitleNormalizer.detect_versions(s.title).values())
        )

        return {
            "total_songs": total,
            "favorite_ratio": round((fav_count / total) * 100.0, 1),
            "discovery_ratio": round((disc_count / total) * 100.0, 1),
            "version_ratio": round((version_count / total) * 100.0, 1),
            "era_distribution": dict(era_counts),
        }