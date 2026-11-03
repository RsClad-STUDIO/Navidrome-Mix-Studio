import unittest
from unittest.mock import Mock

from api.navidrome_client import NavidromeClient


class NavidromeFavoritesNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.client = NavidromeClient(
            server_url="http://navidrome.example",
            username="test",
            password="test",
        )
        self.client._request = Mock()

    def test_normalizes_single_objects_to_lists(self):
        self.client._request.return_value = {
            "starred": {
                "song": {"id": "song-1"},
                "album": {"id": "album-1"},
                "artist": {"id": "artist-1"},
            }
        }

        self.assertEqual(self.client.get_starred(), {
            "song": [{"id": "song-1"}],
            "album": [{"id": "album-1"}],
            "artist": [{"id": "artist-1"}],
        })

    def test_normalizes_missing_categories_to_empty_lists(self):
        self.client._request.return_value = {"starred": {"song": None}}

        self.assertEqual(self.client.get_starred(), {
            "song": [],
            "album": [],
            "artist": [],
        })

    def test_preserves_existing_arrays(self):
        songs = [{"id": "song-1"}, {"id": "song-2"}]
        self.client._request.return_value = {"starred": {"song": songs}}

        self.assertEqual(self.client.get_starred()["song"], songs)


if __name__ == "__main__":
    unittest.main()
