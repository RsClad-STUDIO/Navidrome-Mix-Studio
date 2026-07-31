from typing import TYPE_CHECKING
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from services.translation import tr, TKey, TranslationManager
from .library_tab import LibraryTab
from .report_tab import ReportTab

if TYPE_CHECKING:
    from core.context import AppContext

class StatisticsPage(QWidget):
    def __init__(self, context: "AppContext", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._context = context
        self._init_ui()
        
        TranslationManager.instance().language_changed.connect(self.retranslate_ui)
        self.retranslate_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        self.tabs = QTabWidget()
        self.lib_tab = LibraryTab(self._context)
        self.rep_tab = ReportTab(self._context)
        
        self.tabs.addTab(self.lib_tab, "")
        self.tabs.addTab(self.rep_tab, "")
        layout.addWidget(self.tabs)

    def retranslate_ui(self) -> None:
        self.tabs.setTabText(0, tr(TKey.STATS_TAB_LIBRARY))
        self.tabs.setTabText(1, tr(TKey.STATS_TAB_REPORT))
        self.lib_tab.retranslate_ui()
        self.rep_tab.retranslate_ui()