import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from api.navidrome_client import NavidromeClient
from engine.filters.artist_filter import ArtistFilter
from engine.filters.album_filter import AlbumFilter
from engine.filters.diversity_engine import DiversityEngine
from engine.pipeline.refill_engine import RefillEngine
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

    def test_singleton_playlists_and_now_playing_are_normalized(self):
        client = NavidromeClient("http://example.test", "user", "pass")
        def response_for(endpoint, *args, **kwargs):
            if endpoint == "getPlaylists":
                return {"playlists": {"playlist": {"id": "pl-1", "name": "One"}}}
            if endpoint == "getNowPlaying":
                return {"nowPlaying": {"entry": {"id": "song-1", "title": "One"}}}
            return {}
        client._request = Mock(side_effect=response_for)
        self.assertEqual(client.get_playlists(), [{"id": "pl-1", "name": "One"}])
        self.assertEqual(client.get_history(), [{"id": "song-1", "title": "One"}])

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
