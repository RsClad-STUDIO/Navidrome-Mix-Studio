from models.song import Song
from utils.title_normalizer import TitleNormalizer


class VersionFilter:
    """楽曲タイトル・アルバム名のバージョン表記を設定に応じて除外する。"""

    def __init__(self, config: dict) -> None:
        self.suppress_instrumental = config.get("suppress_instrumental", True)
        self.suppress_live = config.get("suppress_live", False)
        self.suppress_remix = config.get("suppress_remix", False)
        self.suppress_demo = config.get("suppress_demo", False)
        self.suppress_acoustic = config.get("suppress_acoustic", False)

    def is_suppressed(self, song: Song) -> bool:
<<<<<<< origin/main
        """除外設定に基づいて、その曲を弾くべきか判定します。"""
        v_info = TitleNormalizer.detect_versions(song.title)
        if self.suppress_instrumental and v_info.get("instrumental"):
            return True
        if self.suppress_live and v_info.get("live"):
            return True
        if self.suppress_remix and v_info.get("remix"):
            return True
        if self.suppress_demo and v_info.get("demo"):
            return True
        if self.suppress_acoustic and v_info.get("acoustic"):
            return True
        return False
=======
        """有効化された除外条件に該当する場合だけ True を返す。"""
        searchable_text = f"{song.title or ''} {song.album or ''}"
        versions = TitleNormalizer.detect_versions(searchable_text)

        return (
            (self.suppress_instrumental and versions.get("instrumental", False))
            or (self.suppress_live and versions.get("live", False))
            or (self.suppress_remix and versions.get("remix", False))
            or (self.suppress_demo and versions.get("demo", False))
            or (self.suppress_acoustic and versions.get("acoustic", False))
        )
>>>>>>> HEAD

    def is_variant(self, song: Song) -> bool:
        """何らかのバージョン違いであるかを返す。"""
        searchable_text = f"{song.title or ''} {song.album or ''}"
        return any(TitleNormalizer.detect_versions(searchable_text).values())
