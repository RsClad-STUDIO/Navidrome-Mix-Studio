from typing import Any, Dict, List, Set

from models.music_score import MusicScore


class RotationCalculator:
    """Mix履歴に基づく選曲ペナルティとローテーション枠を計算する。"""

    @staticmethod
    def apply_rotation(
        scores: List[MusicScore],
        history_counts: Dict[str, int],
    ) -> List[MusicScore]:
        """過去のMix出現回数に応じてスコアを減点する。"""
        scores.sort(key=lambda item: item.total_score, reverse=True)

        for index, score in enumerate(scores):
            if index < 10 and score.favorite_score > 0:
                score.rotation_penalty = 0.0
                continue

            count = history_counts.get(score.song_id, 0)
            penalty_rate = min(max(count, 0), 4) * 0.005
            penalty_amount = score.total_score * penalty_rate
            score.total_score -= penalty_amount
            score.rotation_penalty = penalty_amount

        scores.sort(key=lambda item: item.total_score, reverse=True)
        return scores

    @staticmethod
    def calculate_penalty_rate(
        accumulated_weight: float, is_priority_track: bool
    ) -> float:
        """Calculate a capped rotation penalty, protecting high-priority tracks."""
        if is_priority_track:
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
        """Replace repeated tracks with the highest-scoring fresh candidates."""
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
    def get_stats(
        scores: List[MusicScore], history_counts: Dict[str, int]
    ) -> Dict[str, Any]:
        """Summarize rotation impact and top-favorite exemptions."""
        affected = [
            score for score in scores
            if history_counts.get(score.song_id, 0) > 0
        ]
        exempt_count = sum(
            1
            for score in scores[:10]
            if score.favorite_score > 0 and history_counts.get(score.song_id, 0) > 0
        )
        if not affected:
            return {
                "rotation_count": 0,
                "avg_penalty": 0.0,
                "max_penalty": 0.0,
                "rotation_exempt": 0,
            }

        penalties = [
            min(max(history_counts.get(score.song_id, 0), 0), 4) * 0.5
            for score in affected
        ]
        return {
            "rotation_count": len(affected),
            "avg_penalty": sum(penalties) / len(penalties),
            "max_penalty": max(penalties),
            "rotation_exempt": exempt_count,
        }
