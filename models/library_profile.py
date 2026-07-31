"""ライブラリ全体の構成比率や特徴プロファイルを保持するモデル。"""

from dataclasses import asdict, dataclass, field
import time
from typing import Any, Dict, List


@dataclass
class LibraryProfile:
    """ライブラリ分析結果プロファイル。"""

    total_songs: int = 0
    total_albums: int = 0
    total_artists: int = 0
    favorite_count: int = 0
    favorite_ratio: float = 0.0  # 0.0 - 100.0 (%)
    artist_distribution: Dict[str, float] = field(default_factory=dict)  # Artist -> Ratio (%)
    album_distribution: Dict[str, float] = field(default_factory=dict)   # Album -> Ratio (%)
    artist_song_counts: Dict[str, int] = field(default_factory=dict)
    album_song_counts: Dict[str, int] = field(default_factory=dict)
    year_known_count: int = 0
    year_unknown_count: int = 0
    year_known_ratio: float = 0.0
    year_unknown_ratio: float = 0.0
    version_count: int = 0
    version_ratio: float = 0.0
    instrumental_count: int = 0
    remix_count: int = 0
    live_count: int = 0
    analysis_time: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LibraryProfile":
        return cls(**data)