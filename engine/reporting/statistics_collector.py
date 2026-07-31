import math
import logging
from collections import Counter
from typing import List, Dict, Any
from models.song import Song
from models.music_score import MusicScore
from models.statistics_data import (
    StatisticsData, UtilizationRow, RotationStats, 
    ScoreStats, DiversityStats
)
from engine.pipeline.rotation_calculator import RotationCalculator

class StatisticsCollector:
    """各工程の確定情報を集約し、不整合のない StatisticsData を生成。"""

    def collect(self, preset_name: str, limit: int, all_songs: List[Song], clean_pool: List[Song],
                scored_list: List[MusicScore], final_songs: List[Song], filtered_songs: List[Song],
                refill_songs: List[Song], days_map: Dict[str, int], rotation_history: Dict[str, int],
                gen_time_ms: int, context: Dict) -> StatisticsData:
        """
        選曲プロセスの各段階（Strategy/Filter/Refill）からデータを収集。
        Utilization は filtered_songs (戦略による初期選出) のみに基づいて計算されます。
        """
        
        # 1. 各段階のソース（タグ）集計
        # strat_counts: フィルタ通過直後（Initial Selection）の内訳。利用率計算の分子。
        strat_counts = Counter(getattr(s, "selection_source", "discovery") for s in filtered_songs)
        
        # final_counts: 最終的なリスト（Final Playlist）の内訳。全体の構成比用。
        final_counts = Counter(getattr(s, "selection_source", "discovery") for s in final_songs)
        
        # refill_counts: 補充された曲の内訳
        refill_counts = Counter(getattr(s, "selection_source", "discovery") for s in refill_songs)
        
        # 統計用プールの定義 (Top 300)
        top_pool = scored_list[:300]
        final_scores = sorted([ms.total_score for ms in scored_list if ms.song in final_songs], reverse=True)

        # 2. 利用率 (Utilization) の計算
        # 重要: 分子に strat_counts (補充前) を使うことで 100% 超えを防止
        def make_util(label, cand_count, used_count):
            # 候補数を超えて採用することは理論上ないため、安全のために min をとる
            actual_used = min(used_count, cand_count)
            ratio = (actual_used / cand_count * 100) if cand_count > 0 else 0.0
            return UtilizationRow(label, cand_count, actual_used, ratio)

        util_list = [
            make_util("Favorite", len([ms for ms in top_pool if ms.song.starred]), strat_counts["favorite"]),
            make_util("Recent", len([ms for ms in top_pool if ms.song_id in days_map and days_map[ms.song_id] <= 14]), strat_counts["recent"]),
            make_util("High PlayCount", len([ms for ms in top_pool if ms.play_count >= 50]), strat_counts["play_count"]),
            make_util("Album Candidates", len([ms for ms in top_pool if ms.album in {s.album for s in filtered_songs[:10]}]), strat_counts.get("similarity_album", 0)),
            make_util("Artist Candidates", len([ms for ms in top_pool if ms.artist in {s.artist for s in filtered_songs[:10]}]), strat_counts.get("similarity", 0) + strat_counts.get("similarity_artist", 0))
        ]

        # 3. Confidence 計算 (不確実性による減点方式)
        refill_total = len(refill_songs)
        discovery_count = final_counts.get("discovery", 0)

        refill_penalty_raw = (refill_total / limit) * 100 if limit > 0 else 0
        discovery_penalty_raw = (discovery_count / limit) * 40 if limit > 0 else 0
        
        ref_penalty_pct = int(refill_penalty_raw * 0.5)
        disc_penalty_pct = int(discovery_penalty_raw * 0.4)
        
        confidence = max(40, min(100, 100 - ref_penalty_pct - disc_penalty_pct))

        # 4. その他統計 (Rotation / Score / Diversity)
        rot = RotationCalculator.get_stats(scored_list, rotation_history)
        avg_s = sum(final_scores)/len(final_scores) if final_scores else 0
        med_s = final_scores[len(final_scores)//2] if final_scores else 0
        std_s = math.sqrt(sum((x - avg_s)**2 for x in final_scores)/len(final_scores)) if final_scores else 0
        
        lib_art = len(set(s.artist for s in all_songs)) or 1
        lib_alb = len(set(s.album for s in all_songs)) or 1
        mix_art = len(set(s.artist for s in final_songs))
        mix_alb = len(set(s.album for s in final_songs))
        art_ratio = (mix_art / lib_art * 100)
        div_level = "Low" if art_ratio < 15 else "Moderate" if art_ratio < 30 else "High" if art_ratio < 50 else "Excellent"

        return StatisticsData(
            preset=preset_name,
            limit=limit,
            library_total=len(all_songs),
            pool_count=len(clean_pool),
            history_loaded=10,
            gen_time_ms=gen_time_ms,
            confidence=confidence,
            conf_intended_count=len(filtered_songs),
            conf_disc_count=discovery_count,
            conf_disc_penalty_pct=disc_penalty_pct,
            conf_refill_count=refill_total,
            conf_refill_penalty_pct=ref_penalty_pct,
            utilization=util_list, 
            rotation=RotationStats(rot['rotation_count'], rot['avg_penalty'], rot['max_penalty'], rot.get('rotation_exempt', 0)), 
            scores=ScoreStats(final_scores[0] if final_scores else 0, avg_s, med_s, final_scores[-1] if final_scores else 0, std_s), 
            diversity=DiversityStats(mix_art, lib_art, mix_alb, lib_alb, art_ratio, (mix_alb/lib_alb*100), div_level, "Balanced diversity."),
            strat_initial_count=len(filtered_songs),
            refill_total=refill_total,
            final_total=len(final_songs),
            refill_sources=dict(refill_counts),
            strat_composition=dict(strat_counts),
            final_composition=dict(final_counts),
            disc_stats=context.get("disc_stats", {})
        )