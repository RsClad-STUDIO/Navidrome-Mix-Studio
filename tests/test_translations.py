import json
import re
import unittest
from pathlib import Path

from services.translation.keys import TKey


ROOT = Path(__file__).resolve().parents[1]
TRANSLATIONS = ROOT / "resources" / "translations"


class TranslationResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (TRANSLATIONS / "en.json").open(encoding="utf-8") as file:
            cls.english = json.load(file)
        with (TRANSLATIONS / "ja.json").open(encoding="utf-8") as file:
            cls.japanese = json.load(file)
        cls.english.pop("__meta__", None)
        cls.japanese.pop("__meta__", None)

    def test_japanese_and_english_have_the_same_keys(self):
        self.assertEqual(set(self.english), set(self.japanese))

    def test_every_translation_key_has_an_english_and_japanese_value(self):
        for key in TKey:
            with self.subTest(key=key.value):
                self.assertIn(key.value, self.english)
                self.assertIn(key.value, self.japanese)

    def test_translation_placeholders_match(self):
        pattern = re.compile(r"\{([A-Za-z_]\w*)\}")
        for key in self.english:
            with self.subTest(key=key):
                english_placeholders = sorted(pattern.findall(self.english[key]))
                japanese_placeholders = sorted(pattern.findall(self.japanese[key]))
                self.assertEqual(english_placeholders, japanese_placeholders)


if __name__ == "__main__":
    unittest.main()
