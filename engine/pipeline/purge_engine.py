from models.song import Song
from utils.title_normalizer import TitleNormalizer
from engine.strategies.strategy_config import GlobalConfig


class PurgeEngine:
    """楽曲が除外対象（長尺・ライブ・各種バージョン）であるかを判定する。"""

    @staticmethod
    def should_purge(song: Song, config: dict) -> bool:
        if song.duration > GlobalConfig.HARD_DURATION_LIMIT:
            return True

        combined_text = f"{song.title or ''} {song.album or ''}"
        version_info = TitleNormalizer.detect_versions(combined_text)

        if config.get("suppress_live", False):
            if version_info["live"] or song.duration > GlobalConfig.LIVE_PURGE_DURATION:
                return True

        exclusions = (
            ("suppress_instrumental", "instrumental", True),
            ("suppress_remix", "remix", False),
            ("suppress_demo", "demo", False),
            ("suppress_acoustic", "acoustic", False),
        )
        for setting, version, default in exclusions:
            if config.get(setting, default) and version_info[version]:
                return True

        return False
