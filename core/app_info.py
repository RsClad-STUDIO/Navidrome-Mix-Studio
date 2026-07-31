"""アプリケーションのメタデータを管理するモジュール。"""

import sys
import PySide6.QtCore

class AppInfo:
    APP_NAME = "Navidrome Mix Studio"
    APP_VERSION = "1.0.0"
    APP_AUTHOR = "RsClad-STUDIO"
    APP_COPYRIGHT = "Copyright (c) 2026 RsClad-STUDIO"
    APP_LICENSE_NAME = "MIT License"
    
    APP_REPOSITORY = "https://github.com/RsClad-STUDIO/Navidrome-Mix-Studio"
    
    PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    QT_VERSION = PySide6.QtCore.__version__