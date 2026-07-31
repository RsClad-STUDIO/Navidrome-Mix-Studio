from models.song import Song
from utils.title_normalizer import TitleNormalizer

class VersionFilter:
    """楽曲のバージョン（Inst/Live/Remix等）に基づいたフィルタリング。"""

    def __init__(self, config: dict) -> None:
        self.suppress_instrumental = config.get("suppress_instrumental", True)
        self.suppress_live = config.get("suppress_live", False)
        self.suppress_remix = config.get("suppress_remix", False)

    def is_suppressed(self, song: Song) -> bool:
        """除外設定に基づいて、その曲を弾くべきか判定します。"""
        v_info = TitleNormalizer.detect_versions(song.title)
        if self.suppress_instrumental and v_info.get("instrumental"):
            return True
        if self.suppress_live and v_info.get("live"):
            return True
        if self.suppress_remix and v_info.get("remix"):
            return True
        return False

    def is_variant(self, song: Song) -> bool:
        """何らかのバリエーション違いであるか。"""
        return any(TitleNormalizer.detect_versions(song.title).values())