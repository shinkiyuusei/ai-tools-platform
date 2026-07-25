"""
Client extension management service.

Extensions are stored as rows in ``t_extension`` with their manifest (YAML as JSON)
and per-user config in ``t_extension_config``.
"""

from ...utils.mysql import query_one, query_all, execute


# ---------------------------------------------------------------------------
#  CRUD
# ---------------------------------------------------------------------------

def list_installed(status: str | None = "active") -> list[dict]:
    """Return installed extensions.  Pass ``status=None`` to return all."""
    if status:
        rows = query_all(
            "SELECT id, manifest, status, install_time FROM t_extension WHERE status = %s ORDER BY install_time",
            (status,),
        )
    else:
        rows = query_all(
            "SELECT id, manifest, status, install_time FROM t_extension ORDER BY install_time"
        )
    return rows or []


def get_extension(ext_id: str) -> dict | None:
    """Return a single extension row or None."""
    return query_one(
        "SELECT id, manifest, status, install_time FROM t_extension WHERE id = %s",
        (ext_id,),
    )


def install_extension(ext_id: str, manifest: dict, status: str = "active") -> None:
    """Insert or replace an extension record."""
    import json
    execute(
        """INSERT INTO t_extension (id, manifest, status)
           VALUES (%s, %s, %s)
           ON DUPLICATE KEY UPDATE manifest = VALUES(manifest), status = VALUES(status)""",
        (ext_id, json.dumps(manifest, ensure_ascii=False), status),
    )


def uninstall_extension(ext_id: str) -> None:
    """Remove an extension and its user configs."""
    execute("DELETE FROM t_extension WHERE id = %s", (ext_id,))
    execute("DELETE FROM t_extension_config WHERE extension_id = %s", (ext_id,))


def update_status(ext_id: str, status: str) -> None:
    """Change extension status (admin action)."""
    execute("UPDATE t_extension SET status = %s WHERE id = %s", (status, ext_id))


# ---------------------------------------------------------------------------
#  Per-user config
# ---------------------------------------------------------------------------

def get_user_config(ext_id: str, user_id: int) -> dict:
    """Return user-specific config for an extension, or ``{}``."""
    import json
    row = query_one(
        "SELECT config FROM t_extension_config WHERE extension_id = %s AND user_id = %s",
        (ext_id, user_id),
    )
    if not row:
        return {}
    config = row.get("config", {})
    if isinstance(config, str):
        try:
            config = json.loads(config)
        except (json.JSONDecodeError, TypeError):
            config = {}
    return config


def set_user_config(ext_id: str, user_id: int, config: dict) -> None:
    """Upsert per-user extension config."""
    import json
    execute(
        """INSERT INTO t_extension_config (extension_id, user_id, config)
           VALUES (%s, %s, %s)
           ON DUPLICATE KEY UPDATE config = VALUES(config)""",
        (ext_id, user_id, json.dumps(config, ensure_ascii=False)),
    )
