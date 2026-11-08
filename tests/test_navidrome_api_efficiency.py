import unittest
from unittest.mock import Mock

from api.navidrome_client import NavidromeClient
from services.favorites_service import FavoritesService
from services.library_service import LibraryService


class NavidromeApiEfficiencyTests(unittest.TestCase):
    def setUp(self):
        self.client = NavidromeClient(
            "http://navidrome.example", "user", "password"
        )

    def test_get_albums_fetches_multiple_pages(self):
        first_page = [{"id": f"album-{i}"} for i in range(500)]
        second_page = [{"id": f"album-{i}"} for i in range(500, 620)]
        self.client._request = Mock(side_effect=[
            {"albumList2": {"album": first_page}},
            {"albumList2": {"album": second_page}},
        ])

        albums = self.client.get_albums(size=620)

        self.assertEqual(len(albums), 620)
        self.assertEqual(
            [call.args[1]["offset"] for call in self.client._request.call_args_list],
            ["0", "500"],
        )
        self.assertEqual(
            [call.args[1]["size"] for call in self.client._request.call_args_list],
            ["500", "120"],
        )

    def test_get_albums_fetches_all_pages_when_size_is_omitted(self):
        self.client._request = Mock(side_effect=[
            {"albumList2": {"album": [{"id": f"album-{i}"} for i in range(500)]}},
            {"albumList2": {"album": [{"id": "album-500"}]}},
        ])

        albums = self.client.get_albums()

        self.assertEqual(len(albums), 501)
        self.assertEqual(self.client._request.call_count, 2)

    def test_get_albums_normalizes_single_album_response(self):
        self.client._request = Mock(return_value={
            "albumList2": {"album": {"id": "album-1"}}
        })

        self.assertEqual(
            self.client.get_albums(size=500),
            [{"id": "album-1"}],
        )

    def test_get_albums_raises_when_server_repeats_a_full_page(self):
        repeated_page = [{"id": f"album-{i}"} for i in range(500)]
        self.client._request = Mock(return_value={
            "albumList2": {"album": repeated_page}
        })

        with self.assertRaisesRegex(RuntimeError, "pagination did not advance"):
            self.client.get_albums()

        self.assertEqual(self.client._request.call_count, 2)

    def test_library_service_propagates_album_fetch_failure(self):
        client = Mock()
        client.get_albums.side_effect = RuntimeError("API unavailable")
        service = LibraryService(client)

        with self.assertRaisesRegex(RuntimeError, "API unavailable"):
            service.fetch_albums()

    def test_get_starred_propagates_api_failure(self):
        self.client._request = Mock(side_effect=RuntimeError("API unavailable"))

        with self.assertRaisesRegex(RuntimeError, "API unavailable"):
            self.client.get_starred()

        self.client._request.assert_called_once_with(
            "getStarred", raise_on_error=True
        )

    def test_favorites_service_does_not_cache_api_failure_as_empty(self):
        client = Mock()
        client.server_url = "http://navidrome.example"
        client.username = "user"
        client.get_starred.side_effect = RuntimeError("API unavailable")
        cache = Mock()
        cache.get.return_value = None
        service = FavoritesService(client, cache_manager=cache)
        service._starred_song_ids = {"previously-favorited"}

        service.sync_favorites()

        cache.set.assert_not_called()
        self.assertTrue(service.is_song_favorite("previously-favorited"))
        self.assertFalse(service.is_song_favorite("song-1"))


if __name__ == "__main__":
    unittest.main()
