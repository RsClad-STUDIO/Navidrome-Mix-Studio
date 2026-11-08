import unittest
from unittest.mock import Mock

from api.navidrome_client import NavidromeClient


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

    def test_get_albums_normalizes_single_album_response(self):
        self.client._request = Mock(return_value={
            "albumList2": {"album": {"id": "album-1"}}
        })

        self.assertEqual(
            self.client.get_albums(size=500),
            [{"id": "album-1"}],
        )

    def test_get_starred_propagates_api_failure(self):
        self.client._request = Mock(side_effect=RuntimeError("API unavailable"))

        with self.assertRaisesRegex(RuntimeError, "API unavailable"):
            self.client.get_starred()

        self.client._request.assert_called_once_with(
            "getStarred", raise_on_error=True
        )


if __name__ == "__main__":
    unittest.main()
