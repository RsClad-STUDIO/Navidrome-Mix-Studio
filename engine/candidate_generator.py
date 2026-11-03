"""推薦エンジンのための候補曲（Candidate）抽出モジュール。"""

import logging
import random
from typing import List, Optional, Set

from engine.filters.diversity_engine import DiversityEngine
from models.song import Song
from services.blacklist_service import BlacklistService
from services.favorites_service import FavoritesService


class CandidateGenerator:
    """ライブラリからフィルター済みの候補曲母集団を生成するクラス。"""

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
        """重複・禁止曲・指定バージョンを除外し、お気に入りを優先して候補を返す。"""
        desired_candidate_count = max(0, target_limit * multiplier)
        if desired_candidate_count == 0:
            return []

        div_engine = DiversityEngine(
            suppress_instrumental=suppress_instrumental,
            suppress_live=suppress_live,
            suppress_remix=suppress_remix,
            suppress_demo=suppress_demo,
            suppress_acoustic=suppress_acoustic,
        )

        favorites: List[Song] = []
        non_favorites: List[Song] = []
        seen_ids: Set[str] = set()

        for song in all_songs:
            if not song.id or song.id in seen_ids:
                continue
            seen_ids.add(song.id)

            if self._blacklist_service and self._blacklist_service.is_blacklisted(song):
                continue
            if div_engine.is_suppressed_version(song):
                continue

            if self._favorites_service and self._favorites_service.is_song_favorite(song.id):
                song.starred = True

            if song.starred:
                favorites.append(song)
            else:
                non_favorites.append(song)

        random.shuffle(non_favorites)
        remaining_slots = max(0, desired_candidate_count - len(favorites))
        result = favorites + non_favorites[:remaining_slots]
        random.shuffle(result)

        self._logger.info(
            "Candidate pool generated: %s favorites + %s non-favorites",
            len(favorites),
            len(result) - len(favorites),
        )
        return result
