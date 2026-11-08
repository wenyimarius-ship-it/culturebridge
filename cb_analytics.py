"""Explicit aggregate events only; never include posts, comments, versions or recovery codes."""
import json
from pathlib import Path

EVENTS = {"generation_saved", "feedback_saved", "review_saved"}
CONFIG = json.loads((Path(__file__).parent / "posthog_config.json").read_text())


def payload_for(event, traffic="live"):
    if event not in EVENTS or traffic not in {"live", "test"}:
        return None
    return {
        "api_key": CONFIG["project_token"],
        "event": "culturebridge_" + event,
        "properties": {
            "distinct_id": "ember-culturebridge-aggregate",
            "site": "culturebridge", "traffic": traffic, "storage": "supabase",
            "$process_person_profile": False, "$geoip_disable": True,
        },
    }


def track(event, storage_kind, traffic="live", sender=None):
    if storage_kind != "supabase":
        return False
    payload = payload_for(event, traffic)
    if payload is None:
        return False
    try:
        if sender is None:
            import requests
            sender = requests.post
        response = sender(CONFIG["api_host"] + "/capture/", json=payload, timeout=1.5)
        return response.status_code < 300
    except Exception:
        return False
