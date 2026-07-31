"""
アプリケーションのメインウィンドウ。
Phase 13.4: プレイリスト管理、Aboutダイアログ、および全言語切替の統合。
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from utils.path_utils import get_resource_path
from PySide6.QtWidgets import (
    QHBoxLayout, QMainWindow, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget, QLabel, QMessageBox
)
from pathlib import Path
from PySide6.QtGui import QIcon

from core.context import AppContext
from gui.pages.mix_page import MixPage
from gui.pages.statistics.statistics_page import StatisticsPage
from gui.pages.playlist_manager_page import PlaylistManagerPage
from gui.pages.blacklist_page import BlacklistPage
from gui.pages.settings_page import SettingsPage
from gui.dialogs.about_dialog import AboutDialog
from services.translation import tr, TKey, TranslationManager

class MainWindow(QMainWindow):

    def __init__(self, context: AppContext) -> None:
        super().__init__()

        icon_path = get_resource_path(
            "resources/icons/app.ico"
        )

        print("ICON PATH:", icon_path)
        print("ICON EXISTS:", icon_path.exists())

        self.setWindowIcon(
            QIcon(str(icon_path))
        )

        self._context = context

        # 1. UIパーツの構築
        self._init_ui()
        
        # 2. 翻訳マネージャーの信号を購読
        # 設定画面などで言語が変わると、この retranslate_ui が自動で呼ばれます
        TranslationManager.instance().language_changed.connect(self.retranslate_ui)
        
        # 3. 初期テキストの適用
        self.retranslate_ui()
        
        self.resize(1100, 750)

        print("WINDOW ICON NULL:", self.windowIcon().isNull())

    def _init_ui(self) -> None:
        """UIコンポーネントの配置定義"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- サイドバーエリア ---
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            border-right: 1px solid palette(mid);
            background-color: palette(window);
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 10)
        sidebar_layout.setSpacing(5)

        # ナビゲーションボタン生成 (Index: 0=Mix, 1=Stats, 2=Playlist, 3=Blacklist, 4=Settings)
        self.btn_mix = self._create_nav_btn(0)
        self.btn_stats = self._create_nav_btn(1)
        self.btn_playlists = self._create_nav_btn(2)
        self.btn_blacklist = self._create_nav_btn(3)
        self.btn_settings = self._create_nav_btn(4)

        sidebar_layout.addWidget(self.btn_mix)
        sidebar_layout.addWidget(self.btn_stats)
        sidebar_layout.addWidget(self.btn_playlists)
        sidebar_layout.addWidget(self.btn_blacklist)
        sidebar_layout.addWidget(self.btn_settings)

        sidebar_layout.addStretch()

        # Aboutボタン (ダイアログ表示用)
        self.btn_about = QPushButton()
        self.btn_about.setFlat(True)
        self.btn_about.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_about.clicked.connect(self._on_about_clicked)
        sidebar_layout.addWidget(self.btn_about)

        # サーバー接続ステータス表示
        sidebar_layout.addSpacing(10)
        self.lbl_conn_status = QLabel()
        self.lbl_conn_status.setStyleSheet("font-weight: bold;")
        sidebar_layout.addWidget(self.lbl_conn_status)

        self.lbl_server_info = QLabel()
        sidebar_layout.addWidget(self.lbl_server_info)

        main_layout.addWidget(sidebar)

        # --- ページスタックエリア (QStackedWidget) ---
        self.stacked_widget = QStackedWidget()
        
        # 各ページのインスタンス化
        self.mix_page = MixPage(self._context)
        self.stats_page = StatisticsPage(self._context)
        self.playlists_page = PlaylistManagerPage(self._context)
        self.blacklist_page = BlacklistPage(self._context)
        self.settings_page = SettingsPage(self._context)

        # スタックに追加 (Indexをナビゲーションボタンと一致させる)
        self.stacked_widget.addWidget(self.mix_page)      # Index 0
        self.stacked_widget.addWidget(self.stats_page)    # Index 1
        self.stacked_widget.addWidget(self.playlists_page)# Index 2
        self.stacked_widget.addWidget(self.blacklist_page)# Index 3
        self.stacked_widget.addWidget(self.settings_page) # Index 4

        main_layout.addWidget(self.stacked_widget)

    def _create_nav_btn(self, index: int) -> QPushButton:
        """ナビゲーションボタンを共通スタイルで生成。"""
        btn = QPushButton()
        btn.setCheckable(True)
        btn.setFixedHeight(40)
        btn.setStyleSheet("text-align: left; padding-left: 15px;")
        # ボタンクリックで QStackedWidget のページを切り替え
        btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(index))
        return btn

    def _on_about_clicked(self) -> None:
        """Aboutダイアログ（ポップアップ）を表示。"""
        dialog = AboutDialog(self)
        dialog.exec()

    def retranslate_ui(self) -> None:
        """
        全UIテキストの翻訳更新。
        言語変更イベント発生時、または初期化時に呼び出されます。
        """
        # メインウィンドウタイトル
        self.setWindowTitle(tr(TKey.MAIN_APP_TITLE))
        
        # サイドバーボタンのテキスト
        self.btn_mix.setText(tr(TKey.MAIN_SIDEBAR_MIX))
        self.btn_stats.setText(tr(TKey.MAIN_SIDEBAR_STATS))
        self.btn_playlists.setText(tr(TKey.MAIN_SIDEBAR_PLAYLISTS))
        self.btn_blacklist.setText(tr(TKey.MAIN_SIDEBAR_BLACKLIST))
        self.btn_settings.setText(tr(TKey.MAIN_SIDEBAR_SETTINGS))
        self.btn_about.setText(tr(TKey.MAIN_SIDEBAR_ABOUT))
        
        # ステータス関連
        self.lbl_conn_status.setText(tr(TKey.MAIN_SIDEBAR_STATUS))

        # 現在の接続URLに基づき、表示を更新
        current_url = self._context.client.server_url
        if current_url:
            # 表示用にURLからホスト名のみを抽出（簡易的）
            display_url = current_url.replace("http://", "").replace("https://", "").split(":")[0]
            status_text = tr(TKey.MAIN_SIDEBAR_CONNECTED)
            self.lbl_server_info.setText(f"{status_text}\n({display_url})")
            self.lbl_server_info.setStyleSheet("color: green; margin-bottom: 10px;")
        else:
            self.lbl_server_info.setText(tr(TKey.MAIN_SIDEBAR_DISCONNECTED))
            self.lbl_server_info.setStyleSheet("color: red; margin-bottom: 10px;")

    def showEvent(self, event):
        """ウィンドウが初めて表示される際に実行されるイベント。"""
        super().showEvent(event)
        # もし一度も接続に成功していない場合は、警告を出して設定画面へ誘導する
        if not self._context.client.server_url:
            QMessageBox.critical(
                self,
                tr(TKey.ERROR_CONNECTION_TITLE),
                tr(TKey.ERROR_CONNECTION_MSG),
                QMessageBox.StandardButton.Ok
            )
            self.stacked_widget.setCurrentIndex(4) # Settingsページを表示