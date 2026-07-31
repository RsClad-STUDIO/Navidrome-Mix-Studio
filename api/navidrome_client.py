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

    def _request(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """汎用リクエストメソッド。404等の通信エラー時に例外で止めず安全に処理。"""
        if not self.server_url:
            return {}
        url = f"{self.server_url}/rest/{endpoint}"
        req_params = self._get_base_params()
        if params:
            req_params.update(params)

        try:
            resp = requests.get(url, params=req_params, timeout=10)
            if resp.status_code == 404:
                self._logger.debug(f"[API] 404 Not Found: {endpoint}")
                return {}
            resp.raise_for_status()
            data = resp.json()
            sub = data.get("subsonic-response", {})
            if sub.get("status") == "ok":
                return sub
            else:
                err = sub.get("error", {})
                self._logger.error(f"Navidrome API Error ({endpoint}): {err.get('message')}")
                return {}
        except Exception as e:
            self._logger.warning(f"Failed HTTP request to {endpoint}: {e}")
            return {}

    def get_starred(self) -> Dict[str, Any]:
        """お気に入り（スター付き）データ（曲、アルバム、アーティスト）を取得します。"""
        res = self._request("getStarred")
        return res.get("starred", {})

    def get_starred_songs(self) -> List[Dict[str, Any]]:
        return self.get_starred().get("song", [])

    def get_starred_albums(self) -> List[Dict[str, Any]]:
        return self.get_starred().get("album", [])

    def get_starred_artists(self) -> List[Dict[str, Any]]:
        return self.get_starred().get("artist", [])

    def search_songs(
        self, query: str = "", count: int = 1000, size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """曲一覧を取得します（search3 API利用）。"""
        limit = size if size is not None else count
        res = self._request("search3", {"query": query, "songCount": str(limit)})
        search_res = res.get("searchResult3", {})
        return search_res.get("song", [])

    def get_songs(
        self, query: str = "", size: int = 1000, count: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """search_songs への互換エイリアスメソッド。"""
        limit = count if count is not None else size
        return self.search_songs(query=query, count=limit)

    def get_history(
        self, count: int = 500, size: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """再生履歴を取得します。getRecentPlayed / getHistory / getNowPlaying を段階的に試行。"""
        limit = size if size is not None else count

        # 1. getRecentPlayed (最も標準的)
        res = self._request("getRecentPlayed", {"count": str(limit)})
        recent = res.get("recentPlayed", {}).get("entry", [])
        if recent:
            return recent if isinstance(recent, list) else [recent]

        # 2. getHistory (Scrobble 履歴)
        res = self._request("getHistory", {"size": str(limit)})
        history = res.get("history", {}).get("item", [])
        if history:
            return history if isinstance(history, list) else [history]

        # 3. getNowPlaying (現在再生中・直近)
        res = self._request("getNowPlaying")
        now_playing = res.get("nowPlaying", {}).get("entry", [])
        return now_playing if isinstance(now_playing, list) else []

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
        return res.get("playlists", {}).get("playlist", [])

    def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """特定のプレイリストの詳細（曲リスト含む）を取得します。"""
        res = self._request("getPlaylist", {"id": playlist_id})
        return res.get("playlist", {})

    def delete_playlist(self, playlist_id: str) -> bool:
        """指定されたプレイリストを削除します。"""
        res = self._request("deletePlaylist", {"id": playlist_id})
        return res.get("status") == "ok"