import logging
from typing import List, Dict, Any

from models.music_score import MusicScore

logger = logging.getLogger("RotationCalculator")


class RotationCalculator:
    """選曲履歴に基づく軽微なスコア補正だけを担当する。"""

    @staticmethod
    def _penalty_rate(history_count: int) -> float:
        if history_count <= 0:
            return 0.0
        if history_count == 1:
            return 0.005
        if history_count == 2:
            return 0.010
        if history_count == 3:
            return 0.015
        return 0.020

    @staticmethod
    def apply_rotation(
        scores: List[MusicScore],
        history_counts: Dict[str, int],
    ) -> List[MusicScore]:
        """履歴回数に応じて減点。上位10曲のお気に入りは免除する。"""
        # 再実行されても二重減点にならないよう、前回補正を戻す。
        for score in scores:
            score.total_score += score.rotation_penalty
            score.rotation_penalty = 0.0
            score.rotation_exempt = False

        # 免除対象は補正前スコアで確定する。
        scores.sort(key=lambda item: item.total_score, reverse=True)

        for index, score in enumerate(scores):
            if index < 10 and score.favorite_score > 0:
                score.rotation_exempt = True
                continue

            rate = RotationCalculator._penalty_rate(
                history_counts.get(score.song_id, 0)
            )
            penalty = score.total_score * rate
            score.total_score -= penalty
            score.rotation_penalty = penalty

        scores.sort(key=lambda item: item.total_score, reverse=True)
        return scores

    @staticmethod
    def get_stats(
        scores: List[MusicScore],
        history_counts: Dict[str, int],
    ) -> Dict[str, Any]:
        """実際に適用した補正量からローテーション統計を算出する。"""
        penalized = [score for score in scores if score.rotation_penalty > 0]
        percentages = [
            score.rotation_penalty
            / (score.total_score + score.rotation_penalty)
            * 100.0
            for score in penalized
            if score.total_score + score.rotation_penalty > 0
        ]
        exempt_count = sum(
            1 for score in scores
            if score.rotation_exempt
            and history_counts.get(score.song_id, 0) > 0
        )

        return {
            "rotation_count": len(penalized),
            "avg_penalty": (
                sum(percentages) / len(percentages) if percentages else 0.0
            ),
            "max_penalty": max(percentages) if percentages else 0.0,
            "rotation_exempt": exempt_count,
        }
