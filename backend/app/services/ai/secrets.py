"""AI provider secret masking helpers.

Mirrors SillyTavern's ``SecretManager._masked_value`` pattern: write accepts
plaintext, GET always returns a masked preview (``*******xxx``).
"""

from __future__ import annotations


def mask_secret(value: str) -> str:
    """Return a masked preview suitable for GET responses.

    Same shape as SillyTavern: 10 chars of asterisks when short,
    ``*******`` + last 3 chars when longer. Empty stays empty.
    """
    if not value:
        return ""
    if len(value) <= 10:
        return "*" * 10
    return "*******" + value[-3:]


def looks_masked(value: str) -> bool:
    """True if *value* looks like the output of :func:`mask_secret`.

    Used by PUT handlers to detect "admin didn't change the key": when the
    submitted value equals the masked preview, we keep the existing stored
    value instead of writing stars back.
    """
    if not value:
        return False
    if value == "*" * 10:
        return True
    return value.startswith("*******") and len(value) == 10
