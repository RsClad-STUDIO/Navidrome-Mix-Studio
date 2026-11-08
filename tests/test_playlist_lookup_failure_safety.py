import unittest
from unittest.mock import Mock

from api.navidrome_client import NavidromeClient
from models.song import Song
from services.playlist_service import PlaylistService


class PlaylistLookupFailureSafetyTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        self.service = PlaylistService(self.client)
        self.songs = [Song(id="song-1", title="One", artist="Artist")]

    def test_client_get_playlists_requests_strict_error_handling(self):
        client = NavidromeClient("http://example.test", "user", "pass")
        client._request = Mock(side_effect=RuntimeError("API unavailable"))

        with self.assertRaisesRegex(RuntimeError, "API unavailable"):
            client.get_playlists()

        client._request.assert_called_once_with("getPlaylists", raise_on_error=True)

    def test_auto_overwrite_aborts_when_playlist_lookup_fails(self):
        self.client.get_playlists.side_effect = RuntimeError("API unavailable")
        self.client.create_playlist = Mock()

        with self.assertRaisesRegex(RuntimeError, "API unavailable"):
            self.service.create_mix_playlist("Daily Mix", self.songs, auto_overwrite=True)

        self.client.create_playlist.assert_not_called()
        self.client.update_playlist.assert_not_called()

    def test_regular_fetch_keeps_legacy_empty_list_behavior_on_failure(self):
        self.client.get_playlists.side_effect = RuntimeError("API unavailable")

        self.assertEqual(self.service.fetch_playlists(), [])

    def test_successful_empty_lookup_creates_playlist(self):
        self.client.get_playlists.return_value = []
        created = {"id": "playlist-1", "name": "Daily Mix"}
        self.client.create_playlist.return_value = created

        result = self.service.create_mix_playlist(
            "Daily Mix", self.songs, auto_overwrite=True
        )

        self.assertEqual(result.id, "playlist-1")
        self.client.create_playlist.assert_called_once_with(
            "Daily Mix", ["song-1"]
        )

    def test_matching_playlist_is_updated_without_creating_duplicate(self):
        self.client.get_playlists.return_value = [
            {"id": "playlist-1", "name": "Daily Mix"}
        ]
        self.client.update_playlist.return_value = {
            "id": "playlist-1", "name": "Daily Mix"
        }
        self.client.create_playlist = Mock()

        result = self.service.create_mix_playlist(
            "Daily Mix", self.songs, auto_overwrite=True
        )

        self.assertEqual(result.id, "playlist-1")
        self.client.update_playlist.assert_called_once_with(
            playlist_id="playlist-1",
            name="Daily Mix",
            song_ids=["song-1"],
        )
        self.client.create_playlist.assert_not_called()

    def test_failed_existing_playlist_update_does_not_create_duplicate(self):
        self.client.get_playlists.return_value = [
            {"id": "playlist-1", "name": "Daily Mix"}
        ]
        self.client.update_playlist.return_value = None
        self.client.create_playlist = Mock()

        result = self.service.create_mix_playlist(
            "Daily Mix", self.songs, auto_overwrite=True
        )

        self.assertIsNone(result)
        self.client.update_playlist.assert_called_once_with(
            playlist_id="playlist-1",
            name="Daily Mix",
            song_ids=["song-1"],
        )
        self.client.create_playlist.assert_not_called()


if __name__ == "__main__":
    unittest.main()
