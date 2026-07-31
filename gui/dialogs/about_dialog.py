"""アプリケーション情報を表示する About ダイアログ。"""

import webbrowser
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGridLayout, QFrame, QDialogButtonBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QDesktopServices
from core.app_info import AppInfo
from services.translation import tr, TKey
from .license_dialog import LicenseDialog
from utils.path_utils import get_resource_path

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr(TKey.ABOUT_TITLE))
        self.setMinimumWidth(450)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 1. Header (App Name & Version)
        header_lyt = QVBoxLayout()
        name_lbl = QLabel(AppInfo.APP_NAME)
        name_font = QFont(); name_font.setBold(True); name_font.setPointSize(16)
        name_lbl.setFont(name_font)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc_lbl = QLabel(tr(TKey.ABOUT_DESCRIPTION))
        desc_lbl.setWordWrap(True)
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_lyt.addWidget(name_lbl)
        header_lyt.addWidget(desc_lbl)
        layout.addLayout(header_lyt)

        # 2. Info Grid
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)
        
        infos = [
            (tr(TKey.ABOUT_LABEL_VERSION), AppInfo.APP_VERSION),
            ("Python:", AppInfo.PYTHON_VERSION),
            ("PySide6:", AppInfo.QT_VERSION),
            (tr(TKey.ABOUT_LABEL_AUTHOR), AppInfo.APP_AUTHOR),
            (tr(TKey.ABOUT_LABEL_LICENSE), AppInfo.APP_LICENSE_NAME),
        ]
        
        for i, (label, val) in enumerate(infos):
            grid.addWidget(QLabel(label), i, 0)
            grid.addWidget(QLabel(val), i, 1)

        # Links
        grid.addWidget(QLabel(tr(TKey.ABOUT_LABEL_REPOSITORY)), len(infos), 0)
        repo_link = QLabel(f'<a href="{AppInfo.APP_REPOSITORY}">{AppInfo.APP_REPOSITORY}</a>')
        repo_link.setOpenExternalLinks(True)
        grid.addWidget(repo_link, len(infos), 1)

        layout.addLayout(grid)

        # 3. License Buttons
        btn_lyt = QHBoxLayout()
        self.btn_license = QPushButton(tr(TKey.ABOUT_BTN_VIEW_LICENSE))
        self.btn_license.clicked.connect(self._show_main_license)
        
        self.btn_third_party = QPushButton(tr(TKey.ABOUT_BTN_VIEW_THIRD_PARTY))
        self.btn_third_party.clicked.connect(self._show_third_party)
        
        # サードパーティライセンスが存在しない場合は非表示
        if not get_resource_path("THIRD_PARTY_LICENSES.md").exists():
            self.btn_third_party.setVisible(False)

        btn_lyt.addWidget(self.btn_license)
        btn_lyt.addWidget(self.btn_third_party)
        layout.addLayout(btn_lyt)

        # 4. Standard OK Button
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btns.accepted.connect(self.accept)
        layout.addWidget(btns)

    def _show_main_license(self):
        LicenseDialog(self, "LICENSE", tr(TKey.ABOUT_LABEL_LICENSE)).exec()

    def _show_third_party(self):
        LicenseDialog(self, "THIRD_PARTY_LICENSES.md", tr(TKey.ABOUT_BTN_VIEW_THIRD_PARTY)).exec()