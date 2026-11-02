"""指定されたスケジュールに従ってバックグラウンドでMix生成を自動実行するサービス。"""

import logging
import threading
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QThread, Signal
from services.mix_service import MixService


class SchedulerWorker(QThread):
    """バックグラウンドで時刻監視およびMix生成を行うワークスレッド。"""

    mix_generated_signal = Signal(str, int)
    error_signal = Signal(str)

    def __init__(
        self,
        mix_service: MixService,
        mode: str = "daily",
        target_time: str = "07:00",
        interval_hours: int = 6,
        default_mix_type: str = "Favorites Mix",
        default_count: int = 50,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__()
        self._mix_service = mix_service
        self._mode = mode
        self._target_time = target_time
        self._interval_hours = max(1, int(interval_hours))
        self._default_mix_type = default_mix_type
        self._default_count = max(1, int(default_count))
        self._logger = logger or logging.getLogger(__name__)
        self._stop_event = threading.Event()
        self._last_executed_day: Optional[str] = None

    def stop(self) -> None:
        """待機中のスレッドを速やかに停止します。"""
        self._stop_event.set()

    def run(self) -> None:
        """スケジュールチェックループを実行します。"""
        self._logger.info("Scheduler thread started (mode=%s).", self._mode)

        if self._mode == "startup":
            self._execute_mix()
            self._logger.info("Scheduler thread stopped.")
            return

        while not self._stop_event.is_set():
            if self._mode == "daily":
                now = datetime.now()
                today = now.strftime("%Y-%m-%d")
                if (
                    now.strftime("%H:%M") == self._target_time
                    and self._last_executed_day != today
                ):
                    self._execute_mix()
                    self._last_executed_day = today

                if self._stop_event.wait(5):
                    break

            elif self._mode == "interval":
                if self._stop_event.wait(self._interval_hours * 3600):
                    break
                self._execute_mix()

            else:
                self._logger.error("Unsupported scheduler mode: %s", self._mode)
                break

        self._logger.info("Scheduler thread stopped.")

    def _execute_mix(self) -> None:
        """Mixを自動生成してNavidromeプレイリストへ同期保存します。"""
        try:
            self._logger.info(
                "Auto-generating Mix: %s (limit=%s)",
                self._default_mix_type,
                self._default_count,
            )
            songs = self._mix_service.generate_by_preset(
                preset_name=self._default_mix_type,
                limit=self._default_count,
            )
            if not songs:
                self._logger.warning("Auto Mix generated no songs; playlist was not changed.")
                return

            playlist = self._mix_service.save_to_navidrome(
                mix_name=self._default_mix_type,
                songs=songs,
            )
            if playlist:
                self._logger.info(
                    "Auto Mix successfully saved to playlist: %s", playlist.name
                )
                self.mix_generated_signal.emit(self._default_mix_type, len(songs))
            else:
                message = "Navidrome playlist save failed."
                self._logger.error(message)
                self.error_signal.emit(message)
        except Exception as exc:
            self._logger.exception("Error during auto mix generation.")
            self.error_signal.emit(str(exc))


class SchedulerService:
    """自動Mix生成スケジューラーの管理を行うサービス。"""

    SUPPORTED_MODES = {"daily", "interval", "startup"}
    SUPPORTED_PRESETS = {
        "Daily Mix",
        "Favorites Mix",
        "Discovery Mix",
        "Forgotten Favorites",
    }
    PRESET_ALIASES = {
        "Recent": "Favorites Mix",
        "Favorite": "Favorites Mix",
        "Favorites": "Favorites Mix",
        "Daily": "Daily Mix",
        "Discovery": "Discovery Mix",
        "Forgotten": "Forgotten Favorites",
    }

    def __init__(
        self, mix_service: MixService, logger: Optional[logging.Logger] = None
    ) -> None:
        self._mix_service = mix_service
        self._logger = logger or logging.getLogger(__name__)
        self._worker: Optional[SchedulerWorker] = None

    def start(
        self,
        mode: str = "daily",
        target_time: str = "07:00",
        interval_hours: int = 6,
        default_mix_type: str = "Favorites Mix",
        default_count: int = 50,
    ) -> None:
        """設定に従ってスケジューラーを起動します。"""
        if mode not in self.SUPPORTED_MODES:
            raise ValueError("Unsupported scheduler mode: %s" % mode)

        self.stop()

        preset_name = self.PRESET_ALIASES.get(default_mix_type, default_mix_type)
        if preset_name not in self.SUPPORTED_PRESETS:
            self._logger.warning(
                "Unsupported mix preset '%s'; using Favorites Mix.", default_mix_type
            )
            preset_name = "Favorites Mix"

        worker = SchedulerWorker(
            mix_service=self._mix_service,
            mode=mode,
            target_time=target_time,
            interval_hours=interval_hours,
            default_mix_type=preset_name,
            default_count=default_count,
            logger=self._logger,
        )
        self._worker = worker
        worker.start()

    def stop(self) -> None:
        """スケジューラーを停止し、ワーカースレッドの終了を待ちます。"""
        worker = self._worker
        if worker is None:
            return

        if worker.isRunning():
            worker.stop()
            worker.wait()

        self._worker = None
        self._logger.info("Scheduler service stopped.")
