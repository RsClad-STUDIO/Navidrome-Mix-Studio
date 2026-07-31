"""Phase 13.1: Blocklist管理ページの国際化および名称統一対応（クラス名互換性維持版）。"""

from typing import TYPE_CHECKING
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from services.translation import tr, TKey, TranslationManager

if TYPE_CHECKING:
    from core.context import AppContext


class BlacklistPage(QWidget):
    """
    禁止リスト (Blocklist) 管理UIクラス。
    MainWindowとの互換性のためクラス名は BlacklistPage を維持します。
    """

    def __init__(self, context: "AppContext") -> None:
        super().__init__()
        self._context: "AppContext" = context
        self._init_ui()
        
        # 翻訳シグナルの接続
        TranslationManager.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()
        self._refresh_table()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 1. 入力フォーム
        input_layout = QHBoxLayout()

        self.category_combo = QComboBox()
        # 内部IDをUserDataに保持
        self.category_combo.addItem("", "songs")
        self.category_combo.addItem("", "albums")
        self.category_combo.addItem("", "artists")
        self.category_combo.addItem("", "genres")
        input_layout.addWidget(self.category_combo)

        self.value_input = QLineEdit()
        input_layout.addWidget(self.value_input)

        self.add_btn = QPushButton()
        self.add_btn.clicked.connect(self._on_add)
        input_layout.addWidget(self.add_btn)

        layout.addLayout(input_layout)

        # 2. 検索バー
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.textChanged.connect(self._refresh_table)
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        # 3. テーブル
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

    def retranslate_ui(self) -> None:
        """UIのテキストを現在の言語に更新します。"""
        # Placeholders
        self.value_input.setPlaceholderText(tr(TKey.BLOCKLIST_LABEL_VALUE_PLACEHOLDER))
        self.search_input.setPlaceholderText(tr(TKey.BLOCKLIST_LABEL_SEARCH_PLACEHOLDER))
        
        # Buttons
        self.add_btn.setText(tr(TKey.BLOCKLIST_BUTTON_ADD))
        
        # Table Headers
        self.table.setHorizontalHeaderLabels([
            tr(TKey.BLOCKLIST_TABLE_CAT),
            tr(TKey.BLOCKLIST_TABLE_VAL),
            tr(TKey.BLOCKLIST_TABLE_ACT)
        ])
        
        # ComboBox Items
        cat_map = {
            "songs": TKey.BLOCKLIST_CAT_SONGS,
            "albums": TKey.BLOCKLIST_CAT_ALBUMS,
            "artists": TKey.BLOCKLIST_CAT_ARTISTS,
            "genres": TKey.BLOCKLIST_CAT_GENRES,
        }
        for i in range(self.category_combo.count()):
            internal_id = self.category_combo.itemData(i)
            if internal_id in cat_map:
                self.category_combo.setItemText(i, tr(cat_map[internal_id]))
        
        # テーブルの内容（削除ボタン等）を再描画
        self._refresh_table()

    def _refresh_table(self) -> None:
        """テーブルの内容を最新のデータと翻訳で更新します。"""
        if not self._context.blacklist_service:
            return

        query = self.search_input.text().lower().strip()
        data = self._context.blacklist_service.get_all()

        rows = []
        for cat, items in data.items():
            for item in items:
                if not query or query in item.lower():
                    rows.append((cat, item))

        self.table.setRowCount(len(rows))
        
        # カテゴリ内部IDから表示名への変換用マップ
        cat_display_map = {
            "songs": tr(TKey.BLOCKLIST_CAT_SONGS),
            "albums": tr(TKey.BLOCKLIST_CAT_ALBUMS),
            "artists": tr(TKey.BLOCKLIST_CAT_ARTISTS),
            "genres": tr(TKey.BLOCKLIST_CAT_GENRES),
        }

        for idx, (cat, val) in enumerate(rows):
            display_cat = cat_display_map.get(cat, cat)
            self.table.setItem(idx, 0, QTableWidgetItem(display_cat))
            self.table.setItem(idx, 1, QTableWidgetItem(val))

            # 削除ボタンの翻訳対応
            del_btn = QPushButton(tr(TKey.BLOCKLIST_BUTTON_REMOVE))
            del_btn.clicked.connect(lambda _, c=cat, v=val: self._on_remove(c, v))
            self.table.setCellWidget(idx, 2, del_btn)

    def _on_add(self) -> None:
        """入力された値を禁止リストに追加します。"""
        val = self.value_input.text().strip()
        if val and self._context.blacklist_service:
            cat = self.category_combo.currentData() # 内部ID (UserData) を使用
            self._context.blacklist_service.add_item(cat, val)
            self.value_input.clear()
            self._refresh_table()

    def _on_remove(self, category: str, value: str) -> None:
        """指定された項目を禁止リストから削除します。"""
        if self._context.blacklist_service:
            self._context.blacklist_service.remove_item(category, value)
            self._refresh_table()