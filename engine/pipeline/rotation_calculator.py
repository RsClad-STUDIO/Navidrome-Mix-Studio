import logging
from typing import List, Dict, Any
from models.music_score import MusicScore

logger = logging.getLogger("RotationCalculator")


class RotationCalculator:
    """スコアに履歴ベースの軽微なローテーション補正を適用する。"""

    @staticmethod
    def apply_rotation(
        scores: List[MusicScore],
        history_counts: Dict[str, int],
    ) -> List[MusicScore]:
        # 補正前のスコア順で上位10曲を確定する。
        scores.sort(key=lambda item: item.total_score, reverse=True)

        for index, music_score in enumerate(scores):
            # 上位10曲のお気に入りはローテーション減点を免除する。
            if index < 10 and music_score.favorite_score > 0:
                music_score.rotation_penalty = 0.0
                continue

            count = history_counts.get(music_score.song_id, 0)
            if count <= 0:
                penalty_rate = 0.0
            elif count == 1:
                penalty_rate = 0.005
            elif count == 2:
                penalty_rate = 0.010
            elif count == 3:
                penalty_rate = 0.015
            else:
                penalty_rate = 0.020

            penalty_amount = music_score.total_score * penalty_rate
            music_score.total_score -= penalty_amount
            music_score.rotation_penalty = penalty_amount

        scores.sort(key=lambda item: item.total_score, reverse=True)
        return scores

    @staticmethod
    def get_stats(
        scores: List[MusicScore],
        history_counts: Dict[str, int],
    ) -> Dict[str, Any]:
        """補正対象数・減点率・上位お気に入り免除数を集計する。"""
        affected = [
            score for score in scores
            if history_counts.get(score.song_id, 0) > 0
        ]

        # apply_rotation() 後のスコア降順リストを前提とする。
        exempt_count = sum(
            1
            for score in scores[:10]
            if score.favorite_score > 0
            and history_counts.get(score.song_id, 0) > 0
        )

        if not affected:
            return {
                "rotation_count": 0,
                "avg_penalty": 0.0,
                "max_penalty": 0.0,
                "rotation_exempt": 0,
            }

        rates = []
        for score in affected:
            count = history_counts.get(score.song_id, 0)
            rate = 0.5 if count == 1 else (
                1.0 if count == 2 else (1.5 if count == 3 else 2.0)
            )
            rates.append(rate)

        return {
            "rotation_count": len(affected),
            "avg_penalty": sum(rates) / len(rates),
            "max_penalty": max(rates),
            "rotation_exempt": exempt_count,
        }

