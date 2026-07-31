from engine.strategies.daily_strategy import DailyStrategy
from engine.strategies.favorites_strategy import FavoritesStrategy
from engine.strategies.discovery_strategy import DiscoveryStrategy
from engine.strategies.forgotten_strategy import ForgottenStrategy

class StrategyFactory:
    """プリセット名に応じた戦略クラスを生成するファクトリ。"""
    
    @staticmethod
    def create(preset_name: str):
        # プリセット名に特定のキーワードが含まれているかで判断
        if "Daily" in preset_name:
            return DailyStrategy()
        if "Discovery" in preset_name:
            return DiscoveryStrategy()
        if "Forgotten" in preset_name:
            return ForgottenStrategy()
        
        # デフォルトは Favorites
        return FavoritesStrategy()