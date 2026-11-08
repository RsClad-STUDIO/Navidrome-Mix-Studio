import json
import tempfile
import unittest
from pathlib import Path

from config.settings import Settings


class FakeCredentialStore:
    def __init__(self):
        self.values = {}
        self.deleted = []

    def set_password(self, target, password):
        self.values[target] = password

    def get_password(self, target):
        return self.values.get(target)

    def delete_password(self, target):
        self.deleted.append(target)
        self.values.pop(target, None)


class SettingsCredentialTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "config.json"
        self.store = FakeCredentialStore()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_save_never_writes_profile_password_to_json(self):
        settings = Settings(str(self.path), credential_store=self.store)
        settings.set("profiles", [{
            "name": "Home", "url": "http://localhost", "username": "user",
            "password": "secret",
        }])

        settings.save()

        saved = json.loads(self.path.read_text(encoding="utf-8"))
        profile = saved["profiles"][0]
        self.assertNotIn("password", profile)
        self.assertTrue(profile["credential_target"].startswith("NavidromeMixStudio/"))
        self.assertEqual(self.store.values[profile["credential_target"]], "secret")

    def test_load_migrates_legacy_plaintext_password(self):
        self.path.write_text(json.dumps({
            "profiles": [{
                "name": "Home", "url": "http://localhost",
                "username": "user", "password": "legacy-secret",
            }]
        }), encoding="utf-8")

        settings = Settings(str(self.path), credential_store=self.store)

        self.assertEqual(settings.get("profiles")[0]["password"], "legacy-secret")
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertNotIn("password", saved["profiles"][0])
        target = saved["profiles"][0]["credential_target"]
        self.assertEqual(self.store.get_password(target), "legacy-secret")

    def test_reload_resolves_password_from_credential_store(self):
        settings = Settings(str(self.path), credential_store=self.store)
        settings.set("profiles", [{
            "name": "Home", "url": "http://localhost", "username": "user",
            "password": "secret",
        }])
        settings.save()

        reloaded = Settings(str(self.path), credential_store=self.store)
        self.assertEqual(reloaded.get("profiles")[0]["password"], "secret")

    def test_credential_store_failure_does_not_write_plaintext(self):
        class FailingStore(FakeCredentialStore):
            def set_password(self, target, password):
                raise RuntimeError("store unavailable")

        settings = Settings(str(self.path), credential_store=FailingStore())
        settings.set("profiles", [{
            "name": "Home", "url": "http://localhost", "username": "user",
            "password": "secret",
        }])

        with self.assertRaisesRegex(RuntimeError, "store unavailable"):
            settings.save()
        self.assertFalse(self.path.exists())


if __name__ == "__main__":
    unittest.main()
