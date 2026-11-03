import unittest
from unittest.mock import Mock

from api.navidrome_client import NavidromeClient


class NavidromeLibraryEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = NavidromeClient(
            server_url="http://navidrome.example",
            username="test",
            password="test",
        )
        self.client._request = Mock()

    def test_flattens_artist_index_and_normalizes_single_artist(self):
        self.client._request.return_value = {
            "artists": {
                "index": {
                    "name": "A",
                    "artist": {"id": "artist-1", "name": "Artist One"},
                }
            }
        }

        self.assertEqual(self.client.get_artists(), [
            {"id": "artist-1", "name": "Artist One"}
        ])

    def test_supports_direct_artist_response(self):
        self.client._request.return_value = {
            "artists": {"artist": {"id": "artist-2", "name": "Artist Two"}}
        }

        self.assertEqual(self.client.get_artists(), [
            {"id": "artist-2", "name": "Artist Two"}
        ])

    def test_normalizes_single_album_response(self):
        album = {"id": "album-1", "name": "Album One"}
        self.client._request.return_value = {"albumList2": {"album": album}}

        self.assertEqual(self.client.get_albums(), [album])

    def test_does_not_request_albums_for_non_positive_size(self):
        self.assertEqual(self.client.get_albums(size=0), [])
        self.client._request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
