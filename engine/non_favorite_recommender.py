import logging
import random
import math
from typing import Dict, List, Set, Tuple, Any
from models.song import Song
from engine.filters.diversity_engine import DiversityEngine

logger = logging.getLogger("NonFavoriteRecommender")

class NonFavoriteRecommender:
    """仕様書 v10.0 準拠。Discoveryモードによる重み付け調整に対応した推薦エンジン。"""

    @staticmethod
    def get_recommendations(
        all_candidates: List[Song],
        selected_favorites: List[Song],
        limit: int,
        context: Dict
    ) -> Tuple[List[Song], Dict[str, Any]]:
        """
        非お気に入り曲の中から推薦曲を選出し、選出理由をタグ付けして返します。
        """
        # モードの判定 (Discovery Strategy から渡される)
        is_discovery_mode = context.get("discovery_mode", False)
        
        div_engine = DiversityEngine(
            suppress_instrumental=context.get("suppress_instrumental", True),
            suppress_live=context.get("suppress_live", False),
            suppress_remix=context.get("suppress_remix", False),
            suppress_demo=context.get("suppress_demo", False),
            suppress_acoustic=context.get("suppress_acoustic", False),
        )

        selected_ids = {s.id for s in selected_favorites}
        # 類似度判定用データ (お気に入り曲のアーティスト/アルバム)
        fav_artists = {s.artist for s in selected_favorites if s.artist}
        fav_albums = {s.album for s in selected_favorites if s.album}

        # 1. フィルタリング
        candidates = []
        for s in all_candidates:
            if s.id in selected_ids or getattr(s, "starred", False):
                continue
            
            # --- 重要: Discoveryモード時は PlayCount=0 (未聴曲) を許可する ---
            if not is_discovery_mode and s.play_count == 0:
                continue
                
            if div_engine.is_suppressed_version(s):
                continue
            candidates.append(s)

        if not candidates:
            return [], {"scanned": 0, "inserted": 0}

        # スコア計算用基礎データ
        max_play = max([s.play_count for s in candidates], default=1) or 1
        log_max_play = math.log10(max_play + 1)
        days_map = context.get("days_since_last_play", {})

        # --- 2. モード別の重み設定 ---
        if is_discovery_mode:
            # 未知の曲を掘り起こすための設定 (RandomとSimilarity重視)
            w_pc   = 0.05  # 再生回数の影響を弱める
            w_rec  = 0.05  # 新しさの影響を最小限に
            w_sim  = 0.20  # 好きなアーティストの知らない曲を優先
            w_rand = 0.70  # 運要素を最大にして多様性を出す
        else:
            # 通常の設定 (好みの傾向を維持)
            w_pc   = 0.45
            w_rec  = 0.25
            w_sim  = 0.20
            w_rand = 0.10

        scored_candidates = []

        # 3. DiscoveryScore の計算
        for s in candidates:
            # PlayCountScore
            pop_raw = (math.log10(s.play_count + 1) / log_max_play) * 100.0
            pop_weighted = pop_raw * w_pc
            
            # RecentScore
            days = days_map.get(s.id, 180) # 知らない曲は半年聴いていないと仮定
            rec_raw = 100.0 * math.exp(-days / 30.0)
            rec_weighted = rec_raw * w_rec

            # ArtistSimilarity (お気に入りアーティストならボーナス)
            sim_score = 0
            if s.artist in fav_artists:
                sim_score = 100
            elif s.album in fav_albums:
                sim_score = 80
            sim_weighted = sim_score * w_sim
            
            # Random Factor
            rand_raw = random.uniform(0, 100.0)
            rand_weighted = rand_raw * w_rand

            # 合計スコア
            total_score = pop_weighted + rec_weighted + sim_weighted + rand_weighted

            # --- 4. 選出理由 (selection_source) の特定 ---
            if is_discovery_mode:
                # Discovery Mix のレポートを綺麗にするため、タグを制限
                # 好きなアーティスト経由なら 'similarity'、それ以外は 'discovery'
                s.selection_source = "similarity" if sim_score > 0 else "discovery"
            else:
                # 通常時は最も寄与が高い成分を理由にする
                components = {
                    "recent": rec_weighted,
                    "play_count": pop_weighted,
                    "similarity": sim_weighted,
                    "discovery": rand_weighted
                }
                s.selection_source = max(components, key=components.get)

            scored_candidates.append((s, total_score))

        # スコア順にソートして上位 limit を選出
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        recommended = [x[0] for x in scored_candidates[:limit]]

        stats = {
            "scanned": len(candidates),
            "inserted": len(recommended)
        }

        logger.info(f"Discovery Engine: Mode={'Discovery' if is_discovery_mode else 'Standard'}, "
                    f"Scanned {stats['scanned']}, Inserted {stats['inserted']}")
        
        return recommended, stats