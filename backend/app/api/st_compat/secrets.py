"""SillyTavern-compatible /api/secrets endpoints."""

from __future__ import annotations

from pathlib import Path

from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from .helpers import get_jwt_user_id, get_user_dirs, parse_json_safe, uuid4_str, write_json_file

secrets_bp = Blueprint("st_compat_secrets", __name__, url_prefix="/secrets")


SECRET_KEYS = {
    "_MIGRATED": "_migrated",
    "HORDE": "api_key_horde",
    "MANCER": "api_key_mancer",
    "VLLM": "api_key_vllm",
    "APHRODITE": "api_key_aphrodite",
    "TABBY": "api_key_tabby",
    "OPENAI": "api_key_openai",
    "NOVEL": "api_key_novel",
    "CLAUDE": "api_key_claude",
    "DEEPL": "deepl",
    "LIBRE": "libre",
    "LIBRE_URL": "libre_url",
    "LINGVA_URL": "lingva_url",
    "OPENROUTER": "api_key_openrouter",
    "AI21": "api_key_ai21",
    "ONERING_URL": "oneringtranslator_url",
    "DEEPLX_URL": "deeplx_url",
    "MAKERSUITE": "api_key_makersuite",
    "VERTEXAI": "api_key_vertexai",
    "SERPAPI": "api_key_serpapi",
    "TOGETHERAI": "api_key_togetherai",
    "MISTRALAI": "api_key_mistralai",
    "CUSTOM": "api_key_custom",
    "OOBA": "api_key_ooba",
    "INFERMATICAI": "api_key_infermaticai",
    "DREAMGEN": "api_key_dreamgen",
    "NOMICAI": "api_key_nomicai",
    "KOBOLDCPP": "api_key_koboldcpp",
    "LLAMACPP": "api_key_llamacpp",
    "COHERE": "api_key_cohere",
    "PERPLEXITY": "api_key_perplexity",
    "GROQ": "api_key_groq",
    "AZURE_TTS": "api_key_azure_tts",
    "FEATHERLESS": "api_key_featherless",
    "HUGGINGFACE": "api_key_huggingface",
    "STABILITY": "api_key_stability",
    "CUSTOM_OPENAI_TTS": "api_key_custom_openai_tts",
    "TAVILY": "api_key_tavily",
    "CHUTES": "api_key_chutes",
    "ELECTRONHUB": "api_key_electronhub",
    "NANOGPT": "api_key_nanogpt",
    "BFL": "api_key_bfl",
    "COMFY_RUNPOD": "api_key_comfy_runpod",
    "FALAI": "api_key_falai",
    "GENERIC": "api_key_generic",
    "DEEPSEEK": "api_key_deepseek",
    "SERPER": "api_key_serper",
    "AIMLAPI": "api_key_aimlapi",
    "XAI": "api_key_xai",
    "FIREWORKS": "api_key_fireworks",
    "VERTEXAI_SERVICE_ACCOUNT": "vertexai_service_account_json",
    "MINIMAX": "api_key_minimax",
    "MINIMAX_GROUP_ID": "minimax_group_id",
    "MOONSHOT": "api_key_moonshot",
    "COMETAPI": "api_key_cometapi",
    "AZURE_OPENAI": "api_key_azure_openai",
    "ZAI": "api_key_zai",
    "SILICONFLOW": "api_key_siliconflow",
    "ELEVENLABS": "api_key_elevenlabs",
    "POLLINATIONS": "api_key_pollinations",
    "VOLCENGINE_APP_ID": "volcengine_app_id",
    "VOLCENGINE_ACCESS_KEY": "volcengine_access_key",
    "WORKERS_AI": "api_key_workers_ai",
}

EXPORTABLE_KEYS = {
    SECRET_KEYS["LIBRE_URL"],
    SECRET_KEYS["LINGVA_URL"],
    SECRET_KEYS["ONERING_URL"],
    SECRET_KEYS["DEEPLX_URL"],
}


def _request_body() -> dict:
    from flask import request

    body = request.get_json(silent=True) or {}
    return body if isinstance(body, dict) else {}


class SecretManager:
    def __init__(self, secrets_path: Path):
        self.secrets_path = secrets_path

    def _read(self):
        if not self.secrets_path.exists():
            return {}
        data = parse_json_safe(self.secrets_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}

    def _write(self, secrets: dict):
        write_json_file(self.secrets_path, secrets)

    def _masked_value(self, value: str, key: str, allow_exposure: bool) -> str:
        if allow_exposure or key in EXPORTABLE_KEYS:
            return value
        if len(value) <= 10:
            return "*" * 10
        return "*******" + value[-3:]

    def write_secret(self, key: str, value: str, label: str = "Unlabeled") -> str:
        secrets = self._read()
        if not isinstance(secrets.get(key), list):
            secrets[key] = []
        for secret in secrets[key]:
            secret["active"] = False
        secret = {"id": uuid4_str(), "value": value, "label": label, "active": True}
        secrets[key].append(secret)
        self._write(secrets)
        return secret["id"]

    def delete_secret(self, key: str, secret_id: str | None = None):
        secrets = self._read()
        values = secrets.get(key)
        if not isinstance(values, list):
            return
        target_index = next(
            (i for i, secret in enumerate(values) if (secret_id and secret.get("id") == secret_id) or (not secret_id and secret.get("active"))),
            -1,
        )
        if target_index != -1:
            values.pop(target_index)
        if values and not any(secret.get("active") for secret in values):
            values[0]["active"] = True
        if not values:
            secrets.pop(key, None)
        self._write(secrets)

    def read_secret(self, key: str, secret_id: str | None = None) -> str:
        secrets = self._read()
        values = secrets.get(key)
        if isinstance(values, list) and values:
            for secret in values:
                if (secret_id and secret.get("id") == secret_id) or (not secret_id and secret.get("active")):
                    return secret.get("value") or ""
        return ""

    def rotate_secret(self, key: str, secret_id: str):
        secrets = self._read()
        values = secrets.get(key)
        if not isinstance(values, list):
            return
        target = next((secret for secret in values if secret.get("id") == secret_id), None)
        if target is None:
            return
        for secret in values:
            secret["active"] = False
        target["active"] = True
        self._write(secrets)

    def rename_secret(self, key: str, secret_id: str, label: str):
        secrets = self._read()
        values = secrets.get(key)
        if not isinstance(values, list):
            return
        target = next((secret for secret in values if secret.get("id") == secret_id), None)
        if target is not None:
            target["label"] = label
            self._write(secrets)

    def get_secret_state(self, allow_exposure: bool):
        secrets = self._read()
        state = {}
        for value in SECRET_KEYS.values():
            if value == SECRET_KEYS["_MIGRATED"]:
                continue
            values = secrets.get(value)
            if isinstance(values, list) and values:
                state[value] = [
                    {
                        "id": secret.get("id"),
                        "value": self._masked_value(secret.get("value") or "", value, allow_exposure),
                        "label": secret.get("label"),
                        "active": secret.get("active"),
                    }
                    for secret in values
                ]
            else:
                state[value] = None
        return state


def _allow_keys_exposure() -> bool:
    from flask import current_app

    return bool(current_app.config.get("ST_COMPAT_ALLOW_KEYS_EXPOSURE", False))


@secrets_bp.post("/write")
@jwt_required()
def write_secret():
    body = _request_body()
    key = body.get("key")
    value = body.get("value")
    if not key or not isinstance(value, str):
        return ("Invalid key or value", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    manager = SecretManager(dirs["root"] / "secrets.json")
    secret_id = manager.write_secret(str(key), value, str(body.get("label") or "Unlabeled"))
    return jsonify({"id": secret_id})


@secrets_bp.post("/read")
@jwt_required()
def read_secret():
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    manager = SecretManager(dirs["root"] / "secrets.json")
    return jsonify(manager.get_secret_state(_allow_keys_exposure()))


@secrets_bp.post("/view")
@jwt_required()
def view_secrets():
    if not _allow_keys_exposure():
        return ("", 403)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    path = dirs["root"] / "secrets.json"
    if not path.exists():
        return ("", 404)
    return jsonify(parse_json_safe(path.read_text(encoding="utf-8")) or {})


@secrets_bp.post("/find")
@jwt_required()
def find_secret():
    body = _request_body()
    key = body.get("key")
    if not key:
        return ("Key is required", 400)
    if not _allow_keys_exposure() and str(key) not in EXPORTABLE_KEYS:
        return ("", 403)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    manager = SecretManager(dirs["root"] / "secrets.json")
    state = manager.get_secret_state(_allow_keys_exposure())
    if not state.get(str(key)):
        return ("", 404)
    return jsonify({"value": manager.read_secret(str(key), body.get("id"))})


@secrets_bp.post("/delete")
@jwt_required()
def delete_secret():
    body = _request_body()
    key = body.get("key")
    if not key:
        return ("Key and ID are required", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    SecretManager(dirs["root"] / "secrets.json").delete_secret(str(key), body.get("id"))
    return ("", 204)


@secrets_bp.post("/rotate")
@jwt_required()
def rotate_secret():
    body = _request_body()
    key = body.get("key")
    secret_id = body.get("id")
    if not key or not secret_id:
        return ("Key and ID are required", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    SecretManager(dirs["root"] / "secrets.json").rotate_secret(str(key), str(secret_id))
    return ("", 204)


@secrets_bp.post("/rename")
@jwt_required()
def rename_secret():
    body = _request_body()
    key = body.get("key")
    secret_id = body.get("id")
    label = body.get("label")
    if not key or not secret_id or not label:
        return ("Key, ID, and label are required", 400)
    user_id = get_jwt_user_id()
    dirs = get_user_dirs(user_id)
    SecretManager(dirs["root"] / "secrets.json").rename_secret(str(key), str(secret_id), str(label))
    return ("", 204)


@secrets_bp.post("/settings")
@jwt_required()
def secrets_settings():
    return jsonify({"allowKeysExposure": _allow_keys_exposure()})
