"""Phase 13.4: SettingsPage - Final Polished version."""

from typing import TYPE_CHECKING, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox,
    QCheckBox, QSpinBox, QTimeEdit, QTabWidget, QScrollArea
)
from PySide6.QtCore import QTime, Qt
from api.navidrome_client import NavidromeClient
from models.server_profile import ServerProfile
from services.translation import tr, TKey, TranslationManager
from gui.dialogs.about_dialog import AboutDialog

if TYPE_CHECKING:
    from core.context import AppContext

class SettingsPage(QWidget):
    def __init__(self, context: "AppContext") -> None:
        super().__init__()
        self._context: "AppContext" = context
        self._profiles: List[ServerProfile] = []
        self._last_test_result = None
        
        self._init_ui()
        # 翻訳信号の接続
        TranslationManager.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()
        self._load_settings()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.tabs = QTabWidget()
        self._init_server_tab()
        self._init_general_tab()
        layout.addWidget(self.tabs)

        # 下部ボタンエリア
        btn_layout = QHBoxLayout()
        
        # Aboutボタン
        self.btn_about = QPushButton("?")
        self.btn_about.setFixedSize(30, 30)
        self.btn_about.setToolTip("About this application")
        self.btn_about.clicked.connect(self._on_about_clicked)
        btn_layout.addWidget(self.btn_about)

        btn_layout.addStretch()

        self.btn_reset = QPushButton()
        self.btn_reset.clicked.connect(self._load_settings)
        btn_layout.addWidget(self.btn_reset)

        self.btn_save_all = QPushButton()
        self.btn_save_all.setStyleSheet("height: 35px; font-weight: bold; min-width: 180px;")
        self.btn_save_all.clicked.connect(self._on_save)
        btn_layout.addWidget(self.btn_save_all)
        
        layout.addLayout(btn_layout)

    def _init_server_tab(self) -> None:
        tab = QWidget(); scroll = QScrollArea(); scroll.setWidgetResizable(True)
        container = QWidget(); lyt = QVBoxLayout(container); lyt.setSpacing(20)

        # 1. Profile Select
        self.group_prof_list = QGroupBox()
        plist_lyt = QHBoxLayout(self.group_prof_list)
        self.lbl_active_prof = QLabel()
        self.combo_profiles = QComboBox()
        self.combo_profiles.currentIndexChanged.connect(self._on_profile_index_changed)
        self.btn_add = QPushButton(); self.btn_add.clicked.connect(self._on_add_profile)
        self.btn_delete = QPushButton(); self.btn_delete.clicked.connect(self._on_delete_profile)
        plist_lyt.addWidget(self.lbl_active_prof); plist_lyt.addWidget(self.combo_profiles, 1)
        plist_lyt.addWidget(self.btn_add); plist_lyt.addWidget(self.btn_delete)
        lyt.addWidget(self.group_prof_list)

        # 2. Connection Details
        self.group_details = QGroupBox()
        det_lyt = QGridLayout(self.group_details)
        self.lbl_prof_name = QLabel(); self.edit_prof_name = QLineEdit()
        self.lbl_server_url = QLabel(); self.edit_server_url = QLineEdit()
        self.lbl_username = QLabel(); self.edit_username = QLineEdit()
        self.lbl_password = QLabel(); self.edit_password = QLineEdit()
        self.edit_password.setEchoMode(QLineEdit.EchoMode.Password)
        det_lyt.addWidget(self.lbl_prof_name, 0, 0); det_lyt.addWidget(self.edit_prof_name, 0, 1)
        det_lyt.addWidget(self.lbl_server_url, 1, 0); det_lyt.addWidget(self.edit_server_url, 1, 1)
        det_lyt.addWidget(self.lbl_username, 2, 0); det_lyt.addWidget(self.edit_username, 2, 1)
        det_lyt.addWidget(self.lbl_password, 3, 0); det_lyt.addWidget(self.edit_password, 3, 1)
        self.lbl_test_status = QLabel(); det_lyt.addWidget(self.lbl_test_status, 4, 1)
        self.btn_test_conn = QPushButton(); self.btn_test_conn.clicked.connect(self._on_test_connection)
        det_lyt.addWidget(self.btn_test_conn, 5, 1, Qt.AlignmentFlag.AlignRight)
        lyt.addWidget(self.group_details)

        # 3. Failover Priority
        self.group_priority = QGroupBox()
        pri_lyt = QGridLayout(self.group_priority)
        self.lbl_primary = QLabel(); self.combo_primary = QComboBox()
        self.lbl_secondary = QLabel(); self.combo_secondary = QComboBox()
        pri_lyt.addWidget(self.lbl_primary, 0, 0); pri_lyt.addWidget(self.combo_primary, 0, 1)
        pri_lyt.addWidget(self.lbl_secondary, 1, 0); pri_lyt.addWidget(self.combo_secondary, 1, 1)
        lyt.addWidget(self.group_priority)

        lyt.addStretch(); scroll.setWidget(container)
        v = QVBoxLayout(tab); v.addWidget(scroll); self.tabs.addTab(tab, "")

    def _init_general_tab(self) -> None:
        tab = QWidget(); lyt = QVBoxLayout(tab)
        # Language
        self.group_lang = QGroupBox()
        lang_lyt = QHBoxLayout(self.group_lang)
        self.lbl_lang = QLabel(); self.combo_lang = QComboBox()
        langs = TranslationManager.instance().available_languages()
        for code, name in langs.items(): self.combo_lang.addItem(name, code)
        self.combo_lang.currentIndexChanged.connect(self._on_language_ui_changed)
        lang_lyt.addWidget(self.lbl_lang); lang_lyt.addWidget(self.combo_lang); lang_lyt.addStretch()
        lyt.addWidget(self.group_lang)
        # Cache
        self.group_cache = QGroupBox(); clyt = QGridLayout(self.group_cache)
        self.chk_cache_enable = QCheckBox(); self.lbl_cache_expire = QLabel(); self.spin_cache_expire = QSpinBox()
        self.spin_cache_expire.setRange(1, 720); clyt.addWidget(self.chk_cache_enable, 0, 0, 1, 2)
        clyt.addWidget(self.lbl_cache_expire, 1, 0); clyt.addWidget(self.spin_cache_expire, 1, 1); lyt.addWidget(self.group_cache)
        # Scheduler
        self.group_sched = QGroupBox(); slyt = QGridLayout(self.group_sched)
        self.chk_sched_enable = QCheckBox(); self.lbl_sched_mode = QLabel(); self.combo_sched_mode = QComboBox()
        self.combo_sched_mode.addItem("", "daily"); self.combo_sched_mode.addItem("", "startup"); self.combo_sched_mode.addItem("", "interval")
        self.lbl_sched_time = QLabel(); self.time_sched = QTimeEdit()
        slyt.addWidget(self.chk_sched_enable, 0, 0, 1, 2); slyt.addWidget(self.lbl_sched_mode, 1, 0); slyt.addWidget(self.combo_sched_mode, 1, 1)
        slyt.addWidget(self.lbl_sched_time, 2, 0); slyt.addWidget(self.time_sched, 2, 1); lyt.addWidget(self.group_sched)
        # Mix Defaults
        self.group_mix = QGroupBox(); mlyt = QGridLayout(self.group_mix)
        self.lbl_mix_count = QLabel(); self.spin_mix_count = QSpinBox()
        self.spin_mix_count.setRange(1, 200); self.chk_mix_auto = QCheckBox()
        mlyt.addWidget(self.lbl_mix_count, 0, 0); mlyt.addWidget(self.spin_mix_count, 0, 1); mlyt.addWidget(self.chk_mix_auto, 1, 0, 1, 2)
        lyt.addWidget(self.group_mix); lyt.addStretch(); self.tabs.addTab(tab, "")

    def retranslate_ui(self) -> None:
        """多言語テキストの適用。"""
        self.tabs.setTabText(0, tr(TKey.SETTINGS_TAB_SERVER)); self.tabs.setTabText(1, tr(TKey.SETTINGS_TAB_GENERAL))
        self.group_prof_list.setTitle(tr(TKey.SETTINGS_GROUP_PROFILES)); self.group_details.setTitle(tr(TKey.SETTINGS_GROUP_DETAILS))
        self.group_priority.setTitle(tr(TKey.SETTINGS_GROUP_PRIORITY)); self.group_lang.setTitle(tr(TKey.SETTINGS_GROUP_LANGUAGE))
        self.group_cache.setTitle(tr(TKey.SETTINGS_GROUP_CACHE)); self.group_sched.setTitle(tr(TKey.SETTINGS_GROUP_SCHEDULER))
        self.group_mix.setTitle(tr(TKey.SETTINGS_GROUP_MIX_DEFAULTS))
        self.lbl_active_prof.setText(tr(TKey.SETTINGS_LABEL_ACTIVE_PROFILE)); self.lbl_prof_name.setText(tr(TKey.SETTINGS_LABEL_PROF_NAME))
        self.lbl_server_url.setText(tr(TKey.SETTINGS_LABEL_SERVER_URL)); self.lbl_username.setText(tr(TKey.SETTINGS_LABEL_USERNAME))
        self.lbl_password.setText(tr(TKey.SETTINGS_LABEL_PASSWORD)); self.lbl_primary.setText(tr(TKey.SETTINGS_LABEL_PRIMARY))
        self.lbl_secondary.setText(tr(TKey.SETTINGS_LABEL_SECONDARY)); self.lbl_lang.setText(tr(TKey.SETTINGS_LABEL_LANGUAGE))
        self.chk_cache_enable.setText(tr(TKey.SETTINGS_LABEL_CACHE_ENABLE)); self.lbl_cache_expire.setText(tr(TKey.SETTINGS_LABEL_CACHE_EXPIRE))
        self.chk_sched_enable.setText(tr(TKey.SETTINGS_LABEL_SCHED_ENABLE)); self.lbl_sched_mode.setText(tr(TKey.SETTINGS_LABEL_SCHED_MODE))
        self.lbl_sched_time.setText(tr(TKey.SETTINGS_LABEL_SCHED_TIME)); self.lbl_mix_count.setText(tr(TKey.SETTINGS_LABEL_DEFAULT_COUNT))
        self.chk_mix_auto.setText(tr(TKey.SETTINGS_LABEL_AUTO_UPDATE))
        self.btn_add.setText(tr(TKey.SETTINGS_BTN_ADD)); self.btn_delete.setText(tr(TKey.SETTINGS_BTN_DELETE))
        self.btn_test_conn.setText(tr(TKey.SETTINGS_BTN_TEST_CONN)); self.btn_save_all.setText(tr(TKey.SETTINGS_BTN_SAVE))
        self.btn_reset.setText(tr(TKey.SETTINGS_BTN_RESET))
        
        # スケジュールモード名の翻訳更新
        sm = {"daily": TKey.SETTINGS_SCHED_MODE_DAILY, "startup": TKey.SETTINGS_SCHED_MODE_STARTUP, "interval": TKey.SETTINGS_SCHED_MODE_INTERVAL}
        for i in range(self.combo_sched_mode.count()):
            self.combo_sched_mode.setItemText(i, tr(sm.get(self.combo_sched_mode.itemData(i))))
        
        if not self._last_test_result: self.lbl_test_status.setText(tr(TKey.SETTINGS_STATUS_NOT_TESTED))
        else: self._update_status_label(self._last_test_result)

    def _update_status_label(self, res):
        if res.success:
            self.lbl_test_status.setText(tr(TKey.SETTINGS_STATUS_CONNECTED_FORMAT, version=res.version, ms=res.response_time_ms))
            self.lbl_test_status.setStyleSheet("color: green;")
        else:
            self.lbl_test_status.setText(tr(TKey.SETTINGS_STATUS_FAILED_FORMAT, error=res.error_message))
            self.lbl_test_status.setStyleSheet("color: red;")

    def _load_settings(self) -> None:
        s = self._context.settings
        p_data = s.get("profiles", [])
        self._profiles = [ServerProfile.from_dict(d) for d in p_data] if p_data else [ServerProfile(name="Local", url="", username="", password="")]
        self._refresh_profile_combos(s.get("active_profile", "Local"))
        
        self.combo_lang.blockSignals(True)
        idx = self.combo_lang.findData(TranslationManager.instance().current_lang)
        if idx >= 0: self.combo_lang.setCurrentIndex(idx)
        self.combo_lang.blockSignals(False)

        self.chk_cache_enable.setChecked(s.get("cache.enabled", True))
        self.spin_cache_expire.setValue(s.get("cache.expire_hours", 24))
        self.chk_sched_enable.setChecked(s.get("scheduler.enabled", False))
        midx = self.combo_sched_mode.findData(s.get("scheduler.mode", "daily"))
        self.combo_sched_mode.setCurrentIndex(midx if midx >= 0 else 0)
        self.time_sched.setTime(QTime.fromString(s.get("scheduler.time", "07:00"), "HH:mm"))
        self.spin_mix_count.setValue(s.get("mix.default_count", 50))
        self.chk_mix_auto.setChecked(s.get("mix.auto_update", False))

    def _refresh_profile_combos(self, active_name: str) -> None:
        for c in [self.combo_profiles, self.combo_primary, self.combo_secondary]:
            c.blockSignals(True); c.clear()
        self.combo_secondary.addItem(tr(TKey.COMMON_NONE), "None")
        for p in self._profiles:
            for c in [self.combo_profiles, self.combo_primary, self.combo_secondary]: c.addItem(p.name, p.name)
        self.combo_profiles.setCurrentIndex(max(0, self.combo_profiles.findData(active_name)))
        s = self._context.settings
        self.combo_primary.setCurrentText(s.get("server.primary", "Local"))
        self.combo_secondary.setCurrentText(s.get("server.secondary", "None"))
        for c in [self.combo_profiles, self.combo_primary, self.combo_secondary]: c.blockSignals(False)
        self._on_profile_index_changed(self.combo_profiles.currentIndex())

    def _on_profile_index_changed(self, index: int) -> None:
        if 0 <= index < len(self._profiles):
            p = self._profiles[index]
            self.edit_prof_name.setText(p.name); self.edit_server_url.setText(p.url)
            self.edit_username.setText(p.username); self.edit_password.setText(p.password)
            self.lbl_test_status.setText(tr(TKey.SETTINGS_STATUS_NOT_TESTED)); self.lbl_test_status.setStyleSheet("color: gray;"); self._last_test_result = None

    def _on_add_profile(self) -> None:
        name = f"New Profile {len(self._profiles)+1}"
        self._profiles.append(ServerProfile(name=name, url="", username="", password=""))
        self._refresh_profile_combos(name)

    def _on_delete_profile(self) -> None:
        if len(self._profiles) <= 1:
            QMessageBox.warning(self, tr(TKey.SETTINGS_TITLE), tr(TKey.WARNING_PROFILE_REQUIRED))
            return
        idx = self.combo_profiles.currentIndex()
        if QMessageBox.question(self, tr(TKey.DIALOG_CONFIRM_DELETE_TITLE), tr(TKey.DIALOG_CONFIRM_DELETE_MSG, name=self._profiles[idx].name)) == QMessageBox.StandardButton.Yes:
            self._profiles.pop(idx); self._refresh_profile_combos(self._profiles[0].name)

    def _on_test_connection(self) -> None:
        self.lbl_test_status.setText(tr(TKey.SETTINGS_STATUS_CONNECTING)); self.lbl_test_status.setStyleSheet("color: orange;")
        client = NavidromeClient(self.edit_server_url.text(), self.edit_username.text(), self.edit_password.text())
        self._last_test_result = client.test_connection()
        self._update_status_label(self._last_test_result)

    def _on_language_ui_changed(self) -> None:
        code = self.combo_lang.currentData()
        if code: TranslationManager.instance().load_language(code)

    def _on_about_clicked(self) -> None:
        AboutDialog(self).exec()

    def _on_save(self) -> None:
        """全ての情報を一括保存し、必要に応じて再起動を促す。"""
        s = self._context.settings
        
        # 1. 保存前の接続設定を保持（比較用）
        # 現在のクライアント、または設定ファイルから取得
        old_url = s.get("connection.server_url", "")
        old_user = s.get("connection.username", "")
        old_pass = s.get("connection.password", "")

        # 2. 編集中のプロファイル内容を同期
        idx = self.combo_profiles.currentIndex()
        if idx >= 0:
            self._profiles[idx].name = self.edit_prof_name.text()
            self._profiles[idx].url = self.edit_server_url.text()
            self._profiles[idx].username = self.edit_username.text()
            self._profiles[idx].password = self.edit_password.text()

        # 3. 設定オブジェクトへの値セット
        s.set("profiles", [p.to_dict() for p in self._profiles])
        s.set("active_profile", self.edit_prof_name.text())
        s.set("server.primary", self.combo_primary.currentText())
        s.set("server.secondary", self.combo_secondary.currentText())
        s.set("language", self.combo_lang.currentData())
        s.set("scheduler.enabled", self.chk_sched_enable.isChecked())
        s.set("scheduler.mode", self.combo_sched_mode.currentData())
        s.set("scheduler.time", self.time_sched.time().toString("HH:mm"))
        s.set("cache.enabled", self.chk_cache_enable.isChecked())
        s.set("cache.expire_hours", self.spin_cache_expire.value())
        s.set("mix.default_count", self.spin_mix_count.value())
        s.set("mix.auto_update", self.chk_mix_auto.isChecked())
        
        # 接続設定の更新（下位互換性/即時反映準備用）
        s.set("connection.server_url", self.edit_server_url.text())
        s.set("connection.username", self.edit_username.text())
        s.set("connection.password", self.edit_password.text())

        # 4. 変更検知（URL, User, Passのいずれか）
        conn_changed = (
            old_url != self.edit_server_url.text() or
            old_user != self.edit_username.text() or
            old_pass != self.edit_password.text()
        )

        # 5. 保存
        s.save()

        # 6. 通知の表示
        if conn_changed:
            # 接続設定が変わった場合：再起動案内
            QMessageBox.information(
                self, 
                tr(TKey.DIALOG_RESTART_REQUIRED_TITLE), 
                tr(TKey.DIALOG_RESTART_REQUIRED_MSG)
            )
        else:
            # それ以外の設定変更：通常の保存完了通知
            QMessageBox.information(
                self, 
                tr(TKey.DIALOG_SAVE_SUCCESS_TITLE), 
                tr(TKey.DIALOG_SAVE_SUCCESS_MSG)
            )
        
        self._refresh_profile_combos(self.edit_prof_name.text())