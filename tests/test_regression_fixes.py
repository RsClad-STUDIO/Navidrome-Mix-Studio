import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from api.navidrome_client import NavidromeClient
from engine.candidate_generator import CandidateGenerator
from engine.filters.artist_filter import ArtistFilter
from engine.filters.album_filter import AlbumFilter
from engine.filters.diversity_engine import DiversityEngine
from engine.filters.version_filter import VersionFilter
from engine.mix_generator import MixGenerator
from engine.pipeline.purge_engine import PurgeEngine
from engine.pipeline.refill_engine import RefillEngine
from engine.pipeline.rotation_calculator import RotationCalculator
from engine.strategies.daily_strategy import DailyStrategy
from engine.reporting.report_formatter import ReportFormatter
from engine.scoring.calculator import ScoringCalculator
from models.history import HistoryEntry
from models.song import Song
from models.music_score import MusicScore
from services.favorites_service import FavoritesService
from services.history_service import HistoryService
from services.library_analyzer import LibraryAnalyzer
from services.mix_history_service import MixHistoryService
from services.playlist_service import PlaylistService


class RegressionFixTests(unittest.TestCase):
    def test_recent_played_timestamp_is_parsed_as_utc(self):
        entry = HistoryEntry.from_dict({
            "id": "song-1",
            "title": "Title",
            "artist": "Artist",
            "played": "2026-11-03T12:00:00Z",
        })
        self.assertEqual(entry.song_id, "song-1")
        self.assertEqual(entry.played_at.utcoffset().total_seconds(), 0)

    def test_recent_played_numeric_timestamp_uses_milliseconds(self):
        entry = HistoryEntry.from_dict({
            "id": "song-1",
            "played": 1793707200000,
        })
        self.assertIsNotNone(entry.played_at)
        self.assertEqual(entry.played_at.tzinfo, __import__("datetime").timezone.utc)

    def test_now_playing_is_not_treated_as_playback_history(self):
        client = NavidromeClient("http://example.test", "user", "pass")
        def response_for(endpoint, *args, **kwargs):
            if endpoint == "getPlaylists":
                return {"playlists": {"playlist": {"id": "pl-1", "name": "One"}}}
            if endpoint in {"getRecentPlayed", "getHistory"}:
                raise RuntimeError("404 endpoint not found")
            if endpoint == "getNowPlaying":
                return {"nowPlaying": {"entry": {"id": "song-1", "title": "One"}}}
            return {}
        client._request = Mock(side_effect=response_for)
        self.assertEqual(client.get_playlists(), [{"id": "pl-1", "name": "One"}])
        with self.assertRaisesRegex(RuntimeError, "No supported playback-history"):
            client.get_history()
        self.assertNotIn(
            "getNowPlaying",
            [call.args[0] for call in client._request.call_args_list],
        )

    def test_candidate_generator_preserves_all_favorites_and_deduplicates_ids(self):
        songs = [
            Song(id="fav-1", title="Favorite", artist="A"),
            Song(id="fav-2", title="Favorite 2", artist="B"),
            Song(id="other-1", title="Other", artist="C"),
            Song(id="other-1", title="Duplicate", artist="D"),
        ]
        favorites = Mock(side_effect=lambda song_id: song_id.startswith("fav-"))
        generator = CandidateGenerator(favorites_service=SimpleNamespace(
            is_song_favorite=favorites
        ))
        result = generator.generate_candidates(songs, target_limit=1, multiplier=1)
        self.assertEqual({song.id for song in result}, {"fav-1", "fav-2"})
        self.assertTrue(all(song.starred for song in result))

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

    def test_diversity_engine_legacy_title_helpers_remain_available(self):
        song = Song(id="1", title="Song (Live)", artist="Artist")
        self.assertEqual(DiversityEngine.normalize_title(song.title), "song")
        self.assertTrue(DiversityEngine.is_version_variant(song))

    def test_rotation_calculator_legacy_helpers_remain_available(self):
        self.assertEqual(RotationCalculator.calculate_penalty_rate(10, False), 0.02)
        self.assertEqual(RotationCalculator.calculate_penalty_rate(10, True), 0.0)
        self.assertEqual(RotationCalculator.calculate_penalty_rate(-1, False), 0.0)

        old_low = Song(id="old-low", title="Old low", artist="A")
        old_high = Song(id="old-high", title="Old high", artist="B")
        fresh = Song(id="fresh", title="Fresh", artist="C")
        details = {
            old_low.id: {"song": old_low, "final_score": 10.0},
            old_high.id: {"song": old_high, "final_score": 20.0},
            fresh.id: {"song": fresh, "final_score": 15.0},
        }
        result = RotationCalculator.apply_rotation_budget(
            candidate_selected=[old_low, old_high],
            prev_mix_ids={old_low.id, old_high.id},
            prev_mix_songs_map={old_low.id: old_low, old_high.id: old_high},
            score_details=details,
            limit=2,
            max_budget=1,
        )
        self.assertEqual({song.id for song in result}, {"old-high", "fresh"})

    def test_mix_generator_uses_server_side_search_query(self):
        song = Song(
            id="song-1",
            title="Ambient Song",
            artist="Ambient Artist",
            album="Ambient Album",
        )
        score = MusicScore(
            song_id=song.id,
            title=song.title,
            artist=song.artist,
            album=song.album,
            play_count=0,
            song=song,
            total_score=100.0,
        )
        library_service = Mock()
        library_service.fetch_songs.return_value = [song]
        history_service = Mock()
        history_service.fetch_history.return_value = []
        history_service.prepare_context.return_value = {}
        history_service.last_fetch_succeeded = True
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
        generator._stats_collector.collect.return_value = SimpleNamespace()

        with patch("engine.mix_generator.DiversityEngine") as diversity_factory:
            diversity_factory.return_value.apply.return_value = [song]
            with patch("engine.mix_generator.ReportFormatter.format", return_value=""):
                generator.generate_mix(
                    "Daily Mix",
                    limit=1,
                    query="Ambient",
                    suppress_remix=True,
                    suppress_demo=True,
                )

        library_service.fetch_songs.assert_called_once_with(query="Ambient")
        self.assertTrue(generator._pipeline.execute.call_args.args[4]["suppress_demo"])
        diversity_factory.assert_called_once_with(
            suppress_instrumental=True,
            suppress_live=False,
            suppress_remix=True,
            suppress_demo=True,
            suppress_acoustic=False,
            filter_versions=True,
            target_size=1,
            available_album_count=1,
            available_artist_count=1,
        )

    def test_candidate_generator_returns_empty_for_zero_target(self):
        generator = CandidateGenerator()
        self.assertEqual(generator.generate_candidates([], target_limit=0), [])

    def test_version_filter_honors_demo_and_acoustic_options(self):
        version_filter = VersionFilter({
            "suppress_demo": True,
            "suppress_acoustic": True,
        })
        self.assertTrue(version_filter.is_suppressed(
            Song(id="demo", title="Song Demo", artist="Artist")
        ))
        self.assertTrue(version_filter.is_suppressed(
            Song(id="acoustic", title="Song Acoustic", artist="Artist")
        ))
        self.assertFalse(version_filter.is_suppressed(
            Song(id="normal", title="Song", artist="Artist")
        ))

    def test_purge_engine_applies_demo_remix_and_acoustic_options(self):
        cases = (
            ("Song Demo", "suppress_demo"),
            ("Song Remix", "suppress_remix"),
            ("Song Acoustic", "suppress_acoustic"),
        )
        for title, setting in cases:
            with self.subTest(title=title):
                song = Song(id=title, title=title, artist="Artist", duration=240)
                self.assertTrue(PurgeEngine.should_purge(song, {setting: True}))
                self.assertFalse(PurgeEngine.should_purge(song, {setting: False}))

    def test_live_filter_remains_opt_in_by_default(self):
        song = Song(
            id="live-1",
            title="Concert Live",
            artist="Artist",
            duration=240,
        )
        self.assertFalse(PurgeEngine.should_purge(song, {}))
        self.assertTrue(PurgeEngine.should_purge(song, {"suppress_live": True}))

    def test_adaptive_mode_changes_weights_based_on_library_context(self):
        adaptive = ScoringCalculator(
            mix_type="Daily",
            adaptive_mode=True,
            favorite_ratio=0.30,
            history_coverage=0.10,
        )
        fixed = ScoringCalculator(
            mix_type="Daily",
            adaptive_mode=False,
        )
        self.assertNotEqual(adaptive.w_recent, fixed.w_recent)
        self.assertNotEqual(adaptive.w_favorite, fixed.w_favorite)

    def test_history_falls_back_to_time_and_normalizes_song_id(self):
        entry = HistoryEntry.from_dict({
            "id": None,
            "songId": 123,
            "played": None,
            "time": "2026-11-03T12:00:00Z",
        })
        self.assertEqual(entry.song_id, "123")
        self.assertIsNotNone(entry.played_at)

    def test_playlist_service_handles_single_song_entry(self):
        client = SimpleNamespace(
            get_playlist=Mock(return_value={
                "entry": {
                    "id": "song-1",
                    "title": "One",
                    "artist": "Artist",
                }
            })
        )
        songs = PlaylistService(client).get_playlist_songs("playlist-1")
        self.assertEqual(len(songs), 1)
        self.assertEqual(songs[0].id, "song-1")

    def test_single_recent_played_and_history_entries_are_normalized(self):
        client = NavidromeClient("http://example.test", "user", "pass")
        client._request = Mock(return_value={
            "recentPlayed": {"entry": {"id": "recent-1"}}
        })
        self.assertEqual(client.get_history(), [{"id": "recent-1"}])
        client._request = Mock(return_value={
            "history": {"item": {"id": "history-1"}}
        })
        self.assertEqual(client.get_history(), [{"id": "history-1"}])

    def test_diversity_caps_scale_with_requested_mix_size(self):
        self.assertEqual(AlbumFilter(target_size=25).max_per_album, 6)
        self.assertEqual(AlbumFilter(target_size=50).max_per_album, 12)
        self.assertEqual(AlbumFilter(level="Low", target_size=50).max_per_album, 16)
        self.assertEqual(AlbumFilter(level="High", target_size=50).max_per_album, 6)

        songs = [
            Song(id=str(i), title=f"Song {i}", artist=f"Artist {i // 30}")
            for i in range(60)
        ]
        self.assertEqual(len(ArtistFilter(target_size=25).apply(songs)), 24)
        self.assertEqual(len(ArtistFilter(target_size=50).apply(songs)), 50)

    def test_single_album_and_single_artist_do_not_block_requested_size(self):
        songs = [
            Song(
                id=str(i),
                title=f"Unique Track {i}",
                artist="Only Artist",
                album="Only Album",
            )
            for i in range(80)
        ]
        self.assertEqual(len(AlbumFilter(target_size=50).apply(songs)), 50)
        self.assertEqual(len(ArtistFilter(target_size=50).apply(songs)), 50)
        self.assertEqual(
            len(DiversityEngine(target_size=50).apply(songs)),
            50,
        )

    def test_album_cap_rejection_does_not_reserve_duplicate_title(self):
        songs = [
            Song(id="album-a-1", title="Anchor", artist="Artist A", album="Album A"),
            Song(id="album-a-2", title="Shared Title", artist="Artist A", album="Album A"),
            Song(id="album-b-1", title="Shared Title", artist="Artist B", album="Album B"),
        ]

        filtered = AlbumFilter(
            target_size=4,
            available_album_count=2,
        ).apply(songs)

        self.assertEqual(
            [song.id for song in filtered],
            ["album-a-1", "album-b-1"],
        )

    def test_artist_filter_does_not_drop_adjacent_same_artist_candidates(self):
        songs = [
            Song(id=str(i), title=f"Song {i}", artist="Same Artist")
            for i in range(4)
        ]
        filtered = ArtistFilter().apply(songs)
        self.assertEqual([song.id for song in filtered], ["0", "1", "2", "3"])

    def test_daily_mix_refills_zero_play_count_library_to_requested_limit(self):
        songs = []
        scores = []
        for index in range(10001):
            if index < 75:
                album = "Dominant Album"
            elif index < 100:
                album = "Secondary Album"
            else:
                album = f"Album {index}"
            song = Song(
                id=f"song-{index}",
                title=f"Track {index}",
                artist=f"Artist {index}",
                album=album,
                play_count=0,
            )
            songs.append(song)
            scores.append(MusicScore(
                song_id=song.id,
                title=song.title,
                artist=song.artist,
                album=song.album,
                play_count=0,
                song=song,
                total_score=float(10001 - index),
            ))

        requested = 25
        strategy = DailyStrategy()
        raw_candidates = strategy.generate(
            scores, {}, requested * 2, songs, {"adaptive_mode": True}
        )
        filtered = DiversityEngine(filter_versions=True).apply(raw_candidates)
        initial = filtered[:requested]
        self.assertEqual(len(initial), 12)

        # A successful empty history must bootstrap zero-playcount tracks even
        # when song-level lastPlayed metadata has populated days_map.
        final, refilled = RefillEngine.refill(
            initial,
            scores,
            requested,
            "Daily Mix",
            {"song-100": 30},
            filter_config={},
            history_available=True,
            history_empty=True,
        )

        self.assertEqual(len(final), requested)
        self.assertEqual(len(refilled), requested - len(initial))
        self.assertTrue(all(song.play_count == 0 for song in final))

        # An empty map caused by an unavailable history API must not bootstrap.
        failed_history_result, failed_history_refills = RefillEngine.refill(
            initial,
            scores,
            requested,
            "Daily Mix",
            {},
            filter_config={},
            history_available=False,
            history_empty=False,
        )
        self.assertEqual(len(failed_history_result), len(initial))
        self.assertEqual(failed_history_refills, [])

    def test_favorites_mix_refills_with_unplayed_tracks_after_played_pool_is_exhausted(self):
        current_songs = []
        scores = []

        # 21 selected tracks already occupy the normal six-per-album allowance.
        for index in range(27):
            album_index = index // 6 if index < 21 else (index - 21) // 2
            song = Song(
                id=f"played-{index}",
                title=f"Played Track {index}",
                artist=f"Played Artist {index}",
                album=f"Album {album_index}",
                play_count=1,
            )
            if index < 21:
                current_songs.append(song)
            scores.append(MusicScore(
                song_id=song.id,
                title=song.title,
                artist=song.artist,
                album=song.album,
                play_count=1,
                song=song,
                total_score=float(100 - index),
            ))

        # These never-played tracks have distinct artists/albums and can safely
        # fill the remaining slots after played candidates hit diversity caps.
        for index in range(4):
            song = Song(
                id=f"unplayed-{index}",
                title=f"Unplayed Track {index}",
                artist=f"Unplayed Artist {index}",
                album=f"Unplayed Album {index}",
                play_count=0,
            )
            scores.append(MusicScore(
                song_id=song.id,
                title=song.title,
                artist=song.artist,
                album=song.album,
                play_count=0,
                song=song,
                total_score=float(10 - index),
            ))

        final, refilled = RefillEngine.refill(
            current_songs,
            scores,
            25,
            "Favorites Mix",
            {},
            filter_config={},
            history_available=True,
            history_empty=False,
        )

        self.assertEqual(len(final), 25)
        self.assertEqual(len(refilled), 4)
        self.assertTrue(all(song.play_count == 0 for song in refilled))
        self.assertEqual(len({song.id for song in final}), 25)

    def test_daily_mix_can_refill_unplayed_tracks_when_history_is_partial(self):
        existing = Song(
            id="daily-existing",
            title="Existing Track",
            artist="Existing Artist",
            album="Existing Album",
            play_count=5,
        )
        scores = [MusicScore(
            song_id=existing.id,
            title=existing.title,
            artist=existing.artist,
            album=existing.album,
            play_count=5,
            song=existing,
            total_score=90.0,
        )]
        for index in range(4):
            song = Song(
                id=f"daily-unplayed-{index}",
                title=f"Daily Unplayed {index}",
                artist=f"Daily Artist {index}",
                album=f"Daily Album {index}",
                play_count=0,
            )
            scores.append(MusicScore(
                song_id=song.id,
                title=song.title,
                artist=song.artist,
                album=song.album,
                play_count=0,
                song=song,
                total_score=float(40 - index),
            ))

        final, refilled = RefillEngine.refill(
            [existing],
            scores,
            5,
            "Daily Mix",
            {"daily-existing": 2},
            filter_config={},
            history_available=True,
            history_empty=False,
        )

        self.assertEqual(len(final), 5)
        self.assertEqual(len(refilled), 4)
        self.assertTrue(all(song.play_count == 0 for song in refilled))

    def test_discovery_refill_accepts_never_played_tracks(self):
        existing = Song(
            id="discovery-existing",
            title="Existing Discovery",
            artist="Existing Artist",
            album="Existing Album",
            play_count=1,
        )
        scores = [MusicScore(
            song_id=existing.id,
            title=existing.title,
            artist=existing.artist,
            album=existing.album,
            play_count=1,
            song=existing,
            total_score=90.0,
        )]
        for index in range(4):
            song = Song(
                id=f"discovery-new-{index}",
                title=f"Discovery New {index}",
                artist=f"Discovery Artist {index}",
                album=f"Discovery Album {index}",
                play_count=0,
            )
            scores.append(MusicScore(
                song_id=song.id,
                title=song.title,
                artist=song.artist,
                album=song.album,
                play_count=0,
                song=song,
                total_score=float(40 - index),
            ))

        final, refilled = RefillEngine.refill(
            [existing],
            scores,
            5,
            "Discovery Mix",
            {},
            filter_config={},
        )

        self.assertEqual(len(final), 5)
        self.assertEqual(len(refilled), 4)

    def test_forgotten_mix_does_not_refill_never_played_tracks(self):
        existing = Song(
            id="forgotten-existing",
            title="Forgotten Existing",
            artist="Existing Artist",
            album="Existing Album",
            play_count=3,
        )
        unplayed = Song(
            id="forgotten-unplayed",
            title="Never Played",
            artist="New Artist",
            album="New Album",
            play_count=0,
        )
        scores = [
            MusicScore(
                song_id=existing.id,
                title=existing.title,
                artist=existing.artist,
                album=existing.album,
                play_count=3,
                song=existing,
                total_score=90.0,
            ),
            MusicScore(
                song_id=unplayed.id,
                title=unplayed.title,
                artist=unplayed.artist,
                album=unplayed.album,
                play_count=0,
                song=unplayed,
                total_score=40.0,
            ),
        ]

        final, refilled = RefillEngine.refill(
            [existing],
            scores,
            2,
            "Forgotten Favorites",
            {},
            filter_config={},
            history_available=True,
            history_empty=True,
        )

        self.assertEqual(final, [existing])
        self.assertEqual(refilled, [])

    def test_navidrome_history_raises_when_all_history_endpoints_fail(self):
        client = NavidromeClient("http://example.test", "user", "pass")
        client._request = Mock(side_effect=RuntimeError("404 Not Found"))
        with self.assertRaises(RuntimeError):
            client.get_history()

    def test_history_service_distinguishes_empty_history_from_fetch_failure(self):
        successful = HistoryService(SimpleNamespace(get_history=Mock(return_value=[])))
        self.assertEqual(successful.fetch_history(), [])
        self.assertTrue(successful.last_fetch_succeeded)

        failed = HistoryService(SimpleNamespace(
            get_history=Mock(side_effect=RuntimeError("API unavailable"))
        ))
        self.assertEqual(failed.fetch_history(), [])
        self.assertFalse(failed.last_fetch_succeeded)

    def test_empty_playlist_report_does_not_divide_by_zero(self):
        data = SimpleNamespace(
            preset="Daily Mix",
            library_total=0,
            pool_count=0,
            gen_time_ms=0,
            strat_initial_count=0,
            limit=25,
            strat_composition={},
            refill_total=0,
            conf_refill_penalty_pct=0,
            confidence=0,
            utilization=[],
            rotation=SimpleNamespace(affected=0, avg_penalty=0.0),
            scores=SimpleNamespace(highest=0.0, lowest=0.0, average=0.0, median=0.0),
            diversity=SimpleNamespace(
                unique_artists=0, total_artists=0,
                unique_albums=0, total_albums=0,
                ratio_artist=0.0, ratio_album=0.0,
                assessment_level="Low",
            ),
            final_total=0,
            final_composition={"discovery": 1},
        )
        report = ReportFormatter.format(data)
        self.assertIn("Result: 0 songs generated successfully.", report)
        self.assertIn("Random Discovery", report)

    def test_favorites_cache_keys_are_server_scoped(self):
        cache = Mock()
        cache.get.return_value = None
        first_client = SimpleNamespace(
            server_url="http://server-one", username="user",
            get_starred=Mock(return_value={"song": [], "artist": [], "album": []}),
        )
        second_client = SimpleNamespace(
            server_url="http://server-two", username="user",
            get_starred=Mock(return_value={"song": [], "artist": [], "album": []}),
        )
        FavoritesService(first_client, cache).sync_favorites()
        FavoritesService(second_client, cache).sync_favorites()
        keys = [call.args[0] for call in cache.get.call_args_list]
        self.assertEqual(len(keys), 2)
        self.assertNotEqual(keys[0], keys[1])

    def test_library_profile_cache_is_invalidated_when_library_changes(self):
        class MemoryCache:
            def __init__(self):
                self.values = {}

            def get(self, key):
                return self.values.get(key)

            def set(self, key, value):
                self.values[key] = value

        cache = MemoryCache()
        analyzer = LibraryAnalyzer(
            cache_manager=cache,
            cache_namespace="https://server.example|user",
        )
        analyzer.analyze_library([
            Song(id="1", title="Song", artist="Artist A"),
        ])
        updated = analyzer.analyze_library([
            Song(id="1", title="Song", artist="Artist B"),
            Song(id="2", title="Other", artist="Artist C"),
        ])
        self.assertEqual(updated.total_songs, 2)
        self.assertEqual(updated.total_artists, 2)
        self.assertIn("Artist B", updated.artist_distribution)
        self.assertNotIn("Artist A", updated.artist_distribution)

    def test_library_profile_cache_keys_are_server_scoped(self):
        first = LibraryAnalyzer(cache_namespace="server-one|user")
        second = LibraryAnalyzer(cache_namespace="server-two|user")
        self.assertNotEqual(first._cache_key, second._cache_key)

    def test_corrupt_mix_history_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "mix_history.json"
            original = "{broken json"
            path.write_text(original, encoding="utf-8")
            service = MixHistoryService(storage_path=str(path))
            self.assertFalse(service.save_mix(
                preset="daily_mix",
                timestamp="2026-11-03T12:00:00",
                songs=[{"id": "song-1"}],
            ))
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_mix_history_skips_same_preset_and_same_songs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = MixHistoryService(
                storage_path=str(Path(temp_dir) / "mix_history.json")
            )
            songs = [
                {"id": "song-1", "title": "One"},
                {"id": "song-2", "title": "Two"},
            ]
            self.assertTrue(service.save_mix(
                preset="daily_mix",
                timestamp="2026-11-03T12:00:00",
                songs=songs,
            ))
            self.assertFalse(service.save_mix(
                preset="daily_mix",
                timestamp="2026-11-03T12:05:00",
                songs=songs,
            ))
            self.assertTrue(service.last_save_was_duplicate)
            self.assertEqual(len(service.load_history()), 1)

    def test_mix_history_duplicate_detection_ignores_song_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = MixHistoryService(
                storage_path=str(Path(temp_dir) / "mix_history.json")
            )
            self.assertTrue(service.save_mix(
                preset="daily_mix",
                timestamp="2026-11-03T12:00:00",
                songs=[{"id": "song-1"}, {"id": "song-2"}],
            ))
            self.assertFalse(service.save_mix(
                preset="daily_mix",
                timestamp="2026-11-03T12:05:00",
                songs=[{"id": "song-2"}, {"id": "song-1"}],
            ))
            self.assertTrue(service.last_save_was_duplicate)
            self.assertEqual(len(service.load_history()), 1)

    def test_mix_history_allows_different_preset_or_song_set(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            service = MixHistoryService(
                storage_path=str(Path(temp_dir) / "mix_history.json")
            )
            original_songs = [{"id": "song-1"}, {"id": "song-2"}]
            self.assertTrue(service.save_mix(
                preset="daily_mix",
                timestamp="2026-11-03T12:00:00",
                songs=original_songs,
            ))
            self.assertTrue(service.save_mix(
                preset="favorites_mix",
                timestamp="2026-11-03T12:05:00",
                songs=original_songs,
            ))
            self.assertTrue(service.save_mix(
                preset="daily_mix",
                timestamp="2026-11-03T12:10:00",
                songs=[{"id": "song-1"}, {"id": "song-3"}],
            ))
            self.assertEqual(len(service.load_history()), 3)
            self.assertFalse(service.last_save_was_duplicate)

    def test_mix_history_storage_is_server_scoped(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = str(Path(temp_dir) / "mix_history.json")
            first = MixHistoryService(storage_path=base, namespace="server-one|user")
            second = MixHistoryService(storage_path=base, namespace="server-two|user")
            self.assertNotEqual(first._storage_path, second._storage_path)
            self.assertTrue(first._storage_path.exists())
            self.assertTrue(second._storage_path.exists())


if __name__ == "__main__":
    unittest.main()
