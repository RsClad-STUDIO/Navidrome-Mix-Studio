"""Phase 13.2: MixPage - Playlist Name Internationalization Implementation."""

from datetime import datetime  # 日時取得用
from typing import List, Optional, TYPE_CHECKING
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSpinBox, QTableView, QVBoxLayout, QWidget,
)

from engine.preset_strategy import (
    DailyStrategy, DiscoveryStrategy, FavoritesStrategy, ForgottenFavoritesStrategy,
)
from gui.models.mix_table_model import MixTableModel
from models.song import Song
from services.translation import tr, TKey, TranslationManager

if TYPE_CHECKING:
    from core.context import AppContext


class MixPage(QWidget):
    """選曲戦略の切り替えとMix生成を行うメイン画面。"""

    STRATEGIES = [
        DailyStrategy(),
        FavoritesStrategy(),
        DiscoveryStrategy(),
        ForgottenFavoritesStrategy(),
    ]

    def __init__(self, context: "AppContext") -> None:
        super().__init__()
        self._context: "AppContext" = context
        self._current_songs: List[Song] = []
        
        self._init_ui()
        TranslationManager.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        # 1. プリセット戦略選択エリア
        self.preset_group = QGroupBox()
        preset_layout = QVBoxLayout(self.preset_group)
        combo_layout = QHBoxLayout()
        self.lbl_strategy = QLabel()
        combo_layout.addWidget(self.lbl_strategy)
        
        self.preset_combo = QComboBox()
        self.preset_combo.setMinimumWidth(180)
        for s in self.STRATEGIES:
            self.preset_combo.addItem("", userData=s.name)
        combo_layout.addWidget(self.preset_combo)

        self.lbl_filter = QLabel()
        combo_layout.addWidget(self.lbl_filter)
        self.search_input = QLineEdit()
        self.search_input.setClearButtonEnabled(True)
        combo_layout.addWidget(self.search_input)

        self.btn_generate = QPushButton()
        self.btn_generate.setStyleSheet("font-weight: bold; padding: 6px 14px;")
        self.btn_generate.clicked.connect(self._on_generate)
        combo_layout.addWidget(self.btn_generate)

        preset_layout.addLayout(combo_layout)
        self.desc_label = QLabel()
        self.desc_label.setStyleSheet("color: #666; font-style: italic; margin-top: 4px;")
        self.desc_label.setWordWrap(True)
        preset_layout.addWidget(self.desc_label)

        self.preset_combo.currentIndexChanged.connect(self._on_strategy_changed)
        main_layout.addWidget(self.preset_group)

        # 2. パラメータ & モード設定
        params_layout = QHBoxLayout()
        self.lbl_limit = QLabel()
        params_layout.addWidget(self.lbl_limit)
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 200)
        self.limit_spin.setValue(25)
        params_layout.addWidget(self.limit_spin)

        self.chk_adaptive = QCheckBox()
        self.chk_adaptive.setChecked(True)
        params_layout.addWidget(self.chk_adaptive)

        self.chk_debug = QCheckBox()
        self.chk_debug.toggled.connect(self._on_debug_toggled)
        params_layout.addWidget(self.chk_debug)

        params_layout.addStretch()
        main_layout.addLayout(params_layout)

        # 3. Version Filter
        self.ver_group = QGroupBox()
        ver_layout = QHBoxLayout(self.ver_group)
        self.chk_inst = QCheckBox()
        self.chk_inst.setChecked(True)
        ver_layout.addWidget(self.chk_inst)
        self.chk_live = QCheckBox()
        ver_layout.addWidget(self.chk_live)
        self.chk_remix = QCheckBox()
        ver_layout.addWidget(self.chk_remix)
        self.chk_demo = QCheckBox()
        ver_layout.addWidget(self.chk_demo)
        self.chk_acoustic = QCheckBox()
        ver_layout.addWidget(self.chk_acoustic)
        main_layout.addWidget(self.ver_group)

        # 4. Table View
        self.table_view = QTableView()
        self.table_model = MixTableModel()
        self.table_view.setModel(self.table_model)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table_view)

        # 5. Navidrome 保存ボタン
        self.btn_save = QPushButton()
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self._on_save)
        main_layout.addWidget(self.btn_save)

    def retranslate_ui(self) -> None:
        self.preset_group.setTitle(tr(TKey.MIX_GROUP_STRATEGY))
        self.lbl_strategy.setText(tr(TKey.MIX_LABEL_STRATEGY))
        self.lbl_filter.setText(tr(TKey.MIX_LABEL_FILTER))
        self.search_input.setPlaceholderText(tr(TKey.MIX_PLACEHOLDER_FILTER))
        self.lbl_limit.setText(tr(TKey.MIX_LABEL_LIMIT))
        self.ver_group.setTitle(tr(TKey.MIX_GROUP_VERSION))
        self.btn_generate.setText(tr(TKey.MIX_BUTTON_GENERATE))
        self.btn_save.setText(tr(TKey.MIX_BUTTON_SAVE))
        self.chk_adaptive.setText(tr(TKey.MIX_CHECKBOX_ADAPTIVE))
        self.chk_debug.setText(tr(TKey.MIX_CHECKBOX_DEBUG))
        self.chk_inst.setText(tr(TKey.MIX_CHECKBOX_INST))
        self.chk_live.setText(tr(TKey.MIX_CHECKBOX_LIVE))
        self.chk_remix.setText(tr(TKey.MIX_CHECKBOX_REMIX))
        self.chk_demo.setText(tr(TKey.MIX_CHECKBOX_DEMO))
        self.chk_acoustic.setText(tr(TKey.MIX_CHECKBOX_ACOUSTIC))

        strategy_keys = {
            "Daily Mix": TKey.STRATEGY_DAILY_NAME,
            "Favorites Mix": TKey.STRATEGY_FAVORITES_NAME,
            "Discovery Mix": TKey.STRATEGY_DISCOVERY_NAME,
            "Forgotten Favorites": TKey.STRATEGY_FORGOTTEN_NAME,
        }
        for i in range(self.preset_combo.count()):
            internal_id = self.preset_combo.itemData(i)
            if internal_id in strategy_keys:
                self.preset_combo.setItemText(i, tr(strategy_keys[internal_id]))

        self._on_strategy_changed()

    def _on_strategy_changed(self) -> None:
        internal_id = self.preset_combo.currentData()
        desc_keys = {
            "Daily Mix": TKey.STRATEGY_DAILY_DESC,
            "Favorites Mix": TKey.STRATEGY_FAVORITES_DESC,
            "Discovery Mix": TKey.STRATEGY_DISCOVERY_DESC,
            "Forgotten Favorites": TKey.STRATEGY_FORGOTTEN_DESC,
        }
        if internal_id in desc_keys:
            self.desc_label.setText(tr(desc_keys[internal_id]))

    def _on_debug_toggled(self, checked: bool) -> None:
        self.table_model.set_debug_mode(checked)

    def _on_generate(self) -> None:
        if not self._context.mix_service: return
        preset_name = self.preset_combo.currentData()
        limit = self.limit_spin.value()
        adaptive = self.chk_adaptive.isChecked()
        query = self.search_input.text().strip()

        self.setCursor(Qt.CursorShape.WaitCursor)
        self.btn_generate.setEnabled(False)
        try:
            self._current_songs = self._context.mix_service.generate_by_preset(
                preset_name=preset_name, limit=limit, adaptive=adaptive, query=query,
                suppress_instrumental=self.chk_inst.isChecked(),
                suppress_live=self.chk_live.isChecked(),
                suppress_remix=self.chk_remix.isChecked(),
                suppress_demo=self.chk_demo.isChecked(),
                suppress_acoustic=self.chk_acoustic.isChecked(),
            )
            stats = self._context.mix_service.get_last_stats()
            scored_list = self._context.mix_service.get_last_scored_list()
            self.table_model.set_recommendation_result(stats)
            self.table_model.set_scored_list(scored_list)
            self.table_model.set_songs(self._current_songs)
            self.table_view.viewport().update()
            self.btn_save.setEnabled(len(self._current_songs) > 0)
        except Exception as e:
            QMessageBox.critical(self, tr(TKey.DIALOG_ERROR_TITLE), tr(TKey.DIALOG_ERROR_GEN_FAILED, error=str(e)))
        finally:
            self.btn_generate.setEnabled(True)
            self.unsetCursor()

    def _on_save(self) -> None:
        """国際化されたプレイリスト名でNavidromeに保存。"""
        if not self._current_songs or not self._context.playlist_service:
            return

        # 1. 現在の戦略IDを取得
        internal_id = self.preset_combo.currentData()

        # 2. プレイリスト名用の翻訳キーマッピング
        playlist_name_keys = {
            "Daily Mix": TKey.PLAYLIST_NAME_DAILY,
            "Favorites Mix": TKey.PLAYLIST_NAME_FAVORITES,
            "Discovery Mix": TKey.PLAYLIST_NAME_DISCOVERY,
            "Forgotten Favorites": TKey.PLAYLIST_NAME_FORGOTTEN
        }
        
        # 3. 翻訳された名称を取得 (なければ一般名称を使用)
        name_key = playlist_name_keys.get(internal_id, TKey.STRATEGY_DAILY_NAME)
        localized_name = tr(name_key)
        
        # 4. 日時文字列の作成 (YYYY-MM-DD HH:mm)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 5. フォーマットを適用して最終的なプレイリスト名を構築
        playlist_title = tr(TKey.PLAYLIST_NAME_FORMAT, name=localized_name, datetime=now_str)

        # 6. 保存実行
        playlist = self._context.playlist_service.create_mix_playlist(
            mix_name=playlist_title,
            songs=self._current_songs,
            auto_overwrite=True,
        )

        if playlist:
            QMessageBox.information(
                self, 
                tr(TKey.DIALOG_SUCCESS_TITLE), 
                tr(TKey.DIALOG_SUCCESS_SAVE, name=playlist.name)
            )