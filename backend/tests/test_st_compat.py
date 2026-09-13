"""Smoke tests for the SillyTavern-compatible API layer (4.2 / 4.3)."""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("FLASK_ENV", "development")
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key"

_TEMP_DATA = tempfile.TemporaryDirectory()
os.environ["ST_COMPAT_DATA_DIR"] = _TEMP_DATA.name
os.environ["ST_COMPAT_ENABLED"] = "true"

# Keep the tests independent from a running MySQL instance.
import app.extensions as _extensions  # noqa: E402
import app.services.scheduler as _scheduler  # noqa: E402

_extensions.init_pool = lambda _config: None  # type: ignore[attr-defined]
_scheduler.start_scheduler = lambda _app: None  # type: ignore[attr-defined]

from app import create_app  # noqa: E402
from flask_jwt_extended import create_access_token  # noqa: E402


class StCompatTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config.update(
            TESTING=True,
            JWT_TOKEN_LOCATION=["headers"],
            JWT_CSRF_IN_COOKIES=False,
            JWT_COOKIE_CSRF_PROTECT=False,
        )
        cls.client = cls.app.test_client()
        cls.data_root = Path(_TEMP_DATA.name)

    def setUp(self):
        with self.app.app_context():
            # Each test gets its own user directory so tests stay independent.
            self.token = create_access_token(identity=str(id(self)))
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.user_id = str(id(self))

    @classmethod
    def tearDownClass(cls):
        _TEMP_DATA.cleanup()

    def _user_dir(self):
        return self.data_root / self.user_id

    def test_characters_crud(self):
        payload = {
            "ch_name": "Test Character",
            "description": "A test persona",
            "personality": "Curious",
            "scenario": "In a lab",
            "first_mes": "Hello there.",
            "mes_example": "Example",
            "tags": "tag1, tag2",
            "alternate_greetings": '["Hi!"]',
        }
        response = self.client.post("/api/characters/create", data=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "Test Character.png")

        response = self.client.post("/api/characters/get", json={"avatar_url": "Test Character.png"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        card = response.get_json()
        self.assertEqual(card["name"], "Test Character")
        self.assertEqual(card["data"]["name"], "Test Character")
        self.assertEqual(card["data"]["tags"], ["tag1", "tag2"])
        self.assertEqual(card["data"]["alternate_greetings"], ["Hi!"])

        response = self.client.post("/api/characters/all", json={}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        characters = response.get_json()
        self.assertEqual(len(characters), 1)
        self.assertEqual(characters[0]["avatar"], "Test Character.png")

        response = self.client.post(
            "/api/characters/merge-attributes",
            json={"avatar": "Test Character.png", "data": {"extensions": {"talkativeness": 0.9}}},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/api/characters/get", json={"avatar_url": "Test Character.png"}, headers=self.headers)
        self.assertEqual(response.get_json()["talkativeness"], 0.9)

        response = self.client.post("/api/characters/duplicate", json={"avatar_url": "Test Character.png"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["path"], "Test Character_1.png")

        response = self.client.post(
            "/api/characters/export",
            json={"avatar_url": "Test Character.png", "format": "json"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        exported = response.get_data(as_text=True)
        self.assertIn("chara_card_v3", exported)
        self.assertIn("Test Character", exported)

        response = self.client.post("/api/characters/delete", json={"avatar_url": "Test Character_1.png"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/api/characters/all", json={}, headers=self.headers)
        self.assertEqual(len(response.get_json()), 1)

    def test_character_png_roundtrip(self):
        from app.api.st_compat import png_utils

        card = {"name": "PNG Card", "description": "", "personality": "", "scenario": "", "first_mes": "", "mes_example": ""}
        png_bytes = png_utils.default_avatar_png(__import__("json").dumps(card))
        restored = png_utils.read_character_data(png_bytes)
        self.assertIn("PNG Card", restored)

        payload = {
            "ch_name": "PNG Card",
            "description": "Imported via PNG",
            "avatar": (io.BytesIO(png_bytes), "avatar.png"),
        }
        response = self.client.post(
            "/api/characters/create",
            data=payload,
            content_type="multipart/form-data",
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_data(as_text=True), "PNG Card.png")

    def test_chats_save_get_and_search(self):
        self.client.post("/api/characters/create", data={"ch_name": "Chatter"}, headers=self.headers)
        chat = [
            {"chat_metadata": {"scenario": "test"}, "user_name": "unused", "character_name": "unused"},
            {"name": "User", "is_user": True, "mes": "Hi", "extra": {}},
            {"name": "Chatter", "is_user": False, "mes": "Hello back", "extra": {}},
        ]
        response = self.client.post(
            "/api/chats/save",
            json={"avatar_url": "Chatter.png", "file_name": "chat-1", "chat": chat},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"ok": True})

        response = self.client.post(
            "/api/chats/get",
            json={"avatar_url": "Chatter.png", "file_name": "chat-1"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.get_json()), 3)
        self.assertEqual(response.get_json()[2]["mes"], "Hello back")

        response = self.client.post(
            "/api/chats/search",
            json={"avatar_url": "Chatter.png", "query": "hello"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        results = response.get_json()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["message_count"], 2)

        response = self.client.post(
            "/api/chats/rename",
            json={"avatar_url": "Chatter.png", "original_file": "chat-1.jsonl", "renamed_file": "chat-renamed.jsonl"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue((self._user_dir() / "chats" / "Chatter" / "chat-renamed.jsonl").exists())

    def test_groups_crud(self):
        response = self.client.post("/api/groups/create", json={"name": "Party"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        group = response.get_json()
        self.assertEqual(group["name"], "Party")
        self.assertTrue(group["id"])

        group["name"] = "Renamed Party"
        response = self.client.post("/api/groups/edit", json=group, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"ok": True})

        response = self.client.post("/api/groups/all", json={}, headers=self.headers)
        self.assertEqual(len(response.get_json()), 1)
        self.assertEqual(response.get_json()[0]["name"], "Renamed Party")

        group_chat = [
            {"chat_metadata": {}, "user_name": "unused", "character_name": "unused"},
            {"name": "User", "is_user": True, "mes": "g", "extra": {}},
        ]
        response = self.client.post(
            "/api/chats/group/save",
            json={"id": group["id"], "chat": group_chat},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/api/chats/group/get", json={"id": group["id"]}, headers=self.headers)
        self.assertEqual(len(response.get_json()), 2)

        response = self.client.post("/api/groups/delete", json={"id": group["id"]}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertFalse((self._user_dir() / "groups" / f"{group['id']}.json").exists())

    def test_world_info_crud(self):
        entries = {"1": {"uid": 1, "key": ["castle"], "content": "The castle is old.", "enabled": True}}
        response = self.client.post("/api/worldinfo/edit", json={"name": "Lore", "data": {"entries": entries}}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"ok": True})

        response = self.client.post("/api/worldinfo/get", json={"name": "Lore"}, headers=self.headers)
        self.assertEqual(response.get_json()["entries"]["1"]["content"], "The castle is old.")

        response = self.client.post("/api/worldinfo/list", json={}, headers=self.headers)
        self.assertEqual(response.get_json()[0]["name"], "Lore")

        response = self.client.post("/api/worldinfo/delete", json={"name": "Lore"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/api/worldinfo/list", json={}, headers=self.headers)
        self.assertEqual(response.get_json(), [])

    def test_settings_save_get_and_snapshot(self):
        response = self.client.post("/api/settings/save", json={"power_user": {"swipe_auto": True}}, headers=self.headers)
        self.assertEqual(response.get_json(), {"result": "ok"})

        response = self.client.post("/api/settings/get", json={}, headers=self.headers)
        data = response.get_json()
        self.assertIn('"swipe_auto"', data["settings"])

        response = self.client.post("/api/settings/make-snapshot", json={}, headers=self.headers)
        self.assertEqual(response.status_code, 204)
        response = self.client.post("/api/settings/get-snapshots", json={}, headers=self.headers)
        snapshots = response.get_json()
        self.assertEqual(len(snapshots), 1)
        self.assertTrue(snapshots[0]["name"].startswith(f"settings_{self.user_id}_"))

        self.client.post("/api/settings/save", json={"power_user": {}}, headers=self.headers)
        response = self.client.post(
            "/api/settings/restore-snapshot",
            json={"name": snapshots[0]["name"]},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 204)
        response = self.client.post("/api/settings/get", json={}, headers=self.headers)
        self.assertIn('"swipe_auto"', response.get_json()["settings"])

    def test_presets_themes_moving_ui_quick_replies(self):
        response = self.client.post(
            "/api/presets/save",
            json={"apiId": "openai", "name": "Creative", "preset": {"temperature": 0.9}},
            headers=self.headers,
        )
        self.assertEqual(response.get_json(), {"name": "Creative"})
        self.assertTrue((self._user_dir() / "OpenAI Settings" / "Creative.json").exists())

        response = self.client.post("/api/presets/delete", json={"apiId": "openai", "name": "Creative"}, headers=self.headers)
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/api/themes/save", json={"name": "Dark", "colors": {"bg": "#000"}}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue((self._user_dir() / "themes" / "Dark.json").exists())

        response = self.client.post("/api/moving-ui/save", json={"name": "Layout", "panels": []}, headers=self.headers)
        self.assertEqual(response.status_code, 200)

        response = self.client.post("/api/quick-replies/save", json={"name": "QR", "replies": []}, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue((self._user_dir() / "QuickReplies" / "QR.json").exists())

    def test_secrets_flow(self):
        response = self.client.post(
            "/api/secrets/write",
            json={"key": "api_key_openai", "value": "sk-test-123", "label": "Main"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        secret_id = response.get_json()["id"]

        response = self.client.post("/api/secrets/read", json={}, headers=self.headers)
        state = response.get_json()
        self.assertEqual(state["api_key_openai"][0]["label"], "Main")
        self.assertNotEqual(state["api_key_openai"][0]["value"], "sk-test-123")

        response = self.client.post(
            "/api/secrets/find",
            json={"key": "api_key_openai", "id": secret_id},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 403)

        response = self.client.post(
            "/api/secrets/rotate",
            json={"key": "api_key_openai", "id": secret_id},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 204)

        response = self.client.post(
            "/api/secrets/rename",
            json={"key": "api_key_openai", "id": secret_id, "label": "Renamed"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 204)

        response = self.client.post("/api/secrets/delete", json={"key": "api_key_openai", "id": secret_id}, headers=self.headers)
        self.assertEqual(response.status_code, 204)

    def test_requires_jwt(self):
        response = self.client.post("/api/characters/all", json={})
        self.assertEqual(response.status_code, 401)

    def test_path_traversal_blocked(self):
        self.client.post("/api/characters/create", data={"ch_name": "Safe"}, headers=self.headers)
        response = self.client.post(
            "/api/characters/get",
            json={"avatar_url": "../evil.png"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            "/api/chats/get",
            json={"avatar_url": "../../escape.png", "file_name": "x"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse((self.data_root.parent / "escape").exists())


if __name__ == "__main__":
    unittest.main()
