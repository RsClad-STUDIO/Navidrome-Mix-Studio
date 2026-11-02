import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from engine.candidate_generator import CandidateGenerator
from engine.mix_generator import MixGenerator
from engine.preset_strategy import FavoritesStrategy
from engine.filters.diversity_engine import DiversityEngine
from engine.filters.version_filter import VersionFilter
from engine.pipeline.purge_engine import PurgeEngine
from engine.pipeline.rotation_calculator import RotationCalculator
from engine.reporting.report_formatter import ReportFormatter
from api.navidrome_client import NavidromeClient
from models.song import Song
from models.music_score import MusicScore
from services.history_service import HistoryService
from models.history import HistoryEntry
from services.library_analyzer import LibraryAnalyzer
from services.favorites_service import FavoritesService
from models.statistics_data import (
    DiversityStats,
    RotationStats,
    ScoreStats,
    StatisticsData,
)


class FavoriteLookup:
    def __init__(self, favorite_ids):
        self.favorite_ids = set(favorite_ids)

    def is_song_favorite(self, song_id):
        return song_id in self.favorite_ids


class CandidateGeneratorTests(unittest.TestCase):
    def test_filters_duplicates_and_keeps_all_favorites(self):
        songs = [
            Song(id="fav-1", title="Favorite", artist="A"),
            Song(id="fav-2", title="Favorite 2", artist="B"),
            Song(id="other-1", title="Other", artist="C"),
            Song(id="other-1", title="Duplicate", artist="D"),
        ]
        generator = CandidateGenerator(
            favorites_service=FavoriteLookup({"fav-1", "fav-2"})
        )

        result = generator.generate_candidates(songs, target_limit=1, multiplier=1)

        self.assertEqual({song.id for song in result}, {"fav-1", "fav-2"})
        self.assertTrue(all(song.starred for song in result))

    def test_zero_candidate_target_returns_empty_list(self):
        generator = CandidateGenerator()
        self.assertEqual(generator.generate_candidates([], target_limit=0), [])


class RotationCalculatorTests(unittest.TestCase):
    def test_penalty_rate_caps_and_protects_priority_tracks(self):
        self.assertEqual(RotationCalculator.calculate_penalty_rate(10, False), 0.02)
        self.assertEqual(RotationCalculator.calculate_penalty_rate(10, True), 0.0)
        self.assertEqual(RotationCalculator.calculate_penalty_rate(-1, False), 0.0)

    def test_rotation_budget_replaces_lowest_scoring_repeated_track(self):
        old_low = Song(id="old-low", title="Old low", artist="A")
        old_high = Song(id="old-high", title="Old high", artist="B")
        fresh = Song(id="fresh", title="Fresh", artist="C")
        score_details = {
            old_low.id: {"song": old_low, "final_score": 10.0},
            old_high.id: {"song": old_high, "final_score": 20.0},
            fresh.id: {"song": fresh, "final_score": 15.0},
        }

        result = RotationCalculator.apply_rotation_budget(
            candidate_selected=[old_low, old_high],
            prev_mix_ids={old_low.id, old_high.id},
            prev_mix_songs_map={old_low.id: old_low, old_high.id: old_high},
            score_details=score_details,
            limit=2,
            max_budget=1,
        )

        self.assertEqual({song.id for song in result}, {"old-high", "fresh"})


class LegacyFavoritesStrategyTests(unittest.TestCase):
    def test_favorites_strategy_fills_available_non_favorite_slots(self):
        songs = [
            Song(id="favorite", title="Favorite", artist="A", starred=True, play_count=20),
            Song(id="other-1", title="Other 1", artist="B", play_count=5),
            Song(id="other-2", title="Other 2", artist="C", play_count=4),
            Song(id="other-3", title="Other 3", artist="D", play_count=3),
            Song(id="other-4", title="Other 4", artist="E", play_count=2),
        ]

        selected, metrics = FavoritesStrategy().execute_selection(
            songs, limit=4, context={}
        )

        self.assertEqual(len(selected), 4)
        self.assertEqual(metrics["favorite_count"], 1)
        self.assertEqual(metrics["non_favorite_count"], 3)


class NavidromeClientCollectionTests(unittest.TestCase):
    def test_get_artists_flattens_artist_indexes(self):
        client = NavidromeClient()
        client._request = lambda endpoint, params=None: {
            "artists": {
                "index": [
                    {"name": "A", "artist": [{"id": "1", "name": "Artist A"}]},
                    {"name": "B", "artist": {"id": "2", "name": "Artist B"}},
                ]
            }
        }

        self.assertEqual(
            [artist["id"] for artist in client.get_artists()],
            ["1", "2"],
        )

    def test_singleton_starred_song_is_normalized_to_a_list(self):
        client = NavidromeClient()
        client._request = lambda endpoint, params=None: {
            "starred": {"song": {"id": "song-1"}, "album": None, "artist": None}
        }

        self.assertEqual(client.get_starred()["song"], [{"id": "song-1"}])
        self.assertEqual(client.get_starred()["album"], [])

    def test_singleton_now_playing_entry_is_preserved(self):
        client = NavidromeClient()
        responses = iter([
            {},
            {},
            {"nowPlaying": {"entry": {"id": "song-1"}}},
        ])
        client._request = lambda endpoint, params=None, **kwargs: next(responses)

        self.assertEqual(client.get_history(), [{"id": "song-1"}])

    def test_get_albums_handles_single_album_response(self):
        client = NavidromeClient()
        client._request = lambda endpoint, params=None: {
            "albumList2": {"album": {"id": "album-1", "name": "Album"}}
        }

        self.assertEqual(
            [album["id"] for album in client.get_albums(size=1)],
            ["album-1"],
        )


class VersionFilterTests(unittest.TestCase):
    def test_demo_and_acoustic_options_are_honored(self):
        version_filter = VersionFilter(
            {"suppress_demo": True, "suppress_acoustic": True}
        )

        self.assertTrue(
            version_filter.is_suppressed(
                Song(id="1", title="Song Demo", artist="Artist")
            )
        )
        self.assertTrue(
            version_filter.is_suppressed(
                Song(id="2", title="Song Acoustic", artist="Artist")
            )
        )
        self.assertFalse(
            version_filter.is_suppressed(
                Song(id="3", title="Song", artist="Artist")
            )
        )

    def test_legacy_title_helpers_are_available(self):
        song = Song(id="1", title="Song (Live)", artist="Artist")
        self.assertEqual(DiversityEngine.normalize_title(song.title), "song")
        self.assertTrue(DiversityEngine.is_version_variant(song))


class MixGeneratorConfigurationTests(unittest.TestCase):
    def test_search_query_and_version_options_reach_the_pipeline(self):
        song = Song(id="song-1", title="Song", artist="Artist")
        score = MusicScore(song_id=song.id, title=song.title, artist=song.artist)
        score.song = song

        library_service = Mock()
        library_service.fetch_songs.return_value = [song]
        history_service = Mock()
        history_service.fetch_history.return_value = []
        history_service.prepare_context.return_value = {}
        mix_history_service = Mock()

        generator = MixGenerator(
            library_service=library_service,
            history_service=history_service,
            mix_history_service=mix_history_service,
        )
        generator._pipeline = Mock()
        generator._pipeline.execute.return_value = ([song], [score], {})
        strategy = Mock()
        strategy.generate.return_value = [song]
        generator._strategy_factory = Mock()
        generator._strategy_factory.create.return_value = strategy
        generator._refill_engine = Mock()
        generator._refill_engine.refill.return_value = ([song], [])
        generator._stats_collector = Mock()
        generator._stats_collector.collect.return_value = object()

        with patch("engine.mix_generator.DiversityEngine") as diversity_factory:
            with patch("engine.mix_generator.ReportFormatter.format", return_value="report"):
                generator.generate_mix(
                    "Daily Mix",
                    limit=1,
                    query="ambient",
                    suppress_instrumental=True,
                    suppress_live=False,
                    suppress_remix=True,
                    suppress_demo=True,
                    suppress_acoustic=False,
                )

        library_service.fetch_songs.assert_called_once_with(query="ambient")
        diversity_factory.assert_called_once_with(
            suppress_instrumental=True,
            suppress_live=False,
            suppress_remix=True,
            suppress_demo=True,
            suppress_acoustic=False,
            filter_versions=True,
        )
        self.assertEqual(
            generator._pipeline.execute.call_args.args[4]["suppress_demo"],
            True,
        )


class PurgeEngineTests(unittest.TestCase):
    def test_configured_demo_remix_and_acoustic_filters_are_applied(self):
        cases = (
            ("Song Demo", "suppress_demo"),
            ("Song Remix", "suppress_remix"),
            ("Song Acoustic", "suppress_acoustic"),
        )
        for title, setting in cases:
            with self.subTest(title=title):
                song = Song(id=title, title=title, artist="Artist")
                self.assertTrue(PurgeEngine.should_purge(song, {setting: True}))
                self.assertFalse(PurgeEngine.should_purge(song, {setting: False}))

    def test_live_filter_is_disabled_unless_requested(self):
        song = Song(id="live", title="Concert", artist="Artist", duration=2400)

        self.assertFalse(PurgeEngine.should_purge(song, {"suppress_live": False}))
        self.assertTrue(PurgeEngine.should_purge(song, {"suppress_live": True}))


class InMemoryCache:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value
        return True


class CacheIsolationTests(unittest.TestCase):
    def test_library_profile_cache_is_invalidated_when_library_changes(self):
        cache = InMemoryCache()
        analyzer = LibraryAnalyzer(cache_manager=cache)

        first = analyzer.analyze_library(
            [Song(id="1", title="One", artist="Artist A")]
        )
        second = analyzer.analyze_library(
            [Song(id="2", title="Two", artist="Artist B")]
        )

        self.assertEqual(first.total_artists, 1)
        self.assertEqual(second.total_artists, 1)
        self.assertIn("Artist B", second.artist_distribution)
        self.assertNotIn("Artist A", second.artist_distribution)

    def test_favorites_cache_is_scoped_to_server_and_user(self):
        cache = InMemoryCache()

        class FakeClient:
            def __init__(self, server_url, username):
                self.server_url = server_url
                self.username = username

            def get_starred(self):
                return {"song": [], "artist": [], "album": []}

        FavoritesService(FakeClient("https://one.example", "user"), cache).sync_favorites()
        FavoritesService(FakeClient("https://two.example", "user"), cache).sync_favorites()

        self.assertEqual(len(cache.values), 2)


class TimestampNormalizationTests(unittest.TestCase):
    def test_song_timestamp_is_converted_to_local_time_before_timezone_removal(self):
        raw_timestamp = "2026-11-02T12:00:00+00:00"
        expected = datetime.fromisoformat(raw_timestamp).astimezone().replace(tzinfo=None)

        song = Song.from_dict(
            {"id": "1", "title": "Song", "artist": "Artist", "lastPlayed": raw_timestamp}
        )

        self.assertEqual(song.last_played, expected)

    def test_future_playback_timestamps_do_not_produce_negative_age(self):
        now = datetime(2026, 11, 2, 12, 0, 0)
        entry = HistoryEntry(
            song_id="future-song",
            title="Future",
            artist="Artist",
            played_at=now + timedelta(days=2),
        )

        days = HistoryService(client=None).prepare_context([entry], [], now)

        self.assertEqual(days["future-song"], 0)

    def test_history_timestamp_is_converted_to_local_time_before_timezone_removal(self):
        aware_timestamp = datetime.fromisoformat("2026-11-02T12:00:00+00:00")
        expected = aware_timestamp.astimezone().replace(tzinfo=None)

        self.assertEqual(HistoryService._make_naive(aware_timestamp), expected)


class ReportFormatterTests(unittest.TestCase):
    def test_empty_playlist_does_not_divide_by_zero(self):
        data = StatisticsData(
            preset="Favorites Mix",
            limit=25,
            library_total=0,
            pool_count=0,
            history_loaded=0,
            gen_time_ms=0,
            confidence=100,
            utilization=[],
            rotation=RotationStats(0, 0.0, 0.0, 0),
            scores=ScoreStats(0.0, 0.0, 0.0, 0.0, 0.0),
            diversity=DiversityStats(0, 0, 0, 0, 0.0, 0.0, "Low", ""),
            strat_initial_count=0,
            refill_total=0,
            refill_sources={},
            strat_composition={},
            final_composition={"favorite": 0},
            final_total=0,
        )

        report = ReportFormatter.format(data)
        self.assertIn("Result: 0 songs generated successfully.", report)


if __name__ == "__main__":
    unittest.main()
