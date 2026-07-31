"""Navidromeのお気に入り（Star）データを取得・同期・管理するサービス。"""

import logging
from typing import Optional, Set
from api.navidrome_client import NavidromeClient
from cache.cache_manager import CacheManager


class FavoritesService:
    """スター付き楽曲・アーティスト・アルバムIDのセットを保持・同期するサービス。"""

    def __init__(
        self,
        client: NavidromeClient,
        cache_manager: Optional[CacheManager] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._client = client
        self._cache_manager = cache_manager
        self._logger = logger or logging.getLogger(__name__)

        self._starred_song_ids: Set[str] = set()
        self._starred_artist_names: Set[str] = set()
        self._starred_album_names: Set[str] = set()

    def sync_favorites(self) -> None:
        """Navidrome APIまたはキャッシュからFavorites情報を最新化します。"""
        cache_key = "favorites_data"
        if self._cache_manager:
            cached = self._cache_manager.get(cache_key)
            if cached:
                self._starred_song_ids = set(cached.get("songs", []))
                self._starred_artist_names = set(cached.get("artists", []))
                self._starred_album_names = set(cached.get("albums", []))
                self._logger.info("Favorites loaded from cache.")
                return

        self._logger.info("Syncing Favorites from Navidrome API...")
        starred = self._client.get_starred()

        songs = [str(s.get("id")) for s in starred.get("song", []) if s.get("id")]
        artists = [s.get("name") for s in starred.get("artist", []) if s.get("name")]
        albums = [s.get("name") for s in starred.get("album", []) if s.get("name")]

        self._starred_song_ids = set(songs)
        self._starred_artist_names = set(artists)
        self._starred_album_names = set(albums)

        if self._cache_manager:
            self._cache_manager.set(
                cache_key,
                {
                    "songs": list(self._starred_song_ids),
                    "artists": list(self._starred_artist_names),
                    "albums": list(self._starred_album_names),
                },
            )

        self._logger.info(
            f"Synced Favorites: {len(self._starred_song_ids)} songs, "
            f"{len(self._starred_artist_names)} artists, {len(self._starred_album_names)} albums."
        )

    def is_song_favorite(self, song_id: str) -> bool:
        return song_id in self._starred_song_ids

    def is_artist_favorite(self, artist_name: str) -> bool:
        return artist_name in self._starred_artist_names

    def is_album_favorite(self, album_name: str) -> bool:
        return album_name in self._starred_album_names