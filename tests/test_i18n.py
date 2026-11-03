import re
import string
from pathlib import Path

import i18n

APP = Path(__file__).resolve().parent.parent / "app.py"
FMT = string.Formatter()


def fields(text):
    return {f for _, f, _, _ in FMT.parse(text) if f}


def test_languages_have_identical_keys_and_placeholders():
    zh, en = i18n.STRINGS["zh"], i18n.STRINGS["en"]
    assert set(zh) == set(en)
    for key in zh:
        assert fields(zh[key]) == fields(en[key]), key


def test_every_literal_key_used_by_app_exists():
    src = APP.read_text(encoding="utf-8")
    used = set(re.findall(r'\bt\(\s*"([a-z0-9_]+)"\s*[,)]', src))
    assert used, "no t() calls found"
    assert used <= set(i18n.STRINGS["zh"]), used - set(i18n.STRINGS["zh"])


def test_dynamic_keys_exist():
    zh = i18n.STRINGS["zh"]
    for key in ["err_auth", "err_rate", "err_timeout", "err_conn", "err_other",
                "err_empty", "status_pending", "status_partial", "status_verified",
                "scope_all", "scope_current", "admin_feedback", "admin_reviews"]:
        assert key in zh


def test_translate_formats_falls_back_and_records_missing():
    assert i18n.translate("en", "words_ok", n=5, limit=100) == "About 5 words (target: under 100)"
    assert "5" in i18n.translate("fr", "words_ok", n=5, limit=100)   # 未知语言退回中文
    assert i18n.translate("zh", "nope") == "nope" and "nope" in i18n.MISSING
    assert "{n}" in i18n.translate("zh", "words_ok")                 # 缺参数时不抛错
