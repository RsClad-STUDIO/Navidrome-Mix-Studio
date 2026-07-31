"""Phase 12.7.1: 戦略ロジックの定数・閾値を管理する設定ファイル"""

class DailyMixConfig:
    """Daily Mix 用のパラメータ"""
    # スロット比率 (合計1.0)
    RATIO_FAVORITE = 0.32
    RATIO_RECENT = 0.28
    RATIO_BOOST = 0.16
    RATIO_PAST = 0.12
    # 残りは自動的に Discovery (約0.12)

    # 判定閾値
    RECENT_DAYS_THRESHOLD = 14
    PAST_PLAY_COUNT_MIN = 15
    PAST_DAYS_THRESHOLD = 60
    CORE_POOL_SIZE = 10

class FavoritesMixConfig:
    """Favorites Mix 用のパラメータ"""
    RATIO_FAVORITE = 0.8
    # 残りは Discovery (0.2)

class DiscoveryMixConfig:
    """Discovery Mix 用のパラメータ"""
    PLAY_COUNT_THRESHOLD_INITIAL = 3
    PLAY_COUNT_THRESHOLD_MAX = 5
    SIMILARITY_LIMIT_RATIO = 0.4  # 好きなアーティスト枠の上限

class ForgottenMixConfig:
    """Forgotten Favorites 用のパラメータ"""
    RECENT_DAYS_LIMIT = 30
    PLAY_COUNT_MIN = 1

class GlobalConfig:
    """システム全体・補充・浄化の共通設定"""
    TOP_POOL_SIZE = 300
    HARD_DURATION_LIMIT = 10800  # 3時間 (物理除外)
    LIVE_PURGE_DURATION = 1800   # 30分 (物理除外)