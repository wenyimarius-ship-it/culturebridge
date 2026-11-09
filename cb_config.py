"""Classify configuration problems without exposing configuration values."""
import base64
import json
from urllib.parse import urlsplit


def configuration_issue(url, key):
    if not isinstance(url, str) or not isinstance(key, str):
        return "invalid_configuration"
    try:
        u = urlsplit(url)
        if u.scheme != "https" or u.hostname != "crgfsrfxnwyjcjgmvpjr.supabase.co" or u.path not in ("", "/") or u.query or u.fragment or u.username or u.password or url != url.strip():
            return "invalid_url"
    except ValueError:
        return "invalid_url"
    if key.startswith("sb_secret_") and key == key.strip():
        return None
    if key.startswith("eyJ"):
        try:
            part = key.split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
            if claims.get("role") == "service_role":
                return None
        except (ValueError, IndexError):
            pass
    return "invalid_server_key"
