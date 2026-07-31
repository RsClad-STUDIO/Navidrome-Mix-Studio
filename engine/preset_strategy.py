"""選曲戦略（Strategy Pattern）および実行ログを出力するモジュール。"""

from abc import ABC, abstractmethod
import logging
import random
from typing import Dict, List, Set, Tuple
from engine.weights import RecommendationWeights
from models.song import Song
from engine.pipeline.rotation_calculator import RotationCalculator
from engine.non_favorite_recommender import NonFavoriteRecommender


class PresetStrategy(ABC):
    """Mix生成戦略の基底抽象クラス。"""

    @property
    @abstractmethod
    def name(self) -> str: pass

    @property
    @abstractmethod
    def description(self) -> str: pass

    @abstractmethod
    def get_weights(self, profile_weights: RecommendationWeights) -> RecommendationWeights:
        pass

    @abstractmethod
    def execute_selection(
        self, candidates: List[Song], limit: int, context: Dict
    ) -> Tuple[List[Song], Dict[str, int]]:
        pass

    def _run_common_selection_flow(
        self, 
        pool: List[Song], 
        limit: int, 
        context: Dict, 
        weights: RecommendationWeights, 
        max_budget: int
    ) -> Tuple[List[Song], Dict]:
        """
        全戦略で共通して使用する選出・Rotation・レポート生成の標準フロー。
        """
        logger = logging.getLogger(self.__class__.__name__)
        
        if not pool:
            return [], {"error": "Empty pool"}

        recent_ids: List[str] = context.get("recent_ids", [])
        recent_set: Set[str] = set(recent_ids)
        decay_map: Dict[str, Dict] = context.get("rotation_decay_map", {})
        has_history = len(decay_map) > 0
        current_pool_ids = {s.id for s in pool}

        # 前回Mix情報の整理
        prev_mix_ids: Set[str] = set()
        prev_mix_songs_map: Dict[str, Song] = {}
        if has_history:
            for sid, info in decay_map.items():
                if info.get("appeared_in_last") and sid in current_pool_ids:
                    prev_mix_ids.add(sid)

        max_play = max([s.play_count for s in pool], default=1) or 1
        score_details = {}

        # -------------------------------------------------------------------------
        # 1. 選出スコアリング (多様性を生むためのランダム性を強化)
        # -------------------------------------------------------------------------
        for s in pool:
            starred_val = 100.0 if getattr(s, "starred", False) else 0.0
            recency_val = 100.0 if s.id in recent_set else 0.0
            # 人気度の影響を少しマイルドにする (対数的なスケーリングに近い効果)
            play_val = min(100.0, (s.play_count / max_play) * 100.0)
            discovery_val = 100.0 if s.play_count == 0 else 0.0
            
            # 各曲に固有のランダム値を付与 (これがないと毎回同じ曲が選ばれる)
            random_val = random.uniform(0.0, 100.0)

            # プロフィール重みの計算
            profile_score = (
                (starred_val * weights.weight_favorite) +
                (recency_val * weights.weight_recency) +
                (play_val * weights.weight_popularity) +
                (discovery_val * weights.weight_discovery) +
                (random_val * weights.weight_random)
            )

            # Rotation計算 (Phase 10: 追い出しロジック)
            accum_weight = 0.0
            if has_history and s.id in decay_map:
                accum_weight = decay_map[s.id]["accumulated_weight"]
            is_top_favorite = (s.play_count >= max_play * 0.7) or (s.id in recent_set)
            penalty_rate = RotationCalculator.calculate_penalty_rate(accum_weight, is_top_favorite)
            rotation_score = max(0.0, 100.0 * (1.0 - penalty_rate))

            # 最終スコアリング
            raw_score = (profile_score * 0.7) + (100.0 * 0.3) # 基礎
            final_score = (profile_score * 0.7) + (rotation_score * 0.3) # Rotation加味

            score_details[s.id] = {
                "song": s,
                "raw_score": raw_score,
                "final_score": final_score,
                "rotation_diff": final_score - raw_score,
                "penalty_rate": penalty_rate,
            }
            if s.id in prev_mix_ids:
                prev_mix_songs_map[s.id] = s

        # -------------------------------------------------------------------------
        # 2. 選出 (スコア順にソートして上位 limit 分を確定)
        # -------------------------------------------------------------------------
        ranked_final = sorted(pool, key=lambda s: score_details[s.id]["final_score"], reverse=True)
        ranked_raw = sorted(pool, key=lambda s: score_details[s.id]["raw_score"], reverse=True)
        for idx, s in enumerate(ranked_raw): score_details[s.id]["raw_rank"] = idx + 1
        for idx, s in enumerate(ranked_final): score_details[s.id]["final_rank"] = idx + 1

        candidate_selected = ranked_final[:limit]

        # Rotation Budget 適用 (急激な変化を抑えつつ、指定枠数分を入れ替える)
        selected = RotationCalculator.apply_rotation_budget(
            candidate_selected=candidate_selected,
            prev_mix_ids=prev_mix_ids,
            prev_mix_songs_map=prev_mix_songs_map,
            score_details=score_details,
            limit=limit,
            max_budget=max_budget
        )

        # -------------------------------------------------------------------------
        # 3. 再生順序のシャッフル (最終的な並びをランダムに)
        # -------------------------------------------------------------------------
        final_list = list(selected)
        random.shuffle(final_list)

        # メトリクス生成 (略)
        selected_ids = {s.id for s in final_list}
        in_songs = [f"{s.title} - {s.artist}" for s in final_list if s.id not in prev_mix_ids]
        metrics = {
            "rotation_in_count": len(in_songs),
            "in_songs": in_songs,
            "total_selected": len(final_list),
        }

        return final_list, metrics


# ... (冒頭のインポートは維持)

class FavoritesStrategy(PresetStrategy):
    """お気に入りを中心とし、少量の推薦曲を加えたMix戦略。"""

    name = "Favorites Mix"
    description = "お気に入りを最優先（22-23曲）。残りの枠にフィルター条件を満たす推薦曲を2-3曲加えます。"
    
    MAX_ROTATION_BUDGET = 3
    NON_FAVORITE_LIMIT = 3

    def get_weights(self, profile_weights: RecommendationWeights) -> RecommendationWeights:
        return RecommendationWeights(
            weight_favorite=0.8, weight_recency=0.1, weight_popularity=0.1, weight_discovery=0.0, weight_random=0.1
        )

# FavoritesStrategy の execute_selection 部分を以下のように修正
    def execute_selection(self, candidates, limit, context) -> Tuple[List[Song], Dict]:
        # 全お気に入り曲の抽出
        starred_songs = [s for s in candidates if s.starred]
        
        # スコア順に並べて上位 limit 件（22~25曲）を選ぶ
        # (RecommendationEngine側でもスコア順に並ぶが、ここで選出対象を確定させる)
        starred_songs.sort(key=lambda s: s.play_count, reverse=True) # 暫定
        
        selected = starred_songs[:limit]
        return selected, {"reasons": ["Top Favorites Pool"]}

        # 推薦曲の選出
        remaining_limit = limit - len(fav_selected)
        non_fav_request_limit = min(remaining_limit, self.NON_FAVORITE_LIMIT)

        # contextからフィルター情報を引き継いで推薦を依頼
        non_fav_selected = NonFavoriteRecommender.get_recommendations(
            all_candidates=context.get("all_songs", []),
            selected_favorites=fav_selected,
            limit=non_fav_request_limit,
            context=context
        )

        final_list = fav_selected + non_fav_selected
        random.shuffle(final_list)

        metrics = fav_metrics
        metrics.update({
            "favorite_count": len(fav_selected),
            "non_favorite_count": len(non_fav_selected)
        })
        return final_list, metrics

# ... (DailyStrategy, DiscoveryStrategy などの実装も、_run_common_selection_flow を使う形に統一)


class DailyStrategy(PresetStrategy):
    """デイリーミックス：日常的な選曲にランダム要素をブレンド"""
    name = "Daily Mix"
    description = "いつものお気に入りと新しい発見をバランスよくミックス。"
    MAX_ROTATION_BUDGET = 8

    def get_weights(self, profile_weights: RecommendationWeights) -> RecommendationWeights:
        # プロフィール設定をベースにしつつ、最低限のランダム性を保証
        w = profile_weights
        return RecommendationWeights(
            weight_favorite=w.weight_favorite,
            weight_recency=w.weight_recency,
            weight_popularity=w.weight_popularity,
            weight_discovery=w.weight_discovery,
            weight_random=max(w.weight_random, 0.2) # 最低20%はランダム
        )

    def execute_selection(self, candidates: List[Song], limit: int, context: Dict) -> Tuple[List[Song], Dict]:
        profile_weights = context.get("profile_weights", RecommendationWeights())
        return self._run_common_selection_flow(candidates, limit, context, self.get_weights(profile_weights), self.MAX_ROTATION_BUDGET)


class DiscoveryStrategy(PresetStrategy):
    """ディスカバリー：未再生曲を完全にシャッフルして選出"""
    name = "Discovery Mix"
    description = "ライブラリに眠っている未再生曲を発掘します。"

    def get_weights(self, profile_weights: RecommendationWeights) -> RecommendationWeights:
        return RecommendationWeights(weight_discovery=0.8, weight_random=0.2)

    def execute_selection(self, candidates: List[Song], limit: int, context: Dict) -> Tuple[List[Song], Dict]:
        unplayed = [s for s in candidates if s.play_count == 0]
        # 選出そのものを完全にランダム化
        selected = random.sample(unplayed, min(len(unplayed), limit))
        return selected, {"discovery_count": len(selected)}


class ForgottenFavoritesStrategy(PresetStrategy):
    """忘れていたお気に入り：最近聴いていない曲を優先"""
    name = "Forgotten Favorites"
    description = "お気に入りだけど最近聴いていない、懐かしい曲を選出。"

    def get_weights(self, profile_weights: RecommendationWeights) -> RecommendationWeights:
        return RecommendationWeights(weight_favorite=0.5, weight_recency=0.0, weight_discovery=0.2, weight_random=0.3)

    def execute_selection(self, candidates: List[Song], limit: int, context: Dict) -> Tuple[List[Song], Dict]:
        recent_ids = set(context.get("recent_ids", []))
        forgotten = [s for s in candidates if getattr(s, "starred", False) and s.id not in recent_ids]
        return self._run_common_selection_flow(forgotten, limit, context, self.get_weights(None), limit // 2)