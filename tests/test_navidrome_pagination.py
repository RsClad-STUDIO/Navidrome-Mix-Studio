import unittest
from unittest.mock import Mock

from api.navidrome_client import NavidromeClient


class NavidromePaginationTests(unittest.TestCase):
    def setUp(self):
        self.client = NavidromeClient(
            server_url="http://navidrome.example",
            username="test",
            password="test",
        )
        self.client._request = Mock()

    @staticmethod
    def make_page(start, count):
        return [
            {"id": str(index), "title": f"Song {index}"}
            for index in range(start, start + count)
        ]

    def test_fetches_all_pages_until_empty_page(self):
        self.client._request.side_effect = [
            {"searchResult3": {"song": self.make_page(0, 500)}},
            {"searchResult3": {"song": self.make_page(500, 500)}},
            {"searchResult3": {"song": []}},
        ]

        songs = self.client.search_songs()

        self.assertEqual(len(songs), 1000)
        self.assertEqual(
            [
                call.args[1]["songOffset"]
                for call in self.client._request.call_args_list
            ],
            ["0", "500", "1000"],
        )
        self.assertTrue(
            all(call.kwargs["raise_on_error"] for call in self.client._request.call_args_list)
        )

    def test_count_limits_total_results_across_pages(self):
        self.client._request.side_effect = [
            {"searchResult3": {"song": self.make_page(0, 500)}},
            {"searchResult3": {"song": self.make_page(500, 100)}},
        ]

        songs = self.client.search_songs(count=600)

        self.assertEqual(len(songs), 600)
        self.assertEqual(self.client._request.call_count, 2)
        second_params = self.client._request.call_args_list[1].args[1]
        self.assertEqual(second_params["songOffset"], "500")
        self.assertEqual(second_params["songCount"], "100")

    def test_stops_if_server_ignores_offset(self):
        page = self.make_page(0, 500)
        self.client._request.side_effect = [
            {"searchResult3": {"song": page}},
            {"searchResult3": {"song": page}},
        ]

        with self.assertRaisesRegex(RuntimeError, "pagination did not advance"):
            self.client.search_songs()

    def test_empty_library_returns_empty_list(self):
        self.client._request.return_value = {"searchResult3": {"song": []}}

        self.assertEqual(self.client.search_songs(), [])


if __name__ == "__main__":
    unittest.main()
