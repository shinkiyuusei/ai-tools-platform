"""URL join helpers for AI provider endpoints."""

def join_url(base: str, path: str) -> str:
    """Join a provider base URL with a path like ``/models``.

    ``urljoin`` alone misbehaves when ``base`` ends without a slash and
    ``path`` starts with one — it treats the last segment as a file and
    drops it. We normalise so ``"https://api.x.com/v1"`` + ``"/models"``
    yields ``"https://api.x.com/v1/models"``.
    """
    if not base:
        return path
    if not path:
        return base
    if base.endswith("/"):
        return base + path.lstrip("/")
    if path.startswith("/"):
        return base + path
    return base + "/" + path
