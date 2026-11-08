"""各Mix戦略で使用する比率・判定閾値を定義する設定モジュール。"""

class DailyMixConfig:
    """Daily Mix 用のパラメータ"""
    # スロット比率 (合計1.0)
    RATIO_FAVORITE = 0.32
    RATIO_RECENT = 0.28
    RATIO_BOOST = 0.16
    RATIO_PAST = 0.12
    # 残りは自動的に Discovery (約0.12)

    # 判定閾値
    RECENT_DAYS_THRESHOLD = 30  # 現行DailyStrategyの動作を維持
    PAST_PLAY_COUNT_MIN = 15
    PAST_DAYS_THRESHOLD = 60
    # 初期候補プールの規模を、生成するMixの曲数に比例させる。
    CORE_POOL_RATIO = 0.40
    # Discovery候補は固定インデックスではなく、ライブラリ内のスコア分位で抽出する。
    DISCOVERY_START_RATIO = 0.005
    DISCOVERY_END_RATIO = 0.10

class FavoritesMixConfig:
    """Favorites Mix 用のパラメータ"""
    RATIO_FAVORITE = 0.8
    # 残りは Discovery (0.2)

class DiscoveryMixConfig:
    """Discovery Mix 用のパラメータ"""
    PLAY_COUNT_THRESHOLD_INITIAL = 3
    SIMILARITY_LIMIT_RATIO = 0.4  # 好きなアーティスト枠の上限

class ForgottenMixConfig:
    """Forgotten Favorites 用のパラメータ"""
    RECENT_DAYS_LIMIT = 30
    PLAY_COUNT_MIN = 1
    NON_FAVORITE_DAYS_LIMIT = 60

class GlobalConfig:
    """システム全体・補充・浄化の共通設定"""
    HARD_DURATION_LIMIT = 10800  # 3時間 (物理除外)
    LIVE_PURGE_DURATION = 1800   # 30分 (物理除外)