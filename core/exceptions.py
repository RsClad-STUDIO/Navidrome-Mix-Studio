"""アプリケーション共通の独自例外クラスを定義するモジュール。"""


class AppBaseException(Exception):
    """Feishin Mix Generatorの基底例外クラス。"""

    pass


class NavidromeConnectionError(AppBaseException):
    """Navidrome サーバーへの接続失敗時に発生する例外。"""

    pass


class AuthenticationError(AppBaseException):
    """Navidrome サーバーの認証失敗時に発生する例外。"""

    pass


class PlaylistCreationError(AppBaseException):
    """プレイリストの作成・更新失敗時に発生する例外。"""

    pass


class CacheError(AppBaseException):
    """キャッシュの読み書き・パース失敗時に発生する例外。"""

    pass