"""Phase 13.2: ReportTab - Fully Internationalized & Hardcode-Free."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QScrollArea, 
    QFrame, QGridLayout, QLabel, QProgressBar, QMessageBox, QTableWidgetItem
)
from .components import StatCard, ValueLabel, create_standard_table
from services.translation import tr, TKey

class ReportTab(QWidget):
    def __init__(self, context):
        super().__init__()
        self._context = context
        self._init_ui()

    def _init_ui(self):
        self.layout = QVBoxLayout(self); self.layout.setContentsMargins(10, 10, 10, 10)
        self.btn_refresh = QPushButton(); self.btn_refresh.setFixedWidth(200)
        self.btn_refresh.clicked.connect(self.refresh_data)
        self.layout.addWidget(self.btn_refresh)
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        container = QWidget(); self.container_layout = QVBoxLayout(container)

        self.card_conf = StatCard(TKey.STATS_REPORT_CONF)
        self.conf_bar = QProgressBar(); self.conf_bar.setFixedHeight(12); self.conf_bar.setTextVisible(False)
        self.lbl_conf_eval = QLabel("-"); self.lbl_conf_eval.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_conf.layout.addWidget(self.conf_bar); self.card_conf.layout.addWidget(self.lbl_conf_eval)
        self.container_layout.addWidget(self.card_conf)

        self.card_info = StatCard(TKey.STATS_REPORT_TITLE)
        grid = QGridLayout()
        self.lbl_time_tag = QLabel(); self.lbl_time_val = ValueLabel()
        self.lbl_pool_tag = QLabel(); self.lbl_pool_val = ValueLabel()
        self.lbl_size_tag = QLabel(); self.lbl_size_val = ValueLabel()
        grid.addWidget(self.lbl_time_tag, 0, 0); grid.addWidget(self.lbl_time_val, 0, 1, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.lbl_pool_tag, 1, 0); grid.addWidget(self.lbl_pool_val, 1, 1, Qt.AlignmentFlag.AlignRight)
        grid.addWidget(self.lbl_size_tag, 2, 0); grid.addWidget(self.lbl_size_val, 2, 1, Qt.AlignmentFlag.AlignRight)
        self.card_info.layout.addLayout(grid); self.container_layout.addWidget(self.card_info)

        row = QHBoxLayout()
        self.card_div = StatCard(TKey.STATS_REPORT_DIV_TITLE)
        div_lyt = QVBoxLayout()
        self.lbl_art_div_tag = QLabel(); self.lbl_art_div_val = ValueLabel()
        self.lbl_alb_div_tag = QLabel(); self.lbl_alb_div_val = ValueLabel()
        div_lyt.addWidget(self.lbl_art_div_tag); div_lyt.addWidget(self.lbl_art_div_val)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); sep.setStyleSheet("color: palette(mid);")
        div_lyt.addWidget(sep); div_lyt.addWidget(self.lbl_alb_div_tag); div_lyt.addWidget(self.lbl_alb_div_val)
        self.card_div.layout.addLayout(div_lyt); row.addWidget(self.card_div)

        self.card_score = StatCard(TKey.STATS_REPORT_SCORE_TITLE)
        self.score_table = create_standard_table(2)
        self.card_score.layout.addWidget(self.score_table); row.addWidget(self.card_score)
        self.container_layout.addLayout(row)

        self.card_strat = StatCard(TKey.STATS_REPORT_STRAT_TITLE)
        self.strat_table = create_standard_table(2); self.strat_table.setMinimumHeight(200)
        self.card_strat.layout.addWidget(self.strat_table); self.container_layout.addWidget(self.card_strat)

        self.container_layout.addStretch(); scroll.setWidget(container); self.layout.addWidget(scroll)

    def retranslate_ui(self):
        self.btn_refresh.setText(tr(TKey.STATS_BTN_SHOW_LAST_REPORT))
        for c in [self.card_conf, self.card_info, self.card_div, self.card_score, self.card_strat]: c.retranslate()
        self.lbl_time_tag.setText(tr(TKey.STATS_REPORT_TIME)); self.lbl_pool_tag.setText(tr(TKey.STATS_REPORT_POOL))
        self.lbl_size_tag.setText(tr(TKey.STATS_REPORT_SIZE)); self.lbl_art_div_tag.setText(tr(TKey.STATS_REPORT_ARTIST_DIV))
        self.lbl_alb_div_tag.setText(tr(TKey.STATS_REPORT_ALBUM_DIV))
        self.score_table.setHorizontalHeaderLabels([tr(TKey.TABLE_HEADER_METRIC), tr(TKey.TABLE_HEADER_VALUE)])
        self.strat_table.setHorizontalHeaderLabels([tr(TKey.TABLE_HEADER_STRATEGY), tr(TKey.TABLE_HEADER_COUNT)])

    def refresh_data(self):
        stats = self._context.mix_service.get_last_stats()
        if not stats:
            QMessageBox.information(self, tr(TKey.STATS_REPORT_TITLE), tr(TKey.STATS_REPORT_NO_HISTORY)); return
        self.conf_bar.setValue(stats.confidence)
        eval_keys = [(90, TKey.EVAL_EXCELLENT), (75, TKey.EVAL_HIGH), (50, TKey.EVAL_MEDIUM), (0, TKey.EVAL_LOW)]
        self.lbl_conf_eval.setText(tr(next(k for v, k in eval_keys if stats.confidence >= v)))
        self.lbl_time_val.setText(f"{stats.gen_time_ms} ms"); self.lbl_pool_val.setText(str(stats.pool_count)); self.lbl_size_val.setText(str(stats.limit))

        lmap = { "Low": TKey.EVAL_LOW, "Moderate": TKey.EVAL_MEDIUM, "High": TKey.EVAL_HIGH, "Excellent": TKey.EVAL_EXCELLENT }
        self.lbl_art_div_val.setText(f"{tr(lmap.get(stats.diversity.assessment_level, TKey.EVAL_MEDIUM))} ({stats.diversity.unique_artists} / {stats.limit})")
        self.lbl_alb_div_val.setText(f"({stats.diversity.unique_albums} / {stats.pool_count})")

        srows = [(tr(TKey.SCORE_METRIC_MAX), stats.scores.highest), (tr(TKey.SCORE_METRIC_AVG), stats.scores.average), (tr(TKey.SCORE_METRIC_MIN), stats.scores.lowest)]
        self.score_table.setRowCount(len(srows))
        for i, (n, v) in enumerate(srows):
            self.score_table.setItem(i, 0, QTableWidgetItem(n))
            item = QTableWidgetItem(f"{v:.1f}"); item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); self.score_table.setItem(i, 1, item)

        mmap = { "favorite": TKey.STRAT_METHOD_FAVORITE, "recent": TKey.STRAT_METHOD_RECENT, "discovery": TKey.STRAT_METHOD_DISCOVERY, "similarity_artist": TKey.STRAT_METHOD_SIMILAR_ARTIST, "similarity_album": TKey.STRAT_METHOD_SIMILAR_ALBUM, "random": TKey.STRAT_METHOD_RANDOM, "refill": TKey.STRAT_METHOD_REFILL, "rotation": TKey.STRAT_METHOD_ROTATION }
        order = ["favorite", "recent", "discovery", "similarity_artist", "similarity_album", "random", "refill", "rotation"]
        comp = stats.final_composition
        frows = [(k, comp[k]) for k in order if k in comp] + [(k, v) for k, v in comp.items() if k not in order]
        self.strat_table.setRowCount(len(frows))
        for i, (k, c) in enumerate(frows):
            self.strat_table.setItem(i, 0, QTableWidgetItem(tr(mmap.get(k, TKey.STRAT_METHOD_OTHER))))
            item = QTableWidgetItem(str(c)); item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter); self.strat_table.setItem(i, 1, item)