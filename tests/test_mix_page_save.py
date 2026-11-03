import os
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication
from gui.pages.mix_page import MixPage
from models.song import Song


class MixPageSaveGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.playlist_service = Mock()
        context = SimpleNamespace(
            settings=SimpleNamespace(get=lambda key, default=None: default),
            playlist_service=self.playlist_service,
        )
        self.page = MixPage(context)
        self.page._current_songs = [
            Song(id="song-1", title="Test Track", artist="Test Artist")
        ]
        self.page.btn_save.setEnabled(True)

    def tearDown(self):
        self.page.close()
        self.page.deleteLater()
        self.app.processEvents()

    @patch("gui.pages.mix_page.QMessageBox.information")
    def test_successful_save_disables_button_and_ignores_repeated_clicks(self, _message):
        self.playlist_service.create_mix_playlist.return_value = SimpleNamespace(
            name="Daily Mix"
        )

        self.page._on_save()
        self.assertFalse(self.page.btn_save.isEnabled())

        # Simulate another click/event arriving after the successful save.
        self.page._on_save()
        self.playlist_service.create_mix_playlist.assert_called_once()

    @patch("gui.pages.mix_page.QMessageBox.warning")
    def test_failed_save_reenables_button_for_retry(self, _message):
        self.playlist_service.create_mix_playlist.return_value = None

        self.page._on_save()

        self.assertTrue(self.page.btn_save.isEnabled())
        self.assertFalse(self.page._save_in_progress)
        self.playlist_service.create_mix_playlist.assert_called_once()


if __name__ == "__main__":
    unittest.main()
