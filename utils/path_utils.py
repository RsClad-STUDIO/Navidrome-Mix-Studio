import sys
from pathlib import Path


def get_resource_path(relative_path: str = "") -> Path:
    """
    実行環境に応じたリソースパスを取得する。

    通常実行:
        プロジェクトルートを基準に解決

    PyInstaller実行:
        一時展開ディレクトリ(_MEIPASS)を基準に解決

    Args:
        relative_path:
            取得したいリソースへの相対パス

    Returns:
        解決済みのPathオブジェクト
    """

    if hasattr(sys, "_MEIPASS"):
        # PyInstaller等でパッケージ化された環境
        base_path = Path(sys._MEIPASS)
    else:
        # 開発環境
        # utils/path_utils.py の2階層上がプロジェクトルート
        base_path = Path(__file__).resolve().parent.parent

    return base_path / relative_path