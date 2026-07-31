import json
import logging
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal
from utils.path_utils import get_resource_path

class TranslationManager(QObject):
    """
    アプリケーションの国際化を管理するシングルトン。
    '現在言語 -> 英語(en) -> キー文字列' の3段階フォールバックを実装。
    """
    language_changed = Signal()
    _instance: Optional['TranslationManager'] = None

    @classmethod
    def instance(cls) -> 'TranslationManager':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self) -> None:
        # 二重初期化の防止 (Qtシングルトンの標準パターン)
        if getattr(self, "_initialized", False):
            return
        super().__init__()
        self._initialized = True
        
        self._logger = logging.getLogger("TranslationManager")
        # リソースパスの取得 (path_utils.py を利用)
        self._base_path = get_resource_path("resources/translations")
        
        self._current_lang = ""
        self._translations: Dict[str, str] = {}
        self._fallback_translations: Dict[str, str] = {}

        # 1. 常に英語(en.json)をフォールバック用としてバックグラウンドで保持
        self._load_fallback()

    def _load_fallback(self) -> None:
        """en.json をロードし、翻訳辞書からメタデータを除去して保持する。"""
        en_path = self._base_path / "en.json"
        if en_path.exists():
            try:
                with open(en_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data.pop("__meta__", None)  # 翻訳辞書を汚さない
                    self._fallback_translations = data
            except Exception as e:
                self._logger.error(f"Failed to load fallback (en.json): {e}")

    def available_languages(self) -> Dict[str, str]:
        """
        translations フォルダ内の JSON をスキャンして利用可能な言語リストを生成。
        JSON内の __meta__.name を表示名として使用。
        """
        langs = {}
        if not self._base_path.exists():
            return {"en": "English"}

        for json_file in self._base_path.glob("*.json"):
            lang_code = json_file.stem
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    meta = data.get("__meta__", {})
                    display_name = meta.get("name", lang_code.upper())
                    langs[lang_code] = display_name
            except Exception as e:
                self._logger.warning(f"Scan error for {json_file.name}: {e}")
        
        return dict(sorted(langs.items()))

    def load_language(self, lang_code: str) -> bool:
        """指定された言語ファイルをロードし、UIに通知する。"""
        if lang_code == self._current_lang:
            return True

        file_path = self._base_path / f"{lang_code}.json"
        try:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data.pop("__meta__", None)  # 翻訳辞書を汚さない
                    self._translations = data
                self._current_lang = lang_code
                self.language_changed.emit()  # UIへ再描画を通知
                return True
            return False
        except Exception as e:
            self._logger.error(f"Load error ({lang_code}): {e}")
            return False

    def translate(self, key: str, **kwargs: Any) -> str:
        """
        翻訳文字列を解決する。
        1. 現在の言語 2. 英語 3. キーそのもの の順で検索。
        プレースホルダー {version} などがあれば置換。
        """
        # 現在の言語から検索
        text = self._translations.get(key)
        
        # なければ英語（フォールバック）から検索
        if text is None:
            text = self._fallback_translations.get(key, key)

        # 置換パラメータがある場合のみ .format() を適用
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception as e:
                # キーが見つからず、keyそのものが返っている場合の format 失敗を保護
                self._logger.error(f"Format error for '{key}': {e}")
        
        return text

    @property
    def current_lang(self) -> str:
        return self._current_lang