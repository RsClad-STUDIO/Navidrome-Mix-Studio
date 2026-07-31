"""プレイリストの生成・操作を担当するサービス。 (Phase 13.5 連携修正版)"""

import logging
from typing import List, Optional
from api.navidrome_client import NavidromeClient
from models.playlist import Playlist
from models.song import Song


class PlaylistService:
    """プレイリストに関する処理を管理するサービス。"""

    def __init__(
        self, client: NavidromeClient, logger: Optional[logging.Logger] = None
    ) -> None:
        self._client = client
        self._logger = logger or logging.getLogger(__name__)

    def fetch_playlists(self) -> List[Playlist]:
        """全プレイリストを取得します。"""
        try:
            raw = self._client.get_playlists()
            return [Playlist.from_dict(p) for p in raw]
        except Exception as e:
            self._logger.error(f"Failed to fetch playlists: {e}")
            return []

    def create_playlist(
        self, name: str, song_ids: List[str]
    ) -> Optional[Playlist]:
        """新規プレイリストを作成します。"""
        try:
            raw_playlist = self._client.create_playlist(name, song_ids)
            if raw_playlist:
                return Playlist.from_dict(raw_playlist)
            return None
        except Exception as e:
            self._logger.error(f"Failed to create playlist '{name}': {e}")
            return None

    def delete_playlist(self, playlist_id: str) -> bool:
        """プレイリストを削除します。"""
        try:
            return self._client.delete_playlist(playlist_id)
        except Exception as e:
            self._logger.error(f"Failed to delete playlist {playlist_id}: {e}")
            return False

    def get_playlist_songs(self, playlist_id: str) -> List[Song]:
        """プレイリスト内の楽曲一覧を取得します。"""
        try:
            raw = self._client.get_playlist(playlist_id)
            # 'entry' キーの中に曲リストが入っています
            return [Song.from_dict(s) for s in raw.get("entry", [])]
        except Exception as e:
            self._logger.error(f"Failed to fetch songs for playlist {playlist_id}: {e}")
            return []

    def create_mix_playlist(
        self,
        mix_name: str,
        songs: List[Song],
        auto_overwrite: bool = True,
    ) -> Optional[Playlist]:
        """
        Mix用プレイリストを新規保存または自動上書きします。
        """
        if not songs:
            self._logger.warning("No songs provided for mix playlist.")
            return None

        target_name = mix_name
        song_ids = [s.id for s in songs]

        # 1. 自動上書きモードの場合、同名プレイリストを探して中身を更新
        if auto_overwrite:
            existing_playlists = self.fetch_playlists()
            for pl in existing_playlists:
                if pl.name == target_name:
                    # ★修正：NavidromeClientに合わせて引数名を song_ids に統一
                    result = self._client.update_playlist(
                        playlist_id=pl.id,
                        name=target_name,
                        song_ids=song_ids,
                    )
                    if result:
                        return pl

        # 2. 同名が見つからない、または新規作成モードの場合は新しく作る
        return self.create_playlist(target_name, song_ids)