import json
import unittest
from pathlib import Path


TRANSLATION_DIR = Path(__file__).resolve().parents[1] / "resources" / "translations"


class TranslationResourceTests(unittest.TestCase):
    def test_four_additional_languages_are_discoverable(self):
        expected = {
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "pt_BR": "Português (Brasil)",
        }
        for code, display_name in expected.items():
            with self.subTest(language=code):
                path = TRANSLATION_DIR / f"{code}.json"
                self.assertTrue(path.is_file())
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(data["__meta__"]["name"], display_name)
                self.assertIn("mix.button.generate", data)
                self.assertIn("settings.label.language", data)
                self.assertIn("dialog.error.save_failed", data)

    def test_locale_files_are_valid_and_use_only_known_translation_keys(self):
        english = json.loads(
            (TRANSLATION_DIR / "en.json").read_text(encoding="utf-8")
        )
        known_keys = set(english) | {"__meta__"}
        for path in TRANSLATION_DIR.glob("*.json"):
            with self.subTest(language=path.stem):
                data = json.loads(path.read_text(encoding="utf-8"))
                self.assertTrue(data.get("__meta__", {}).get("name"))
                self.assertLessEqual(set(data), known_keys)

    def test_english_fallback_covers_keys_omitted_from_partial_locales(self):
        english = json.loads(
            (TRANSLATION_DIR / "en.json").read_text(encoding="utf-8")
        )
        for code in ("es", "fr", "de", "pt_BR"):
            with self.subTest(language=code):
                locale = json.loads(
                    (TRANSLATION_DIR / f"{code}.json").read_text(encoding="utf-8")
                )
                self.assertTrue(set(locale) - {"__meta__"})
                self.assertTrue(set(english) - set(locale))


if __name__ == "__main__":
    unittest.main()
