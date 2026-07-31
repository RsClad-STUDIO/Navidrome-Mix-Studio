"""Phase 13.3: Playlist Manager - Optimized for Name visibility and simplified Info."""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLineEdit, QPushButton, 
    QLabel, QSplitter, QMessageBox, QSpinBox, QSizePolicy
)
from PySide6.QtCore import Qt
from services.translation import tr, TKey, TranslationManager
from models.playlist import Playlist
from models.song import Song

if TYPE_CHECKING:
    from core.context import AppContext

class PlaylistManagerPage(QWidget):
    def __init__(self, context: "AppContext") -> None:
        super().__init__()
        self._context = context
        self._all_playlists: List[Playlist] = []
        self._current_songs: List[Song] = []
        
        self._init_ui()
        TranslationManager.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()
        self.refresh_playlists()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # 1. Top Bar
        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self._on_search_changed)
        self.btn_refresh = QPushButton()
        self.btn_refresh.setFixedWidth(100)
        self.btn_refresh.clicked.connect(self.refresh_playlists)
        top_layout.addWidget(self.search_input, 1)
        top_layout.addWidget(self.btn_refresh)
        layout.addLayout(top_layout)

        # 2. Splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Left Container (Playlist List)
        left_container = QWidget(); left_lyt = QVBoxLayout(left_container); left_lyt.setContentsMargins(0, 0, 0, 0)
        self.table_playlists = QTableWidget(0, 3) # 列数を3に削減
        self.table_playlists.verticalHeader().setVisible(False)
        self.table_playlists.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_playlists.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_playlists.itemSelectionChanged.connect(self._on_playlist_selected)
        
        # 名前列を自動で広げる設定
        self.table_playlists.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_playlists.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_playlists.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        left_lyt.addWidget(self.table_playlists)
        splitter.addWidget(left_container)

        # Right Container (Details)
        right_container = QWidget(); right_lyt = QVBoxLayout(right_container); right_lyt.setContentsMargins(0, 0, 0, 0)
        
        self.group_info = QGroupBox()
        info_lyt = QVBoxLayout(self.group_info); info_lyt.setSpacing(5)
        self.lbl_info_name = QLabel()
        self.lbl_info_name.setWordWrap(True) # 長い名前の折り返し
        self.lbl_info_count = QLabel()
        # 更新日時ラベルを削除
        info_lyt.addWidget(self.lbl_info_name)
        info_lyt.addWidget(self.lbl_info_count)
        right_lyt.addWidget(self.group_info)

        self.group_songs = QGroupBox()
        song_lyt = QVBoxLayout(self.group_songs)
        self.table_songs = QTableWidget(0, 4); self.table_songs.verticalHeader().setVisible(False)
        self.table_songs.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        song_lyt.addWidget(self.table_songs)
        right_lyt.addWidget(self.group_songs)

        self.btn_delete = QPushButton()
        self.btn_delete.setStyleSheet("color: #cc0000; font-weight: bold; height: 28px;")
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        right_lyt.addWidget(self.btn_delete)

        splitter.addWidget(right_container)
        splitter.setStretchFactor(0, 3); splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        # 3. Cleanup Section
        self.group_cleanup = QGroupBox()
        self.group_cleanup.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.group_cleanup.setMinimumHeight(75) 
        
        cleanup_lyt = QHBoxLayout(self.group_cleanup)
        cleanup_lyt.setContentsMargins(15, 8, 15, 8) 
        cleanup_lyt.setSpacing(8)
        
        self.lbl_cleanup_pre = QLabel()
        self.spin_cleanup_days = QSpinBox()
        self.spin_cleanup_days.setRange(1, 365); self.spin_cleanup_days.setValue(30); self.spin_cleanup_days.setFixedWidth(80)
        self.lbl_cleanup_suf = QLabel()
        self.btn_cleanup = QPushButton()
        self.btn_cleanup.setFixedWidth(130); self.btn_cleanup.clicked.connect(self._on_cleanup_clicked)
        
        cleanup_lyt.addWidget(self.lbl_cleanup_pre)
        cleanup_lyt.addWidget(self.spin_cleanup_days)
        cleanup_lyt.addWidget(self.lbl_cleanup_suf)
        cleanup_lyt.addStretch()
        cleanup_lyt.addWidget(self.btn_cleanup)
        layout.addWidget(self.group_cleanup)

    def retranslate_ui(self) -> None:
        self.search_input.setPlaceholderText(tr(TKey.PLAYLIST_MGR_SEARCH_PLACEHOLDER))
        self.btn_refresh.setText(tr(TKey.PLAYLIST_MGR_BTN_REFRESH))
        
        # ヘッダーを3列に更新
        self.table_playlists.setHorizontalHeaderLabels([
            tr(TKey.PLAYLIST_MGR_COL_NAME), tr(TKey.PLAYLIST_MGR_COL_TYPE),
            tr(TKey.PLAYLIST_MGR_COL_COUNT)
        ])
        
        self.group_info.setTitle(tr(TKey.PLAYLIST_MGR_GROUP_INFO))
        self.group_songs.setTitle(tr(TKey.PLAYLIST_MGR_GROUP_SONGS))
        self.table_songs.setHorizontalHeaderLabels([
            tr(TKey.TABLE_HEADER_TITLE), tr(TKey.TABLE_HEADER_ARTIST),
            tr(TKey.TABLE_HEADER_ALBUM), tr(TKey.TABLE_HEADER_DURATION)
        ])
        self.btn_delete.setText(tr(TKey.PLAYLIST_MGR_BTN_DELETE))
        self.group_cleanup.setTitle(tr(TKey.PLAYLIST_MGR_GROUP_CLEANUP))
        self.lbl_cleanup_pre.setText(tr(TKey.PLAYLIST_MGR_LABEL_CLEANUP_PREFIX))
        self.lbl_cleanup_suf.setText(tr(TKey.PLAYLIST_MGR_LABEL_CLEANUP_SUFFIX))
        self.btn_cleanup.setText(tr(TKey.PLAYLIST_MGR_BTN_CLEANUP))
        
        self._update_info_display()

    def refresh_playlists(self) -> None:
        self.setCursor(Qt.CursorShape.WaitCursor)
        try:
            self._all_playlists = self._context.playlist_service.fetch_playlists()
            self._apply_filter()
        finally: self.unsetCursor()

    def _apply_filter(self) -> None:
        query = self.search_input.text().lower()
        filtered = [p for p in self._all_playlists if query in p.name.lower()]
        self.table_playlists.setRowCount(len(filtered))
        for i, p in enumerate(filtered):
            # 1. 名前
            self.table_playlists.setItem(i, 0, QTableWidgetItem(p.name))
            # 2. 種類
            is_gen = " • " in p.name or "[Mix]" in p.name
            self.table_playlists.setItem(i, 1, QTableWidgetItem(tr(TKey.PLAYLIST_TYPE_GENERATED if is_gen else TKey.PLAYLIST_TYPE_MANUAL)))
            # 3. 曲数
            self.table_playlists.setItem(i, 2, QTableWidgetItem(str(getattr(p, "song_count", 0))))
            
            # ID保持
            self.table_playlists.item(i, 0).setData(Qt.ItemDataRole.UserRole, p)

    def _on_search_changed(self) -> None: self._apply_filter()

    def _on_playlist_selected(self) -> None:
        selected = self.table_playlists.selectedItems()
        if not selected: self._clear_details(); return
        playlist: Playlist = selected[0].data(Qt.ItemDataRole.UserRole)
        self._update_info_display(playlist)
        self.setCursor(Qt.CursorShape.WaitCursor)
        self._current_songs = self._context.playlist_service.get_playlist_songs(playlist.id)
        self._update_songs_table(); self.unsetCursor()

    def _update_info_display(self, playlist: Optional[Playlist] = None) -> None:
        if not playlist:
            self.lbl_info_name.setText(tr(TKey.PLAYLIST_MGR_LABEL_NAME))
            self.lbl_info_count.setText(tr(TKey.PLAYLIST_MGR_LABEL_COUNT)); return
            
        self.lbl_info_name.setText(f"{tr(TKey.PLAYLIST_MGR_LABEL_NAME)} {playlist.name}")
        self.lbl_info_count.setText(f"{tr(TKey.PLAYLIST_MGR_LABEL_COUNT)} {getattr(playlist, 'song_count', 0)}")

    def _update_songs_table(self) -> None:
        self.table_songs.setRowCount(len(self._current_songs))
        for i, s in enumerate(self._current_songs):
            self.table_songs.setItem(i, 0, QTableWidgetItem(s.title))
            self.table_songs.setItem(i, 1, QTableWidgetItem(s.artist))
            self.table_songs.setItem(i, 2, QTableWidgetItem(s.album or "-"))
            self.table_songs.setItem(i, 3, QTableWidgetItem(f"{s.duration // 60}:{s.duration % 60:02d}"))

    def _clear_details(self) -> None:
        self._update_info_display(None); self.table_songs.setRowCount(0); self._current_songs = []

    def _on_delete_clicked(self) -> None:
        selected = self.table_playlists.selectedItems()
        if not selected: return
        playlist: Playlist = selected[0].data(Qt.ItemDataRole.UserRole)
        if QMessageBox.question(self, tr(TKey.DIALOG_DELETE_PLAYLIST_TITLE), tr(TKey.DIALOG_DELETE_PLAYLIST_MSG, name=playlist.name), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            if self._context.playlist_service.delete_playlist(playlist.id):
                self.refresh_playlists(); self._clear_details()

    def _on_cleanup_clicked(self) -> None:
        cutoff = datetime.now() - timedelta(days=self.spin_cleanup_days.value())
        targets = []
        for p in self._all_playlists:
            if " • " not in p.name and "[Mix]" not in p.name: continue
            raw_date = getattr(p, "changed", getattr(p, "created", ""))
            try:
                if datetime.fromisoformat(raw_date.replace("Z", "+00:00")).timestamp() < cutoff.timestamp(): targets.append(p)
            except: continue
        if not targets:
            QMessageBox.information(self, tr(TKey.PLAYLIST_MGR_GROUP_CLEANUP), "No old generated playlists found."); return
        if QMessageBox.question(self, tr(TKey.DIALOG_CLEANUP_TITLE), tr(TKey.DIALOG_CLEANUP_MSG, count=len(targets), days=self.spin_cleanup_days.value()), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.setCursor(Qt.CursorShape.WaitCursor)
            for p in targets: self._context.playlist_service.delete_playlist(p.id)
            self.refresh_playlists(); self._clear_details(); self.unsetCursor()