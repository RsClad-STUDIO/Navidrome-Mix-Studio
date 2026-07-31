"""Phase 13.2: MixTableModel - Consistent Reason Mapping & Hardcode-Free."""

from typing import Any, List, Optional, Dict
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from services.translation import tr, TKey, TranslationManager
from models.song import Song

class MixTableModel(QAbstractTableModel):
    REASON_MAP = {
        "favorite": TKey.STRAT_METHOD_FAVORITE, "star": TKey.STRAT_METHOD_FAVORITE,
        "recent": TKey.STRAT_METHOD_RECENT, "recently_played": TKey.STRAT_METHOD_RECENT,
        "discovery": TKey.STRAT_METHOD_DISCOVERY, "random_discovery": TKey.STRAT_METHOD_DISCOVERY,
        "similarity_artist": TKey.STRAT_METHOD_SIMILAR_ARTIST, "artist_similarity": TKey.STRAT_METHOD_SIMILAR_ARTIST,
        "similarity_album": TKey.STRAT_METHOD_SIMILAR_ALBUM, "album_similarity": TKey.STRAT_METHOD_SIMILAR_ALBUM,
        "random": TKey.STRAT_METHOD_RANDOM, "refill": TKey.STRAT_METHOD_REFILL, "rotation": TKey.STRAT_METHOD_ROTATION,
    }

    def __init__(self, songs: Optional[List[Song]] = None) -> None:
        super().__init__()
        self._songs: List[Song] = songs or []
        self._debug_mode: bool = False
        self._scored_dict: Dict[str, Any] = {}
        TranslationManager.instance().language_changed.connect(self._on_lang_changed)

    def _on_lang_changed(self):
        self.headerDataChanged.emit(Qt.Orientation.Horizontal, 0, self.columnCount() - 1)
        self.layoutChanged.emit()

    def set_debug_mode(self, enabled: bool) -> None:
        self.beginResetModel(); self._debug_mode = enabled; self.endResetModel()

    def set_recommendation_result(self, result) -> None: self._rec_result = result

    def set_scored_list(self, scored_list: List[Any]) -> None:
        self._scored_dict = {score.song.id: score for score in scored_list}
        self.layoutChanged.emit()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._songs) if not parent.isValid() else 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 7 if self._debug_mode else 6

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._songs)): return None
        song = self._songs[index.row()]; col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if not self._debug_mode:
                # Normal Mode: [#, Title, Artist, Album, Year, Duration]
                vals = [index.row() + 1, song.title, song.artist, song.album or "-", song.year or "-", f"{song.duration // 60}:{song.duration % 60:02d}"]
                return vals[col] if col < len(vals) else None
            else:
                # Debug Mode
                sinfo = self._scored_dict.get(song.id)
                if col == 0: return index.row() + 1
                elif col == 1: return song.title
                elif col == 2: return song.artist
                elif col == 3: return f"{sinfo.total_score:.1f}" if sinfo else "-"
                elif col == 4:
                    if not sinfo: return tr(TKey.STRAT_METHOD_OTHER)
                    raw = next((str(getattr(sinfo, a)).lower() for a in ['reason', 'main_reason', 'category'] if getattr(sinfo, a, None)), "other")
                    return tr(self.REASON_MAP.get(raw.replace(" ", "_"), TKey.STRAT_METHOD_OTHER))
                elif col == 5: return song.album or "-"
                elif col == 6: return f"{song.duration // 60}:{song.duration % 60:02d}"

        if role == Qt.ItemDataRole.TextAlignmentRole: return int(Qt.AlignmentFlag.AlignCenter)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if not self._debug_mode:
                h = ["#", TKey.TABLE_HEADER_TITLE, TKey.TABLE_HEADER_ARTIST, TKey.TABLE_HEADER_ALBUM, TKey.TABLE_HEADER_YEAR, TKey.TABLE_HEADER_DURATION]
            else:
                h = ["#", TKey.TABLE_HEADER_TITLE, TKey.TABLE_HEADER_ARTIST, TKey.TABLE_HEADER_SCORE, TKey.TABLE_HEADER_REASON, TKey.TABLE_HEADER_ALBUM, TKey.TABLE_HEADER_DURATION]
            return tr(h[section]) if isinstance(h[section], TKey) else h[section]
        return None

    def set_songs(self, songs: List[Song]) -> None:
        self.beginResetModel(); self._songs = list(songs); self.endResetModel()