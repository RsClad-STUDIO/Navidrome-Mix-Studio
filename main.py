"""アプリケーションのエントリーポイント。"""

import logging
import sys

from core.app import Application
from engine.recommendation import RecommendationEngine
import ctypes

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
    "RsClad-STUDIO.NavidromeMixStudio"
)


def setup_logging() -> None:
    """コンソールおよびファイルへのログ出力設定を行います。"""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    setup_logging()

    # core/app.py 内で QApplication が作成されるため、こちらでは直接呼ばない
    app = Application()
    sys.exit(app.run())


if __name__ == "__main__":
    main()