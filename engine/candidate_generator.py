"""推薦エンジンのための候補曲（Candidate）抽出モジュール。"""

import logging
import random
from typing import List, Optional, Set

from engine.diversity import DiversityEngine
from models.song import Song
from services.blacklist_service import BlacklistService
from services.favorites_service import FavoritesService

class CandidateGenerator:
    """ライブラリから多角的な候補曲母集団を生成するクラス。"""

    def __init__(
        self,
        favorites_service: Optional[FavoritesService] = None,
        blacklist_service: Optional[BlacklistService] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._favorites_service = favorites_service
        self._blacklist_service = blacklist_service
        self._logger = logger or logging.getLogger(__name__)

    def generate_candidates(
        self,
        all_songs: List[Song],
        target_limit: int = 25,
        multiplier: int = 8,
        suppress_instrumental: bool = True,
        suppress_live: bool = False,
        suppress_remix: bool = False,
        suppress_demo: bool = False,
        suppress_acoustic: bool = False,
    ) -> List[Song]:
        """指定制限数の5〜10倍規模の候補曲リストを効率的に抽出・フィルターします。"""
        desired_candidate_count = target_limit * multiplier
        self._logger.info(f"Extracting candidates target: {desired_candidate_count} songs.")

        candidates: List[Song] = []
        seen_ids: Set[str] = set()

        div_engine = DiversityEngine(
            suppress_instrumental=suppress_instrumental,
            suppress_live=suppress_live,
            suppress_remix=suppress_remix,
            suppress_demo=suppress_demo,
            suppress_acoustic=suppress_acoustic,
        )

        # 1. フィルター処理
        for song in all_songs:
            if song.id in seen_ids:
                continue

            # Blacklist 除外
            if self._blacklist_service and self._blacklist_service.is_blacklisted(song):
                continue

            # Version 除外
            if div_engine.is_suppressed_version(song):
                continue

            # Starredフラグの同期
            if self._favorites_service and self._favorites_service.is_song_favorite(song.id):
                song.starred = True

            candidates.append(song)
            seen_ids.add(song.id)

        # ← 修正後
        favorites = []
        non_favorites = []
        for song in all_songs:
            ...
            if song.starred:
                favorites.append(song)   # Favoriteは全件必ず保持
            else:
                non_favorites.append(song)

        random.shuffle(non_favorites)    # non-favoriteだけシャッフル
        remaining_slots = max(0, desired_candidate_count - len(favorites))
        result = favorites + non_favorites[:remaining_slots]
        random.shuffle(result)           # 最後に全体をシャッフル