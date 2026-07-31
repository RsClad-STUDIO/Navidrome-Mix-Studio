from models.song import Song

class BaseScore:
    """スコア計算コンポーネントの基底クラス"""
    def calculate(self, song: Song, **kwargs) -> float:
        """スコア値を計算して 0.0 - 100.0 の範囲で返します。"""
        raise NotImplementedError