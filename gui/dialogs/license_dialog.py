"""ライブラリや本体のライセンス本文を表示するダイアログ。"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit, QDialogButtonBox
from PySide6.QtCore import Qt
from utils.path_utils import get_resource_path
from services.translation import tr, TKey

class LicenseDialog(QDialog):
    def __init__(self, parent, filename: str, title: str):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 450)
        self._init_ui(filename)

    def _init_ui(self, filename: str):
        layout = QVBoxLayout(self)
        
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        
        # ファイル読み込み
        path = get_resource_path(filename)
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self.text_edit.setPlainText(f.read())
            else:
                self.text_edit.setPlainText(tr(TKey.ERROR_LICENSE_NOT_FOUND))
        except Exception as e:
            self.text_edit.setPlainText(f"Error loading file: {e}")

        layout.addWidget(self.text_edit)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)