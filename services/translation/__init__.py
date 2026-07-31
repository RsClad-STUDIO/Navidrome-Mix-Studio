from .translation_manager import TranslationManager
from .keys import TKey
from typing import Any, Union

def tr(key: TKey | str, **kwargs: Any) -> str:
    """
    GUI側から呼び出される翻訳用ショートカット。
    TKey Enum または 直接文字列キーを受け取る。
    """
    key_str = key.value if isinstance(key, TKey) else key
    return TranslationManager.instance().translate(key_str, **kwargs)