import logging
import os
from datetime import datetime

def setup_logger(name: str = "FeishinMixGenerator"):
    """
    ロガーをセットアップします。
    重複出力を防ぐために、既存のハンドラがある場合は再利用します。
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # --- 重要：重複防止策 ---
    # すでにハンドラ（出力先）が設定されている場合は、そのまま返す
    if logger.handlers:
        return logger

    # フォーマットの設定
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. コンソール出力用のハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. ファイル出力用のハンドラ
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    file_handler = logging.FileHandler(
        os.path.join(log_dir, "app.log"), 
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 親ロガー（Root）への伝播を無効にする（これも重複防止に有効）
    logger.propagate = False

    return logger