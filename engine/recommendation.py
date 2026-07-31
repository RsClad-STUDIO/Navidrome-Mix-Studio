import logging
import random
import math
from typing import Dict, List, Optional
from models.recommendation_result import RecommendationItem, RecommendationResult, RecommendationScoreDetail

class RecommendationEngine:
    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self._logger = logger or logging.getLogger("RecommendationEngine")

    def rank_candidates(self, candidates, strategy, limit, play_counts, context) -> RecommendationResult:
        self._logger.info(f"Ranking Start: {len(candidates)} candidates")
        
        days_map = context.get("days_since_last_play", {})
        rotation_map = context.get("rotation_decay_map", {})
        
        # 戦略による「この曲を優先的に選ぶ」というIDセット
        pre_selected, stats = strategy.execute_selection(candidates, limit, context)
        pre_selected_ids = {s.id for s in pre_selected}

        max_play = max([s.play_count for s in candidates], default=1) or 1
        log_max_play = math.log10(max_play + 1)

        # 重み設定 (仕様書10.0 Baseline)
        FAVORITES_MIX_NAMES = {"favorites mix", "favorite mix", "favoritesmix", "fav mix"}
        is_fav_mix = strategy.name.lower().strip() in FAVORITES_MIX_NAMES
        w_fav, w_pop, w_rec, w_rand = (0.35, 0.30, 0.25, 0.05) if is_fav_mix else (0.15, 0.30, 0.25, 0.05)
        
        scored_items = []

        for song in candidates:
            reasons = []
            
            # --- 1. Favorite Score (35% or 15%) ---
            f_val = 100.0 if song.starred else 0.0
            f_score = f_val * w_fav
            if f_val > 0: reasons.append(f"Fav:+{f_score:.1f}")

            # --- 2. PlayCount Score (30% / Log10) ---
            p_val = (math.log10(song.play_count + 1) / log_max_play) * 100.0
            p_score = p_val * w_pop
            reasons.append(f"Play:{song.play_count}(+{p_score:.1f})")

            # --- 3. Recent Score (25% / Exp Decay) ---
            days = days_map.get(song.id, 90)
            r_val = 100.0 * math.exp(-days / 30.0)
            r_score = r_val * w_rec
            if r_val > 10: reasons.append(f"Recent:{days}d(+{r_score:.1f})")

            # --- 4. Random Score (5% / 0-10) ---
            rand_val = random.uniform(0, 10.0)
            rand_score = rand_val * w_rand

            # 合計スコア
            base_total = f_score + p_score + r_score + rand_score

            # --- 5. Rotation System (Penalty) ---
            rot_info = rotation_map.get(song.id, {})
            accum = rot_info.get("accumulated_weight", 0.0)
            if accum > 0:
                # Top Favorite (スコア上位) は免除するルールを適用
                penalty_rate = min(0.02, accum * 0.005)
                penalty = base_total * penalty_rate
                base_total -= penalty
                reasons.append(f"Rot:-{penalty:.1f}")

            # --- 6. Strategy Boost (+1000) ---
            if song.id in pre_selected_ids:
                base_total += 1000.0
                reasons.append("SELECTED")

            detail = RecommendationScoreDetail(
                favorite_score=f_val, recency_score=r_val, popularity_score=p_val,
                total_score=round(base_total, 2),
                reasons=reasons # UIの「Reasons」に表示される
            )
            scored_items.append(RecommendationItem(rank=0, song=song, score_detail=detail))

        # ソート（合計スコア降順）
        scored_items.sort(key=lambda x: x.score_detail.total_score, reverse=True)
        final_items = scored_items[:limit]

        # 再生順のシャッフル（Top 25曲の中でのみ並び替え）
        shuffled = list(final_items)
        random.shuffle(shuffled)

        for idx, item in enumerate(shuffled, start=1):
            item.rank = idx

        return RecommendationResult(
            items=shuffled, strategy_name=strategy.name, metrics=stats, candidate_count=len(candidates)
        )