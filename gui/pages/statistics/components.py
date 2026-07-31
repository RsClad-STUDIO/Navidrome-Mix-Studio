from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGroupBox, QVBoxLayout, QLabel, QFrame, QTableWidget, QHeaderView
from services.translation import tr, TKey

class StatCard(QGroupBox):
    """デザインガイドラインに基づいた共通カードコンポーネント"""
    def __init__(self, title_key: TKey):
        super().__init__()
        self.title_key = title_key
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 20, 15, 15)
        self.layout.setSpacing(10)
        
    def retranslate(self):
        self.setTitle(tr(self.title_key))

class ValueLabel(QLabel):
    """強調表示用の数値ラベル"""
    def __init__(self, text="-"):
        super().__init__(text)
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        self.setFont(font)

def create_standard_table(cols: int) -> QTableWidget:
    """共通スタイルのテーブル作成"""
    table = QTableWidget(0, cols)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setAlternatingRowColors(True)
    table.setShowGrid(False)
    table.setStyleSheet("QTableWidget { background-color: transparent; border: none; }")
    return table