import logging
from typing import List, Dict, Any, Set  # Any を追加
from models.music_score import MusicScore

logger = logging.getLogger("RotationCalculator")

class RotationCalculator:
    """Phase 10.0 Section 6 & 7: Rotation System (弱い補正)"""

    @staticmethod
    def apply_rotation(
        scores: List[MusicScore],
        history_counts: Dict[str, int]
    ) -> List[MusicScore]:
        """
        スコアを直接変更して出現頻度を制御する。
        (Logic preserved from Phase 10.0)
        """
        # Section 7: スコアが高い順に並べて上位10位を特定
        scores.sort(key=lambda x: x.total_score, reverse=True)

        for i, ms in enumerate(scores):
            # Section 7: Top Favorite Protection (上位10位以内のFavoriteはペナルティ免除)
            if i < 10 and ms.favorite_score > 0:
                ms.rotation_penalty = 0.0
                continue

            # Section 6: Rotation Penalty 算出
            count = history_counts.get(ms.song_id, 0)
            if count == 0:
                penalty_rate = 0.0
            elif count == 1:
                penalty_rate = 0.005 # 0.5%
            elif count == 2:
                penalty_rate = 0.010 # 1.0%
            elif count == 3:
                penalty_rate = 0.015 # 1.5%
            else:
                penalty_rate = 0.020 # 2.0% (4回以上)

            # Conversion: RotationScore = -FinalScore * RotationPenalty
            penalty_amount = ms.total_score * penalty_rate
            ms.total_score -= penalty_amount
            ms.rotation_penalty = penalty_amount

        # ペナルティ適用後に再ソート
        scores.sort(key=lambda x: x.total_score, reverse=True)
        return scores

    @staticmethod
    def calculate_penalty_rate(
        accumulated_weight: float, is_top_favorite: bool
    ) -> float:
        """Calculate a capped rotation penalty, protecting high-priority tracks."""
        if is_top_favorite:
            return 0.0
        return min(0.02, max(0.0, accumulated_weight) * 0.005)

    @staticmethod
    def apply_rotation_budget(
        candidate_selected: List[Any],
        prev_mix_ids: Set[str],
        prev_mix_songs_map: Dict[str, Any],
        score_details: Dict[str, Dict[str, Any]],
        limit: int,
        max_budget: int,
    ) -> List[Any]:
        """Replace up to max_budget recently repeated tracks with the best fresh candidates."""
        selected = list(candidate_selected[:max(0, limit)])
        if not selected or max_budget <= 0:
            return selected

        previous_ids = prev_mix_ids.intersection(prev_mix_songs_map)
        selected_ids = {song.id for song in selected}
        repeated = [song for song in selected if song.id in previous_ids]
        replacements = [
            details["song"]
            for song_id, details in score_details.items()
            if song_id not in selected_ids and song_id not in previous_ids
        ]
        replacements.sort(
            key=lambda song: score_details[song.id]["final_score"],
            reverse=True,
        )
        repeated.sort(
            key=lambda song: score_details[song.id]["final_score"]
        )

        for old_song, new_song in zip(repeated[:max_budget], replacements):
            selected[selected.index(old_song)] = new_song

        selected.sort(
            key=lambda song: score_details[song.id]["final_score"],
            reverse=True,
        )
        return selected

    @staticmethod
    def get_stats(scores: List[MusicScore], history_counts: Dict[str, int]) -> Dict[str, Any]:
        """
        Rotationの適用統計を計算する (Phase 10.1 Logging Improvement)
        ロジックは変更せず、統計数値のみを抽出します。
        """
        affected = [s for s in scores if history_counts.get(s.song_id, 0) > 0]
        if not affected:
            return {"rotation_count": 0, "avg_penalty": 0.0, "max_penalty": 0.0}
        
        penalties = []
        for s in affected:
            # Section 6 のルールに基づいて統計用の数値を算出 (%)
            count = history_counts.get(s.song_id, 0)
            p = 0.5 if count == 1 else (1.0 if count == 2 else (1.5 if count == 3 else 2.0))
            penalties.append(p)
            
        return {
            "rotation_count": len(affected),
            "avg_penalty": sum(penalties) / len(penalties),
            "max_penalty": max(penalties)
        }
    
    def get_stats(scores: List[MusicScore], history_counts: Dict[str, int]) -> Dict[str, Any]:
        affected = [s for s in scores if history_counts.get(s.song_id, 0) > 0]
        # Section 7: Top 10 Favorite 免除のカウント
        # スコア順に並んでいる前提で、上位10位かつFavoriteScore > 0 の曲を数える
        exempt_count = len([s for i, s in enumerate(scores[:10]) if s.favorite_score > 0 and history_counts.get(s.song_id, 0) > 0])

        if not affected:
            return {"rotation_count": 0, "avg_penalty": 0.0, "max_penalty": 0.0, "rotation_exempt": 0}
        
        penalties = []
        for s in affected:
            count = history_counts.get(s.song_id, 0)
            p = 0.5 if count == 1 else (1.0 if count == 2 else (1.5 if count == 3 else 2.0))
            penalties.append(p)
            
        return {
            "rotation_count": len(affected),
            "avg_penalty": sum(penalties) / len(penalties),
            "max_penalty": max(penalties),
            "rotation_exempt": exempt_count
        }