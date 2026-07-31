"""Phase 13.2: LibraryTab - Polished & Hardcode-Free."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QGridLayout, QLabel, QTableWidgetItem
from .components import StatCard, ValueLabel, create_standard_table
from services.translation import tr, TKey

class LibraryTab(QWidget):
    def __init__(self, context):
        super().__init__()
        self._context = context
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.btn_refresh = QPushButton()
        self.btn_refresh.setFixedWidth(200)
        self.btn_refresh.clicked.connect(self.refresh_data)
        self.layout.addWidget(self.btn_refresh)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.container_layout = QVBoxLayout(container)

        self.card_overview = StatCard(TKey.STATS_LIB_OVERVIEW_TITLE)
        grid = QGridLayout()
        self.lbl_songs_tag = QLabel(); self.lbl_songs_val = ValueLabel()
        self.lbl_albums_tag = QLabel(); self.lbl_albums_val = ValueLabel()
        self.lbl_artists_tag = QLabel(); self.lbl_artists_val = ValueLabel()
        grid.addWidget(self.lbl_songs_tag, 0, 0); grid.addWidget(self.lbl_songs_val, 0, 1, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.lbl_albums_tag, 1, 0); grid.addWidget(self.lbl_albums_val, 1, 1, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.lbl_artists_tag, 2, 0); grid.addWidget(self.lbl_artists_val, 2, 1, Qt.AlignmentFlag.AlignRight)
        self.card_overview.layout.addLayout(grid)
        self.container_layout.addWidget(self.card_overview)

        self.card_metrics = StatCard(TKey.STATS_LIB_OVERVIEW_TITLE)
        m_grid = QGridLayout()
        self.lbl_fav_tag = QLabel(); self.lbl_fav_val = ValueLabel()
        self.lbl_year_tag = QLabel(); self.lbl_year_val = ValueLabel()
        self.lbl_ver_tag = QLabel(); self.lbl_ver_val = ValueLabel()
        m_grid.addWidget(self.lbl_fav_tag, 0, 0); m_grid.addWidget(self.lbl_fav_val, 0, 1, Qt.AlignmentFlag.AlignRight)
        m_grid.addWidget(self.lbl_year_tag, 1, 0); m_grid.addWidget(self.lbl_year_val, 1, 1, Qt.AlignmentFlag.AlignRight)
        m_grid.addWidget(self.lbl_ver_tag, 2, 0); m_grid.addWidget(self.lbl_ver_val, 2, 1, Qt.AlignmentFlag.AlignRight)
        self.card_metrics.layout.addLayout(m_grid)
        self.container_layout.addWidget(self.card_metrics)

        self.card_artists = StatCard(TKey.STATS_ARTIST_DIST_TITLE)
        self.table = create_standard_table(2)
        self.table.setMinimumHeight(250)
        self.card_artists.layout.addWidget(self.table)
        self.container_layout.addWidget(self.card_artists)

        self.container_layout.addStretch(); scroll.setWidget(container)
        self.layout.addWidget(scroll)

    def retranslate_ui(self):
        self.btn_refresh.setText(tr(TKey.STATS_BTN_REFRESH_PROFILE))
        self.card_overview.retranslate(); self.card_metrics.retranslate(); self.card_artists.retranslate()
        self.lbl_songs_tag.setText(tr(TKey.STATS_LIB_SONGS))
        self.lbl_albums_tag.setText(tr(TKey.STATS_LIB_ALBUMS))
        self.lbl_artists_tag.setText(tr(TKey.STATS_LIB_ARTISTS))
        self.lbl_fav_tag.setText(tr(TKey.STATS_METRIC_FAV))
        self.lbl_year_tag.setText(tr(TKey.STATS_METRIC_YEAR))
        self.lbl_ver_tag.setText(tr(TKey.STATS_METRIC_VER))
        self.table.setHorizontalHeaderLabels([tr(TKey.TABLE_HEADER_ARTIST), tr(TKey.TABLE_HEADER_SHARE)])

    def refresh_data(self):
        if not self._context.library_service: return
        self.setCursor(Qt.CursorShape.WaitCursor)
        try:
            songs = self._context.library_service.fetch_songs(size=10000)
            profile = self._context.mix_service.analyze_library(songs)
            self.lbl_songs_val.setText(str(profile.total_songs))
            self.lbl_albums_val.setText(str(profile.total_albums))
            self.lbl_artists_val.setText(str(profile.total_artists))
            self.lbl_fav_val.setText(f"{profile.favorite_ratio:.1f} %")
            self.lbl_year_val.setText(f"{profile.year_known_ratio:.1f} %")
            self.lbl_ver_val.setText(f"{profile.version_ratio:.1f} %")
            top = sorted(profile.artist_distribution.items(), key=lambda x: x[1], reverse=True)[:15]
            self.table.setRowCount(len(top))
            for i, (art, ratio) in enumerate(top):
                self.table.setItem(i, 0, QTableWidgetItem(art))
                item = QTableWidgetItem(f"{ratio:.2f} %")
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, 1, item)
        finally: self.unsetCursor()