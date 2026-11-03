import json
import unittest
from pathlib import Path


TRANSLATION_DIR = Path(__file__).resolve().parents[1] / "resources" / "translations"


class TranslationResourceTests(unittest.TestCase):
    def test_translation_enum_has_no_duplicate_member_names(self):
        import ast

        keys_path = TRANSLATION_DIR.parents[1] / "services" / "translation" / "keys.py"
        tree = ast.parse(keys_path.read_text(encoding="utf-8"))
        enum_class = next(
            node for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "TKey"
        )
        member_names = []
        for node in enum_class.body:
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        member_names.append(target.id)
        self.assertEqual(
            len(member_names),
            len(set(member_names)),
            "TKey contains duplicate member names",
        )

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
                translated_keys = set(locale) - {"__meta__"}
                self.assertTrue(translated_keys)
                self.assertTrue(set(english) - set(locale))
                self.assertGreaterEqual(len(translated_keys) / (len(english) - 1), 0.8)

    def test_translation_placeholders_match_english(self):
        import re

        english = json.loads(
            (TRANSLATION_DIR / "en.json").read_text(encoding="utf-8")
        )
        placeholder_pattern = re.compile(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}")
        for code in ("es", "fr", "de", "pt_BR"):
            locale = json.loads(
                (TRANSLATION_DIR / f"{code}.json").read_text(encoding="utf-8")
            )
            for key, value in locale.items():
                if key == "__meta__":
                    continue
                with self.subTest(language=code, key=key):
                    self.assertEqual(
                        sorted(placeholder_pattern.findall(value)),
                        sorted(placeholder_pattern.findall(english[key])),
                    )


if __name__ == "__main__":
    unittest.main()
