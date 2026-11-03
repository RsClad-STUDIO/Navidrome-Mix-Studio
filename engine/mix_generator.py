import logging
import random
import time
from datetime import datetime
from typing import List

from models.song import Song
from engine.pipeline.candidate_pipeline import CandidatePipeline
from engine.pipeline.refill_engine import RefillEngine
from engine.reporting.statistics_collector import StatisticsCollector
from engine.reporting.report_formatter import ReportFormatter
from engine.filters.diversity_engine import DiversityEngine
from engine.factory.strategy_factory import StrategyFactory
from services.mix_history_service import MixHistoryService


class MixGenerator:
    HARD_DURATION_LIMIT = 10800

    def __init__(self, **kwargs) -> None:
        self._logger = logging.getLogger("MixGenerator")
        self._library_service = kwargs.get("library_service")
        self._history_service = kwargs.get("history_service")
        self._favorites_service = kwargs.get("favorites_service")
        self._blacklist_service = kwargs.get("blacklist_service")
        self._mix_history_service = kwargs.get("mix_history_service") or MixHistoryService()
        self._pipeline = CandidatePipeline(
            self._favorites_service, self._mix_history_service, self._logger
        )
        self._refill_engine = RefillEngine()
        self._stats_collector = StatisticsCollector()
        self._strategy_factory = StrategyFactory()
        self._last_stats = None
        self._last_scored_list = []

    def generate_mix(self, preset_name: str, limit: int = 25, **kwargs) -> List[Song]:
        start_time = time.perf_counter()
        now = datetime.now()

        filter_config = {
            "suppress_instrumental": kwargs.get("suppress_instrumental", True),
            "suppress_live": kwargs.get("suppress_live", False),
            "suppress_remix": kwargs.get("suppress_remix", False),
            "suppress_demo": kwargs.get("suppress_demo", False),
            "suppress_acoustic": kwargs.get("suppress_acoustic", False),
        }

        if self._favorites_service:
            self._favorites_service.sync_favorites()

        all_songs_raw = self._library_service.fetch_songs()
        if self._blacklist_service:
            all_songs = [
                song for song in all_songs_raw
                if not self._blacklist_service.is_blacklisted(song)
            ]
            self._logger.info(
                "Blocklist filtered: %s -> %s songs",
                len(all_songs_raw), len(all_songs)
            )
        else:
            all_songs = all_songs_raw

        history = self._history_service.fetch_history(size=2000)
        days_map = self._history_service.prepare_context(history, all_songs, now)

        adaptive_mode = bool(kwargs.get("adaptive_mode", True))
        clean_pool, scored_list, rotation_history = self._pipeline.execute(
            all_songs,
            days_map,
            now,
            preset_name,
            filter_config,
            adaptive_mode=adaptive_mode,
        )

        # 検索欄が空なら従来どおり全候補を使用します。
        # 入力がある場合は曲名・アーティスト名・アルバム名の部分一致で候補を限定します。
        query = " ".join(str(kwargs.get("query") or "").casefold().split())
        if query:
            def matches_query(song: Song) -> bool:
                searchable = " ".join(
                    str(value or "")
                    for value in (song.title, song.artist, song.album)
                ).casefold()
                return query in searchable

            clean_pool = [song for song in clean_pool if matches_query(song)]
            matching_ids = {song.id for song in clean_pool}
            scored_list = [
                music_score for music_score in scored_list
                if music_score.song_id in matching_ids
            ]
            self._logger.info(
                "Search filter applied: query=%r, candidates=%s",
                query, len(clean_pool)
            )

        library_count = len(clean_pool)
        favorite_ratio = (
            sum(1 for song in clean_pool if song.starred) / library_count
            if library_count else 0.0
        )
        history_coverage = (
            sum(1 for song in clean_pool if song.id in days_map) / library_count
            if library_count else 0.0
        )
        context = {
            "days_since_last_play": days_map,
            "history_loaded": len(history),
            "favorite_ratio": favorite_ratio,
            "history_coverage": history_coverage,
            "adaptive_mode": adaptive_mode,
            "query": query,
            **filter_config,
        }
        strategy = self._strategy_factory.create(preset_name)
        raw_candidates = strategy.generate(
            scored_list, days_map, limit * 2, clean_pool, context
        )

        div_engine = DiversityEngine(**filter_config, filter_versions=True)
        unique_candidates = self._unique_by_id(raw_candidates)
        all_filtered = div_engine.apply(unique_candidates)

        strat_songs = all_filtered[:limit]
        final_songs, refill_songs = self._refill_engine.refill(
            strat_songs,
            scored_list,
            limit,
            preset_name,
            days_map,
            filter_config=filter_config,
        )

        random.shuffle(final_songs)
        gen_time = int((time.perf_counter() - start_time) * 1000)
        stats_data = self._stats_collector.collect(
            preset_name, limit, all_songs, clean_pool, scored_list,
            final_songs, strat_songs, refill_songs, days_map,
            rotation_history, gen_time, context
        )

        self._last_stats = stats_data
        self._last_scored_list = scored_list
        self._logger.info("\n%s", ReportFormatter.format(stats_data))
        self._save_to_history(preset_name, now, final_songs)
        return final_songs

    def _unique_by_id(self, songs: List[Song]) -> List[Song]:
        seen, unique = set(), []
        for song in songs:
            if song.id not in seen:
                unique.append(song)
                seen.add(song.id)
        return unique

    def _save_to_history(self, preset: str, now: datetime, songs: List[Song]) -> None:
        preset_key = preset.lower().replace(" ", "_")
        song_dicts = [
            {"id": song.id, "title": song.title, "artist": song.artist}
            for song in songs
        ]
        self._mix_history_service.save_mix(
            preset=preset_key, timestamp=now.isoformat(), songs=song_dicts
        )
