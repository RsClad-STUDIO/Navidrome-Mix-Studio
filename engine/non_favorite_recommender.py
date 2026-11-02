import logging
from typing import Dict, List, Tuple, Any

from models.song import Song
from engine.filters.diversity_engine import DiversityEngine
from engine.scoring.recommendation_scorer import RecommendationScorer

logger = logging.getLogger("NonFavoriteRecommender")


class NonFavoriteRecommender:
    """候補の適格性判定を行い、評価処理をRecommendationScorerへ委譲する。"""

    @staticmethod
    def get_recommendations(
        all_candidates: List[Song],
        selected_favorites: List[Song],
        limit: int,
        context: Dict,
    ) -> Tuple[List[Song], Dict[str, Any]]:
        is_discovery_mode = context.get("discovery_mode", False)

        diversity_engine = DiversityEngine(
            suppress_instrumental=context.get("suppress_instrumental", True),
            suppress_live=context.get("suppress_live", False),
            suppress_remix=context.get("suppress_remix", False),
            suppress_demo=context.get("suppress_demo", False),
            suppress_acoustic=context.get("suppress_acoustic", False),
        )

        selected_ids = {song.id for song in selected_favorites}
        eligible_candidates = []

        # ここでは候補の適格性だけを判定し、順位付けは行わない。
        for song in all_candidates:
            if song.id in selected_ids or getattr(song, "starred", False):
                continue
            if not is_discovery_mode and song.play_count == 0:
                continue
            if diversity_engine.is_suppressed_version(song):
                continue
            eligible_candidates.append(song)

        if not eligible_candidates or limit <= 0:
            return [], {
                "scanned": len(eligible_candidates),
                "inserted": 0,
            }

        recommended = RecommendationScorer.rank(
            eligible_candidates,
            selected_favorites,
            limit,
            context,
        )
        stats = {
            "scanned": len(eligible_candidates),
            "inserted": len(recommended),
        }

        logger.info(
            "Recommendation: mode=%s, scanned=%s, inserted=%s",
            "Discovery" if is_discovery_mode else "Standard",
            stats["scanned"],
            stats["inserted"],
        )
        return recommended, stats
