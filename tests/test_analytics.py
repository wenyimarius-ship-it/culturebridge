from cb_analytics import payload_for, track


def test_only_enumerated_events_and_aggregate_fields():
    assert payload_for("feedback body") is None
    p = payload_for("feedback_saved", "test")
    assert set(p["properties"]) == {"distinct_id", "site", "traffic", "storage", "$process_person_profile", "$geoip_disable"}
    assert p["properties"]["traffic"] == "test"
    assert "post_version" not in str(p) and "comment" not in p["properties"]


def test_local_store_and_failed_analytics_never_claim_delivery():
    calls = []
    def sender(*a, **kw):
        calls.append(kw)
        raise RuntimeError("unavailable")
    assert track("feedback_saved", "local", sender=sender) is False
    assert not calls
    assert track("feedback_saved", "supabase", sender=sender) is False
    assert len(calls) == 1 and calls[0]["timeout"] == 1.5
