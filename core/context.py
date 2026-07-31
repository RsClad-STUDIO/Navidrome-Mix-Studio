"""アプリケーション全体の共有状態と依存関係を保持するコンテキストモジュール。"""

import logging
from typing import Optional

from api.navidrome_client import NavidromeClient
from cache.cache_manager import CacheManager
from config.settings import Settings
from engine.mix_generator import MixGenerator
from services.analysis_service import AnalysisService
from services.blacklist_service import BlacklistService
from services.favorites_service import FavoritesService
from services.history_service import HistoryService
from services.library_service import LibraryService
from services.mix_service import MixService
from services.playlist_service import PlaylistService
from services.preset_service import PresetService
from services.scheduler_service import SchedulerService


class AppContext:
    """アプリケーション全体で共有するリソースを保持するクラス。"""

    def __init__(
        self,
        settings: Settings,
        logger: logging.Logger,
        client: Optional[NavidromeClient] = None,
        cache_manager: Optional[CacheManager] = None,
        library_service: Optional[LibraryService] = None,
        playlist_service: Optional[PlaylistService] = None,
        history_service: Optional[HistoryService] = None,
        analysis_service: Optional[AnalysisService] = None,
        favorites_service: Optional[FavoritesService] = None,
        blacklist_service: Optional[BlacklistService] = None,
        preset_service: Optional[PresetService] = None,
        mix_generator: Optional[MixGenerator] = None,
        mix_service: Optional[MixService] = None,
        scheduler_service: Optional[SchedulerService] = None,
    ) -> None:
        self._settings = settings
        self._logger = logger
        self._client = client
        self._cache_manager = cache_manager
        self._library_service = library_service
        self._playlist_service = playlist_service
        self._history_service = history_service
        self._analysis_service = analysis_service
        self._favorites_service = favorites_service
        self._blacklist_service = blacklist_service
        self._preset_service = preset_service
        self._mix_generator = mix_generator
        self._mix_service = mix_service
        self._scheduler_service = scheduler_service

    @property
    def settings(self) -> Settings:
        return self._settings

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @property
    def client(self) -> Optional[NavidromeClient]:
        return self._client

    @property
    def library_service(self) -> Optional[LibraryService]:
        return self._library_service

    @property
    def playlist_service(self) -> Optional[PlaylistService]:
        return self._playlist_service

    @property
    def history_service(self) -> Optional[HistoryService]:
        return self._history_service

    @property
    def analysis_service(self) -> Optional[AnalysisService]:
        return self._analysis_service

    @property
    def favorites_service(self) -> Optional[FavoritesService]:
        return self._favorites_service

    @property
    def blacklist_service(self) -> Optional[BlacklistService]:
        return self._blacklist_service

    @property
    def preset_service(self) -> Optional[PresetService]:
        return self._preset_service

    @property
    def mix_generator(self) -> Optional[MixGenerator]:
        return self._mix_generator

    @property
    def mix_service(self) -> Optional[MixService]:
        return self._mix_service

    @property
    def scheduler_service(self) -> Optional[SchedulerService]:
        return self._scheduler_service