from models.song import Song
from utils.title_normalizer import TitleNormalizer
from engine.strategies.strategy_config import GlobalConfig

class PurgeEngine:
    """楽曲が除外対象（長尺・ライブ・インスト等）であるかを判定するエンジン。"""

    @staticmethod
    def should_purge(song: Song, config: dict) -> bool:
        # 1. 物理的な絶対上限 (GlobalConfig参照)
        if song.duration > GlobalConfig.HARD_DURATION_LIMIT:
            return True

        # 2. タイトルとアルバム名を結合して判定
        combined_text = f"{song.title} {song.album if song.album else ''}"
        v_info = TitleNormalizer.detect_versions(combined_text)

        # 3. ライブ・長尺除外
        if config.get("suppress_live", True):
            if v_info["live"] or song.duration > GlobalConfig.LIVE_PURGE_DURATION:
                return True

        # 4. インスト除外
        if config.get("suppress_instrumental", True):
            if v_info["instrumental"]:
                return True

        return False