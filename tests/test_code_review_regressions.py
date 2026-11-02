import unittest

from engine.candidate_generator import CandidateGenerator
from engine.filters.diversity_engine import DiversityEngine
from engine.filters.version_filter import VersionFilter
from engine.reporting.report_formatter import ReportFormatter
from models.song import Song
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
