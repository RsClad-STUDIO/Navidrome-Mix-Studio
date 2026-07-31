"""ライブラリ（楽曲、アーティスト、アルバム）の取得・キャッシュ管理サービス。"""

import logging
from typing import List, Optional

from api.navidrome_client import NavidromeClient
from models.album import Album
from models.artist import Artist
from models.song import Song


class LibraryService:
    """楽曲ライブラリ情報を統括するサービス。"""

    def __init__(
        self, client: NavidromeClient, logger: Optional[logging.Logger] = None
    ) -> None:
        """LibraryServiceを初期化します。

        Args:
            client (NavidromeClient): APIクライアント
            logger (Optional[logging.Logger]): ロガーインスタンス
        """
        self._client = client
        self._logger = logger or logging.getLogger(__name__)

    def fetch_artists(self) -> List[Artist]:
        """全アーティスト一覧を取得し、モデルのリストとして返します。

        Returns:
            List[Artist]: アーティストのリスト
        """
        try:
            raw_artists = self._client.get_artists()
            return [Artist.from_dict(a) for a in raw_artists]
        except Exception as e:
            self._logger.error(f"Failed to fetch artists: {e}")
            return []

    def fetch_albums(self, size: int = 500) -> List[Album]:
        """アルバム一覧を取得し、モデルのリストとして返します。

        Args:
            size (int): 取得件数

        Returns:
            List[Album]: アルバムのリスト
        """
        try:
            raw_albums = self._client.get_albums(size=size)
            return [Album.from_dict(a) for a in raw_albums]
        except Exception as e:
            self._logger.error(f"Failed to fetch albums: {e}")
            return []

    def fetch_songs(self, query: str = "", size: int = 500) -> List[Song]:
        """楽曲一覧を取得し、モデルのリストとして返します。

        Args:
            query (str): 検索文字
            size (int): 取得件数

        Returns:
            List[Song]: 楽曲のリスト
        """
        try:
            raw_songs = self._client.get_songs(query=query, size=size)
            return [Song.from_dict(s) for s in raw_songs]
        except Exception as e:
            self._logger.error(f"Failed to fetch songs: {e}")
            return []