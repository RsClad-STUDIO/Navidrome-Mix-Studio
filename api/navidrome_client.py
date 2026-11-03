"""Navidrome APIとの通信を担当するクライアントモジュール。 (Phase 13.3 対応版)"""

import logging
import time
import requests
from typing import Any, Dict, List, Optional
from models.server_profile import ConnectionResult


class NavidromeClient:
    def __init__(
        self,
        server_url: str = "",
        username: str = "",
        password: str = "",
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.server_url = server_url.rstrip("/") if server_url else ""
        self.username = username
        self.password = password
        self._logger = logger or logging.getLogger(__name__)

    def _get_base_params(self) -> Dict[str, str]:
        """共通パラメータ。"""
        return {
            "u": self.username,
            "p": self.password,
            "v": "1.16.1",
            "c": "FeishinMixGenerator",
            "f": "json",
        }

    @staticmethod
    def _as_list(value: Any) -> List[Dict[str, Any]]:
        """Subsonic JSONの単一オブジェクト／配列の揺れを正規化します。"""
        if value is None:
            return []
        return value if isinstance(value, list) else [value]

    def test_connection(self) -> ConnectionResult:
        """Phase 11: 接続テストを実施する。"""
        if not self.server_url:
            return ConnectionResult(success=False, error_message="Server URL is empty")

        start_perf = time.perf_counter()
        url = f"{self.server_url}/rest/ping"
        params = self._get_base_params()

        try:
            resp = requests.get(url, params=params, timeout=10)
            elapsed_ms = int((time.perf_counter() - start_perf) * 1000)

            if resp.status_code == 404:
                return ConnectionResult(success=False, error_message="Navidrome API not found (404)")

            resp.raise_for_status()
            data = resp.json()
            sub = data.get("subsonic-response", {})

            if sub.get("status") == "ok":
                return ConnectionResult(
                    success=True,
                    version=sub.get("version", "Unknown"),
                    username=self.username,
                    response_time_ms=elapsed_ms,
                )
            else:
                err = sub.get("error", {})
                code = err.get("code")
                msg = err.get("message", "Unknown API Error")
                if code == "40":
                    msg = "Unauthorized: Wrong username or password"
                return ConnectionResult(success=False, error_message=msg)

        except requests.exceptions.Timeout:
            return ConnectionResult(success=False, error_message="Timeout: Server did not respond")
        except requests.exceptions.ConnectionError:
            return ConnectionResult(success=False, error_message="Connection Failed: Host not found or refused")
        except Exception as e:
            return ConnectionResult(success=False, error_message=f"Error: {str(e)}")

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
        *,
        raise_on_error: bool = False,
    ) -> Dict[str, Any]:
        """汎用リクエスト。通常は安全に空応答へ変換し、完全取得処理では例外を通知する。"""
        if not self.server_url:
            if raise_on_error:
                raise RuntimeError("Navidrome server URL is empty")
            return {}
        url = f"{self.server_url}/rest/{endpoint}"
        req_params = self._get_base_params()
        if params:
            req_params.update(params)

        try:
            resp = requests.get(url, params=req_params, timeout=30)
            if resp.status_code == 404:
                message = f"Navidrome API endpoint not found: {endpoint}"
                if raise_on_error:
                    raise RuntimeError(message)
                self._logger.debug("[API] 404 Not Found: %s", endpoint)
                return {}
            resp.raise_for_status()
            data = resp.json()
            sub = data.get("subsonic-response", {})
            if sub.get("status") == "ok":
                return sub

            err = sub.get("error", {})
            message = (
                f"Navidrome API Error ({endpoint}): "
                f"{err.get('message', 'Unknown API error')}"
            )
            if raise_on_error:
                raise RuntimeError(message)
            self._logger.error(message)
            return {}
        except Exception as e:
            if raise_on_error:
                raise RuntimeError(
                    f"Failed HTTP request to {endpoint}: {e}"
                ) from e
            self._logger.warning("Failed HTTP request to %s: %s", endpoint, e)
            return {}

    def get_starred(self) -> Dict[str, Any]:
        """お気に入り（スター付き）データ（曲、アルバム、アーティスト）を取得します。"""
        res = self._request("getStarred")
        starred = res.get("starred") or {}
        return {
            key: self._as_list(starred.get(key))
            for key in ("song", "album", "artist")
        }

    def get_starred_songs(self) -> List[Dict[str, Any]]:
        return self.get_starred().get("song", [])

    def get_starred_albums(self) -> List[Dict[str, Any]]:
        return self.get_starred().get("album", [])

    def get_starred_artists(self) -> List[Dict[str, Any]]:
        return self.get_starred().get("artist", [])



    def get_artists(self) -> List[Dict[str, Any]]:
        """getArtistsのインデックスを平坦化してアーティスト一覧を返す。"""
        response = self._request("getArtists")
        artists_data = response.get("artists") or {}
        indexes = artists_data.get("index") or []
        if isinstance(indexes, dict):
            indexes = [indexes]

        artists: List[Dict[str, Any]] = []
        for index in indexes:
            entries = index.get("artist", [])
            if isinstance(entries, dict):
                entries = [entries]
            artists.extend(entries)

        # サーバー実装によってはindexを介さずartistを返す場合に対応する。
        direct_entries = artists_data.get("artist") or []
        if isinstance(direct_entries, dict):
            direct_entries = [direct_entries]
        artists.extend(direct_entries)
        return artists

    def get_albums(self, size: int = 500) -> List[Dict[str, Any]]:
        """getAlbumList2から指定件数のアルバム一覧を取得する。"""
        if size <= 0:
            return []

        response = self._request(
            "getAlbumList2",
            {
                "type": "alphabeticalByName",
                "size": str(size),
                "offset": "0",
            },
        )
        albums = (response.get("albumList2") or {}).get("album") or []
        return [albums] if isinstance(albums, dict) else albums

    def search_songs(
        self,
        query: str = "",
        count: Optional[int] = None,
        size: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """search3をオフセットページングし、指定がなければ全曲を取得する。

        count/sizeは後方互換用の総取得上限。APIへの1回の要求は最大500曲。
        """
        total_limit = count if count is not None else size
        if total_limit is not None and total_limit <= 0:
            return []

        page_size = 500
        offset = 0
        songs: List[Dict[str, Any]] = []
        seen_ids = set()

        while total_limit is None or len(songs) < total_limit:
            request_size = (
                page_size
                if total_limit is None
                else min(page_size, total_limit - len(songs))
            )
            response = self._request(
                "search3",
                {
                    "query": query,
                    "songCount": str(request_size),
                    "songOffset": str(offset),
                },
                raise_on_error=True,
            )
            search_result = response.get("searchResult3", {})
            page = search_result.get("song", [])
            if isinstance(page, dict):
                page = [page]
            if not page:
                break

            added = 0
            for song in page:
                song_id = str(song.get("id", ""))
                if not song_id or song_id not in seen_ids:
                    songs.append(song)
                    if song_id:
                        seen_ids.add(song_id)
                    added += 1

            if added == 0:
                raise RuntimeError(
                    "Navidrome search3 pagination did not advance; "
                    "the server may be ignoring songOffset."
                )

            offset += len(page)
            if len(page) < request_size:
                break

        self._logger.info(
            "Fetched %s songs from Navidrome (query=%r)",
            len(songs), query
        )
        return songs

    def get_songs(
        self,
        query: str = "",
        size: Optional[int] = None,
        count: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """search_songs互換API。上限未指定時は全曲を取得する。"""
        total_limit = count if count is not None else size
        return self.search_songs(query=query, count=total_limit)

    def get_history(
        self, count: int = 500, size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """履歴を取得。正常な空履歴とAPI取得失敗を区別するため、通信エラーを通知する。"""
        limit = size if size is not None else count
        attempts = (
            ("getRecentPlayed", {"count": str(limit)}, "recentPlayed", "entry"),
            ("getHistory", {"size": str(limit)}, "history", "item"),
        )
        errors = []
        successful_responses = 0

        for endpoint, params, response_key, entry_key in attempts:
            try:
                response = self._request(endpoint, params, raise_on_error=True)
            except RuntimeError as exc:
                # Unsupported endpoints may be skipped; other failures mean history
                # availability cannot be established.
                if "404" not in str(exc) and "endpoint not found" not in str(exc).lower():
                    errors.append(str(exc))
                continue

            successful_responses += 1
            entries = (response.get(response_key) or {}).get(entry_key, [])
            normalized = self._as_list(entries)
            if normalized:
                return normalized

        if errors:
            raise RuntimeError("Unable to retrieve playback history: " + "; ".join(errors))
        if successful_responses == 0:
            raise RuntimeError("No supported playback-history endpoint could be queried")
        return []

    def create_playlist(self, name: str, song_ids: List[str]) -> Optional[Dict[str, Any]]:
        """新しいプレイリストを作成します。"""
        url = f"{self.server_url}/rest/createPlaylist"
        params_list = [
            ("u", self.username),
            ("p", self.password),
            ("v", "1.16.1"),
            ("c", "FeishinMixGenerator"),
            ("f", "json"),
            ("name", name),
        ]
        for sid in song_ids:
            params_list.append(("songId", sid))

        try:
            resp = requests.get(url, params=params_list, timeout=10)
            resp.raise_for_status()
            sub = resp.json().get("subsonic-response", {})
            if sub.get("status") == "ok":
                self._logger.info(f"Playlist '{name}' created successfully.")
                return sub.get("playlist", {})
            return None
        except Exception as e:
            self._logger.error(f"Error creating playlist: {e}")
            return None

    def update_playlist(self, playlist_id: str, name: str, song_ids: List[str]) -> Optional[Dict[str, Any]]:
        """既存のプレイリストを更新（上書き）します。"""
        # Subsonic APIでは createPlaylist に playlistId を渡すと上書きになります
        url = f"{self.server_url}/rest/createPlaylist"
        params_list = [
            ("u", self.username),
            ("p", self.password),
            ("v", "1.16.1"),
            ("c", "FeishinMixGenerator"),
            ("f", "json"),
            ("playlistId", playlist_id),
            ("name", name),
        ]
        for sid in song_ids:
            params_list.append(("songId", sid))

        try:
            resp = requests.get(url, params=params_list, timeout=10)
            resp.raise_for_status()
            sub = resp.json().get("subsonic-response", {})
            if sub.get("status") == "ok":
                self._logger.info(f"Playlist '{name}' updated successfully.")
                # 更新時は playlist オブジェクトが返らない場合があるため、statusを見て判定
                return {"id": playlist_id, "name": name}
            return None
        except Exception as e:
            self._logger.error(f"Error updating playlist: {e}")
            return None

    def get_playlists(self) -> List[Dict[str, Any]]:
        """プレイリスト一覧を取得します。"""
        res = self._request("getPlaylists")
        return self._as_list((res.get("playlists") or {}).get("playlist"))

    def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """特定のプレイリストの詳細（曲リスト含む）を取得します。"""
        res = self._request("getPlaylist", {"id": playlist_id})
        return res.get("playlist", {})

    def delete_playlist(self, playlist_id: str) -> bool:
        """指定されたプレイリストを削除します。"""
        res = self._request("deletePlaylist", {"id": playlist_id})
        return res.get("status") == "ok"