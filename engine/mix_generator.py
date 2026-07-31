import logging
import random
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import Counter

from models.song import Song
from models.statistics_data import StatisticsData
from engine.pipeline.candidate_pipeline import CandidatePipeline
from engine.pipeline.refill_engine import RefillEngine
from engine.reporting.statistics_collector import StatisticsCollector
from engine.reporting.report_formatter import ReportFormatter
from engine.filters.diversity_engine import DiversityEngine
from engine.factory.strategy_factory import StrategyFactory
from services.mix_history_service import MixHistoryService

class MixGenerator:
    SUPPRESS_LIVE = True
    SUPPRESS_INSTRUMENTAL = True
    HARD_DURATION_LIMIT = 10800 

    def __init__(self, **kwargs) -> None:
        self._logger = logging.getLogger("MixGenerator")
        self._library_service = kwargs.get("library_service")
        self._history_service = kwargs.get("history_service")
        self._favorites_service = kwargs.get("favorites_service")
        
        # ★バグ修正: blacklist_service を保持するように追加
        self._blacklist_service = kwargs.get("blacklist_service")
        
        self._mix_history_service = kwargs.get("mix_history_service") or MixHistoryService()
        self._pipeline = CandidatePipeline(self._favorites_service, self._mix_history_service, self._logger)
        self._refill_engine = RefillEngine()
        self._stats_collector = StatisticsCollector()
        self._strategy_factory = StrategyFactory()
        
        # 統計保持用
        self._last_stats = None

    def generate_mix(self, preset_name: str, limit: int = 25, **kwargs) -> List[Song]:
        start_time = time.perf_counter()
        now = datetime.now()

        if self._favorites_service: 
            self._favorites_service.sync_favorites()
            
        # 1. ライブラリ全取得
        all_songs_raw = self._library_service.fetch_songs(size=10000)
        
        # ★バグ修正: 禁止リスト（Blocklist）による物理除外をここに配置
        if self._blacklist_service:
            all_songs = [
                s for s in all_songs_raw 
                if not self._blacklist_service.is_blacklisted(s)
            ]
            self._logger.info(f"Blocklist filtered: {len(all_songs_raw)} -> {len(all_songs)} songs")
        else:
            all_songs = all_songs_raw

        history = self._history_service.fetch_history(size=2000)
        days_map = self._history_service.prepare_context(history, all_songs, now)

        # 2. Pipeline Execution
        clean_pool, scored_list, rotation_history = self._pipeline.execute(
            all_songs, days_map, now, preset_name, kwargs
        )

        # 3. Strategy Execution (Get 2x buffer)
        context = {"days_since_last_play": days_map, "suppress_instrumental": True, "suppress_live": True}
        strategy = self._strategy_factory.create(preset_name)
        raw_candidates = strategy.generate(scored_list, days_map, limit * 2, clean_pool, context)

        # 4. Filter Execution
        div_engine = DiversityEngine(suppress_instrumental=True, suppress_live=True, filter_versions=True)
        unique_candidates = self._unique_by_id(raw_candidates)
        all_filtered = div_engine.apply(unique_candidates)
        
        # 5. Initial Selection
        strat_songs = all_filtered[:limit]
        
        # 6. Execute Refill Engine
        final_songs, refill_songs = self._refill_engine.refill(
            strat_songs, scored_list, limit, preset_name, days_map
        )

        # 7. Final Shuffle & Statistics
        random.shuffle(final_songs)
        gen_time = int((time.perf_counter() - start_time) * 1000)
        
        stats_data = self._stats_collector.collect(
            preset_name, limit, all_songs, clean_pool, scored_list, 
            final_songs, strat_songs, refill_songs, days_map, 
            rotation_history, gen_time, context
        )


        # 7. Final Shuffle & Statistics
        random.shuffle(final_songs)
        gen_time = int((time.perf_counter() - start_time) * 1000)
        
        stats_data = self._stats_collector.collect(
            preset_name, limit, all_songs, clean_pool, scored_list, 
            final_songs, strat_songs, refill_songs, days_map, 
            rotation_history, gen_time, context
        )

        # ★バグ修正: 統計データだけでなく、曲ごとのスコア詳細（scored_list）も保存する
        self._last_stats = stats_data
        self._last_scored_list = scored_list # この行を追加
        
        self._logger.info(f"\n{ReportFormatter.format(stats_data)}")
        self._save_to_history(preset_name, now, final_songs)

        # 統計データを保存
        self._last_stats = stats_data

        self._logger.info(f"\n{ReportFormatter.format(stats_data)}")
        self._save_to_history(preset_name, now, final_songs)
        return final_songs

    def _unique_by_id(self, songs: List[Song]) -> List[Song]:
        seen, unique = set(), []
        for s in songs:
            if s.id not in seen:
                unique.append(s)
                seen.add(s.id)
        return unique

    def _save_to_history(self, preset: str, now: datetime, songs: List[Song]) -> None:
        preset_key = preset.lower().replace(" ", "_")
        song_dicts = [{"id": s.id, "title": s.title, "artist": s.artist} for s in songs]
        self._mix_history_service.save_mix(preset=preset_key, timestamp=now.isoformat(), songs=song_dicts)