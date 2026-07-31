"""Blacklist情報の保存・読み込み・除外判定を行うサービス。"""

json_path = "config/blacklist.json"

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from models.song import Song


class BlacklistService:
    """除外リスト管理および判定サービス。"""

    def __init__(
        self,
        filepath: str = "config/blacklist.json",
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._filepath = Path(filepath)
        self._logger = logger or logging.getLogger(__name__)

        self._songs: Set[str] = set()
        self._albums: Set[str] = set()
        self._artists: Set[str] = set()
        self._genres: Set[str] = set()

        self.load()

    def load(self) -> None:
        """JSONファイルからブラックリストを読み込みます。"""
        if not self._filepath.exists():
            self.save()
            return

        try:
            with open(self._filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._songs = set(data.get("songs", []))
                self._albums = set(data.get("albums", []))
                self._artists = set(data.get("artists", []))
                self._genres = set(data.get("genres", []))
        except Exception as e:
            self._logger.error(f"Failed to load blacklist: {e}")

    def save(self) -> None:
        """現在のブラックリストをJSONファイルへ書き込みます。"""
        try:
            self._filepath.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "songs": sorted(list(self._songs)),
                "albums": sorted(list(self._albums)),
                "artists": sorted(list(self._artists)),
                "genres": sorted(list(self._genres)),
            }
            with open(self._filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._logger.info("Blacklist saved successfully.")
        except Exception as e:
            self._logger.error(f"Failed to save blacklist: {e}")

    def add_item(self, category: str, value: str) -> None:
        """ブラックリストに項目を追加します。"""
        val = value.strip()
        if not val:
            return
        if category == "songs":
            self._songs.add(val)
        elif category == "albums":
            self._albums.add(val)
        elif category == "artists":
            self._artists.add(val)
        elif category == "genres":
            self._genres.add(val)
        self.save()

    def remove_item(self, category: str, value: str) -> None:
        """ブラックリストから項目を削除します。"""
        if category == "songs":
            self._songs.discard(value)
        elif category == "albums":
            self._albums.discard(value)
        elif category == "artists":
            self._artists.discard(value)
        elif category == "genres":
            self._genres.discard(value)
        self.save()

    def get_all(self) -> Dict[str, List[str]]:
        """カテゴリーごとのリストを返します。"""
        return {
            "songs": sorted(list(self._songs)),
            "albums": sorted(list(self._albums)),
            "artists": sorted(list(self._artists)),
            "genres": sorted(list(self._genres)),
        }

    def is_blacklisted(self, song: Song) -> bool:
        """楽曲がブラックリスト対象か判定します（部分一致・大文字小文字無視）。"""
        # タイトル・IDのチェック
        t_lower = song.title.lower()
        if any(s.lower() in t_lower for s in self._songs) or song.id in self._songs:
            return True
        
        # アルバムのチェック
        if song.album:
            al_lower = song.album.lower()
            if any(a.lower() in al_lower for a in self._albums):
                return True
        
        # アーティストのチェック
        if song.artist:
            ar_lower = song.artist.lower()
            if any(art.lower() in ar_lower for art in self._artists):
                return True
                
        return False