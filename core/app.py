"""アプリケーション全体のライフサイクルを管理するモジュール。 (Phase 13.1 対応)"""

import sys
import logging
from PySide6.QtWidgets import QApplication, QMessageBox

from api.navidrome_client import NavidromeClient
from cache.cache_manager import CacheManager
from config.settings import Settings
from core.context import AppContext
from core.logger import setup_logger
from engine.mix_generator import MixGenerator
from services.library_analyzer import LibraryAnalyzer
from gui.main_window import MainWindow
from services.analysis_service import AnalysisService
from services.blacklist_service import BlacklistService
from services.favorites_service import FavoritesService
from services.history_service import HistoryService
from services.library_service import LibraryService
from services.mix_service import MixService
from services.playlist_service import PlaylistService
from services.preset_service import PresetService
from services.scheduler_service import SchedulerService
from services.mix_history_service import MixHistoryService
from services.translation import TranslationManager # 追加
from PySide6.QtGui import QIcon

class Application:
    """アプリケーションの初期化および実行を管理するクラス。"""

    def __init__(self) -> None:
        self._qapp: QApplication = QApplication(sys.argv)

        self._qapp.setWindowIcon(
            QIcon("resources/icons/app.ico")
        )

        self._settings = Settings()
        self._logger = setup_logger()
        self._logger.info("Initializing Navidrome Mix Studio Phase 13.1...")

        # --- Phase 13.1: 翻訳基盤の初期化 (GUIより先に行う) ---
        lang = self._settings.get("language", "ja") # デフォルトを日本語に
        TranslationManager.instance().load_language(lang)

        # 1. 共通基盤（キャッシュ等）の初期化
        cache_enabled = self._settings.get("cache.enabled", True)
        expire_hours = self._settings.get("cache.expire_hours", 24)
        self._cache_manager = (
            CacheManager(expire_hours=expire_hours, logger=self._logger)
            if cache_enabled
            else None
        )

        # 2. サーバー接続の初期化
        self._client = self._establish_connection()

        # 3. 基本サービスの初期化
        self._library_service = LibraryService(self._client, self._logger)
        self._playlist_service = PlaylistService(self._client, self._logger)
        self._history_service = HistoryService(self._client, self._logger)
        self._analysis_service = AnalysisService(self._logger)
        self._blacklist_service = BlacklistService(logger=self._logger)
        self._preset_service = PresetService(logger=self._logger)
        self._mix_history_service = MixHistoryService()

        # 4. 分析およびお気に入りサービスの初期化
        self._library_analyzer = LibraryAnalyzer(
            cache_manager=self._cache_manager, 
            logger=self._logger
        )
        self._favorites_service = FavoritesService(
            self._client, self._cache_manager, self._logger
        )

        if self._client.server_url:
            try:
                self._favorites_service.sync_favorites()
            except Exception as e:
                self._logger.warning(f"Initial favorites sync failed: {e}")

        # 5. エンジンとメインサービスの初期化
        self._mix_generator = MixGenerator(
            library_service=self._library_service,
            history_service=self._history_service,
            mix_history_service=self._mix_history_service,
            favorites_service=self._favorites_service,
            blacklist_service=self._blacklist_service,
            preset_service=self._preset_service,
            logger=self._logger,
        )

        self._mix_service = MixService(
            generator=self._mix_generator,
            playlist_service=self._playlist_service,
            library_analyzer=self._library_analyzer,
            preset_service=self._preset_service,
            logger=self._logger,
        )

        self._scheduler_service = SchedulerService(
            mix_service=self._mix_service, logger=self._logger
        )

        # 6. アプリケーションコンテキストの構築
        self._context = AppContext(
            settings=self._settings,
            logger=self._logger,
            client=self._client,
            cache_manager=self._cache_manager,
            library_service=self._library_service,
            playlist_service=self._playlist_service,
            history_service=self._history_service,
            analysis_service=self._analysis_service,
            favorites_service=self._favorites_service,
            blacklist_service=self._blacklist_service,
            preset_service=self._preset_service,
            mix_generator=self._mix_generator,
            mix_service=self._mix_service,
            scheduler_service=self._scheduler_service,
        )

        # 7. メインウィンドウの起動 (この時点で TranslationManager は準備完了している)
        self._main_window = MainWindow(context=self._context)

    def _establish_connection(self) -> NavidromeClient:
        primary_name = self._settings.get("server.primary", "Local")
        secondary_name = self._settings.get("server.secondary", "None")
        profiles = self._settings.get("profiles", [])

        def find_profile(name):
            return next((p for p in profiles if p.get("name") == name), None)

        p_data = find_profile(primary_name)
        if p_data:
            client = NavidromeClient(p_data.get("url"), p_data.get("username"), p_data.get("password"), self._logger)
            if client.test_connection().success: return client

        if secondary_name and secondary_name != "None":
            s_data = find_profile(secondary_name)
            if s_data:
                client = NavidromeClient(s_data.get("url"), s_data.get("username"), s_data.get("password"), self._logger)
                if client.test_connection().success: return client

        return NavidromeClient("", "", "", self._logger)

    def run(self) -> int:
        self._main_window.show()
        result = self._qapp.exec()
        if self._scheduler_service:
            self._scheduler_service.stop()
        return result