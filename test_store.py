import csv

import pytest

import cb_core as core
from cb_store import LocalStore, StoreError, SupabaseStore, make_store, today_prefix


# ------------------------- LocalStore -------------------------

def test_local_roundtrip_and_post_lookup(tmp_path):
    s = LocalStore(tmp_path)
    s.log_generation({"version": "v1-aaaaaa", "topic": "ritual", "platform": "instagram",
                      "style": "curious", "kind": "generate", "model": "m", "post": "=Hello tea"})
    s.log_generation({"version": "v2-bbbbbb", "kind": "edit", "post": "Second"})
    got = s.get_post("v1-aaaaaa")
    assert got["post"] == "=Hello tea"          # 原文不被改写
    assert s.get_post("missing") is None


def test_local_feedback_escapes_formulas_but_keeps_post_text(tmp_path):
    s = LocalStore(tmp_path)
    s.save_feedback({"post_version": "v1-aaaaaa", "post_text": "+raw post", "interest": 4,
                     "understanding": 5, "learn_more": 3, "confusing_part": "=cmd()", "comment": "ok"})
    row = s.list_feedback()[0]
    assert row["confusing_part"] == "'=cmd()"
    assert row["post_text"] == "+raw post"
    assert s.list_feedback("other") == []
    assert len(s.list_feedback("v1-aaaaaa")) == 1


def test_local_reuses_existing_header(tmp_path):
    f = tmp_path / "audience_feedback.csv"
    f.write_text("timestamp,post_version,interest,understanding,learn_more,confusing_part,comment\n",
                 encoding="utf-8-sig")
    LocalStore(tmp_path).save_feedback({"post_version": "v", "topic": "x", "interest": 1,
                                        "understanding": 2, "learn_more": 3})
    with open(f, encoding="utf-8-sig", newline="") as fh:
        row = next(csv.DictReader(fh))
    assert "topic" not in row and row["interest"] == "1" and row["timestamp"]


def test_local_count_today_counts_only_generate_and_refine(tmp_path):
    s = LocalStore(tmp_path)
    s.log_generation({"version": "a-aaaaaa", "kind": "generate", "post": "x"})
    s.log_generation({"version": "b-bbbbbb", "kind": "refine", "post": "x"})
    s.log_generation({"version": "c-cccccc", "kind": "edit", "post": "x"})
    s.log_generation({"version": "d-dddddd", "kind": "generate", "post": "x",
                      "created_at": "2001-01-01T00:00:00+00:00"})
    assert s.count_today() == 2
    assert today_prefix()


def test_local_write_failure_raises_store_error(tmp_path):
    s = LocalStore(tmp_path / "does-not-exist")
    with pytest.raises(StoreError):
        s.save_feedback({"post_version": "v"})


def test_make_store_picks_backend(tmp_path):
    assert make_store(tmp_path).kind == "local"
    assert make_store(tmp_path, "https://x.supabase.co", None).kind == "local"
    assert make_store(tmp_path, "https://x.supabase.co", "sb_secret_1",
                      session=object()).kind == "supabase"


# ------------------------- SupabaseStore -------------------------

class FakeResponse:
    def __init__(self, status=200, body=None, headers=None):
        self.status_code = status
        self._body = body if body is not None else []
        self.headers = headers or {}

    def json(self):
        return self._body


class FakeSession:
    def __init__(self, response=None, exc=None):
        self.calls = []
        self.response = response or FakeResponse()
        self.exc = exc

    def request(self, method, url, **kw):
        self.calls.append((method, url, kw))
        if self.exc:
            raise self.exc
        return self.response


def test_supabase_insert_sends_expected_request():
    sess = FakeSession(FakeResponse(201))
    s = SupabaseStore("https://abc.supabase.co/", "sb_secret_key", session=sess)
    s.save_feedback({"post_version": "v1", "interest": 3})
    method, url, kw = sess.calls[0]
    assert method == "POST" and url == "https://abc.supabase.co/rest/v1/feedback"
    assert kw["json"]["post_version"] == "v1"
    assert kw["headers"]["apikey"] == "sb_secret_key"
    assert "Authorization" not in kw["headers"]       # 新式密钥不放 Bearer
    assert kw["headers"]["Prefer"] == "return=minimal"
    assert kw["timeout"]


def test_supabase_legacy_jwt_key_adds_bearer():
    s = SupabaseStore("https://abc.supabase.co", "eyJhbGciOi.x.y", session=FakeSession())
    assert s.headers["Authorization"] == "Bearer eyJhbGciOi.x.y"


def test_supabase_get_post_validates_version_before_querying():
    sess = FakeSession(FakeResponse(200, [{"version": "v", "post": "hi"}]))
    s = SupabaseStore("https://abc.supabase.co", "k", session=sess)
    assert s.get_post("bad;version=eq.1&select=*") is None
    assert sess.calls == []                            # 非法版本号根本不发请求
    assert s.get_post("20261103-045500-a1b2")["post"] == "hi"
    params = sess.calls[0][2]["params"]
    assert params["version"] == "eq.20261103-045500-a1b2" and params["limit"] == 1


def test_supabase_errors_do_not_leak_details():
    s = SupabaseStore("https://abc.supabase.co", "k",
                      session=FakeSession(FakeResponse(401, {"message": "secret detail"})))
    with pytest.raises(StoreError) as e:
        s.save_review({"post_version": "v"})
    assert "secret detail" not in str(e.value) and "401" in str(e.value)

    s2 = SupabaseStore("https://abc.supabase.co", "k",
                       session=FakeSession(exc=ConnectionError("host=10.0.0.1 token=abc")))
    with pytest.raises(StoreError) as e2:
        s2.log_generation({"version": "v"})
    assert "10.0.0.1" not in str(e2.value)


def test_supabase_count_today_reads_content_range():
    sess = FakeSession(FakeResponse(206, [{"id": 1}], {"Content-Range": "0-0/37"}))
    s = SupabaseStore("https://abc.supabase.co", "k", session=sess)
    assert s.count_today() == 37
    kw = sess.calls[0][2]
    assert kw["headers"]["Prefer"] == "count=exact"
    assert kw["params"]["kind"] == "in.(generate,refine)"
    assert kw["params"]["created_at"].startswith("gte.")


def test_supabase_count_today_falls_back_to_body_length():
    sess = FakeSession(FakeResponse(200, [{"id": 1}, {"id": 2}], {}))
    assert SupabaseStore("https://a.supabase.co", "k", session=sess).count_today() == 2


def test_supabase_list_feedback_filters_by_version():
    sess = FakeSession(FakeResponse(200, [{"interest": 5}]))
    s = SupabaseStore("https://abc.supabase.co", "k", session=sess)
    assert s.list_feedback("v1-aaaaaa") == [{"interest": 5}]
    assert sess.calls[0][2]["params"]["post_version"] == "eq.v1-aaaaaa"
    s.list_feedback()
    assert "post_version" not in sess.calls[1][2]["params"]
