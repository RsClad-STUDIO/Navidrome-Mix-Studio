from dataclasses import dataclass, field
from typing import Dict, Any, List

@dataclass
class UtilizationRow:
    """各属性の利用率データ"""
    label: str
    candidates: int
    used: int
    ratio: float

@dataclass
class RotationStats:
    """Rotation(マンネリ防止)の統計"""
    affected: int
    avg_penalty: float
    max_penalty: float
    exempt: int

@dataclass
class ScoreStats:
    """スコアの統計情報"""
    highest: float
    average: float
    median: float
    lowest: float
    std_dev: float

@dataclass
class DiversityStats:
    """多様性の分析結果"""
    unique_artists: int
    total_artists: int
    unique_albums: int
    total_albums: int
    ratio_artist: float
    ratio_album: float
    assessment_level: str
    assessment_msg: str

@dataclass
class StatisticsData:
    """推薦レポート用 全集計データクラス"""
    preset: str
    limit: int
    library_total: int
    pool_count: int
    history_loaded: int
    gen_time_ms: int
    confidence: int
    
    utilization: List[UtilizationRow]
    rotation: RotationStats
    scores: ScoreStats
    diversity: DiversityStats
    
    strat_initial_count: int
    refill_total: int
    refill_sources: Dict[str, int]
    
    strat_composition: Dict[str, int]
    final_composition: Dict[str, int]

    # --- Confidence Detail (Phase 13.0 追加) ---
    conf_intended_count: int = 0
    conf_disc_count: int = 0
    conf_disc_penalty_pct: int = 0
    conf_refill_count: int = 0
    conf_refill_penalty_pct: int = 0
    
    final_total: int = 0  # ★これが必要でした
    disc_stats: Dict[str, Any] = field(default_factory=dict)