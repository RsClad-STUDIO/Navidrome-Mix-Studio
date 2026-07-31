"""指定されたスケジュールに従ってバックグラウンドでMix生成を自動実行するサービス。"""

import logging
import time
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QThread, Signal
from engine.rules import DiscoveryRule, EraRule, PopularRule, RecentRule
from services.mix_service import MixService


class SchedulerWorker(QThread):
    """バックグラウンドで時刻監視およびMix生成を行うワークスレッド。"""

    mix_generated_signal = Signal(str, int)  # mix_type, count
    error_signal = Signal(str)

    def __init__(
        self,
        mix_service: MixService,
        mode: str = "daily",
        target_time: str = "07:00",
        interval_hours: int = 6,
        default_mix_type: str = "Recent",
        default_count: int = 50,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__()
        self._mix_service = mix_service
        self._mode = mode
        self._target_time = target_time
        self._interval_hours = interval_hours
        self._default_mix_type = default_mix_type
        self._default_count = default_count
        self._logger = logger or logging.getLogger(__name__)
        self._running = True
        self._last_executed_day: Optional[str] = None

    def stop(self) -> None:
        """スレッドの停止フラグを立てます。"""
        self._running = False

    def run(self) -> None:
        """スケジュールチェックループを実行します。"""
        self._logger.info(f"Scheduler thread started (mode={self._mode}).")

        # 起動時実行モードの場合は即座に1度実行
        if self._mode == "startup":
            self._execute_mix()

        while self._running:
            now = datetime.now()
            today_str = now.strftime("%Y-%m-%d")
            current_time_str = now.strftime("%H:%M")

            if self._mode == "daily":
                if (
                    current_time_str == self._target_time
                    and self._last_executed_day != today_str
                ):
                    self._execute_mix()
                    self._last_executed_day = today_str
            elif self._mode == "interval":
                # 簡略化のため一定間隔でスリープ後に実行
                for _ in range(self._interval_hours * 3600):
                    if not self._running:
                        break
                    time.sleep(1)
                if self._running:
                    self._execute_mix()

            # 10秒ごとに条件判定
            time.sleep(10)

        self._logger.info("Scheduler thread stopped.")

    def _execute_mix(self) -> None:
        """Mixを自動生成してNavidromeプレイリストへ同期保存します。"""
        try:
            self._logger.info(
                f"Auto-generating Mix: {self._default_mix_type} (limit={self._default_count})"
            )
            songs = self._mix_service.generate_mix(
                mix_type=self._default_mix_type, limit=self._default_count
            )
            if songs:
                pl = self._mix_service.save_to_navidrome(
                    mix_name=self._default_mix_type, songs=songs
                )
                if pl:
                    self._logger.info(
                        f"Auto Mix successfully saved to playlist: {pl.name}"
                    )
                    self.mix_generated_signal.emit(
                        self._default_mix_type, len(songs)
                    )
        except Exception as e:
            self._logger.error(f"Error during auto mix generation: {e}")
            self.error_signal.emit(str(e))


class SchedulerService:
    """自動Mix生成スケジューラーの管理を行うサービス。"""

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
        default_mix_type: str = "Recent",
        default_count: int = 50,
    ) -> None:
        """スケジューラーを起動します。既に稼働している場合は停止して再起動します。"""
        self.stop()
        self._worker = SchedulerWorker(
            mix_service=self._mix_service,
            mode=mode,
            target_time=target_time,
            interval_hours=interval_hours,
            default_mix_type=default_mix_type,
            default_count=default_count,
            logger=self._logger,
        )
        self._worker.start()

    def stop(self) -> None:
        """スケジューラーを停止します。"""
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(3000)
            self._worker = None
            self._logger.info("Scheduler service stopped.")