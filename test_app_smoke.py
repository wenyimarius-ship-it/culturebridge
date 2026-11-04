"""把 app.py 当作脚本整体执行（Streamlit / OpenAI 用替身），检查完整数据流。"""

import csv
import shutil
import sys
from pathlib import Path

import pytest

import cb_core as core
from cb_store import LocalStore
from i18n import translate
from streamlit_stub import FakeOpenAIModule, FakeStreamlit

APP_SRC = Path(__file__).resolve().parent.parent / "app.py"

RAW = """【English Post】
Ever noticed how a pause can feel bigger than a meeting? What would you slow down for?

【中文翻译】
你有没有发现，一次停顿比一场会议更有分量？

【文化表达思路】
避免了刻板印象，用具体场景切入。

【需要核实的内容】
- 功夫茶的说法需要核实
- “待客之道”的表述需要核实
"""

REFINED = """【English Post】
A pause can outweigh a meeting. What would you slow down for?

【中文翻译】
停顿有时比会议更有分量。

【文化表达思路】
更短。

【需要核实的内容】
- 无
"""


def zh(key, **kw):
    return translate("zh", key, **kw)


def en(key, **kw):
    return translate("en", key, **kw)


@pytest.fixture
def h(tmp_path, monkeypatch):
    for name in ("DEEPSEEK_API_KEY", "OPENAI_API_KEY", "ADMIN_KEY", "SUPABASE_URL",
                 "SUPABASE_KEY", "DAILY_LIMIT", "SESSION_LIMIT", "APP_URL",
                 "CULTUREBRIDGE_MODEL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    app = tmp_path / "app.py"
    shutil.copy(APP_SRC, app)

    st = FakeStreamlit(app)
    openai = FakeOpenAIModule()
    monkeypatch.setitem(sys.modules, "streamlit", st)
    monkeypatch.setitem(sys.modules, "streamlit.components", st.components)
    monkeypatch.setitem(sys.modules, "streamlit.components.v1", st._components_v1)
    monkeypatch.setitem(sys.modules, "openai", openai)

    st.openai = openai
    st.store = LocalStore(tmp_path)
    st.tmp = tmp_path
    return st


def rows(path):
    if not path.exists():
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def generate(h, reply=RAW):
    h.openai.responses.append(reply)
    h.run(clicks=[zh("generate_btn")])


# ---------------------------------------------------------------

@pytest.mark.parametrize("lang", ["zh", "en"])
def test_initial_render_has_no_errors(h, lang):
    h.session_state["ui_lang"] = lang
    h.run()
    assert not h.out["error"]
    assert translate(lang, "post_empty") in h.out["info"]
    assert any("15/15" in c and "200/200" in c for c in h.out["caption"])


def test_generate_populates_everything_and_logs(h):
    generate(h)
    ss = h.session_state
    assert not h.out["error"], h.out["error"]
    assert ss["cb_post_edit"].startswith("Ever noticed")
    assert ss["cb_count"] == 1 and core.valid_version(ss["cb_version"])

    log = rows(h.tmp / "generations.csv")
    assert len(log) == 1 and log[0]["kind"] == "generate"
    assert log[0]["version"] == ss["cb_version"]

    prompt = h.openai.calls[0]["messages"][1]["content"]
    assert "Instagram" in prompt and "Curious" in prompt
    assert h.openai.calls[0]["messages"][0]["content"] == core.SYSTEM_PROMPT

    assert any('class="post-card"' in m and "Ever noticed" in m for m in h.out["markdown"])
    assert h.out["components_html"], "copy button should render"
    assert any("1/2" not in c for c in h.out["caption"])


def test_post_is_html_escaped_in_card(h):
    generate(h, RAW.replace("Ever noticed", "<script>alert(1)</script> Ever noticed"))
    card = [m for m in h.out["markdown"] if 'class="post-card"' in m][0]
    assert "<script>alert(1)</script>" not in card
    assert "&lt;script&gt;" in card


def test_refine_button_uses_edited_text_and_logs_refine(h):
    generate(h)
    h.inputs["cb_post_edit"] = "My hand-edited post about tea."
    h.openai.responses.append(REFINED)
    h.run(clicks=["refine_shorter"])

    assert not h.out["error"], h.out["error"]
    prompt = h.openai.calls[1]["messages"][1]["content"]
    assert "My hand-edited post about tea." in prompt        # 基于手动修改后的文本
    assert core.REFINE_PRESETS["shorter"]["instruction"] in prompt
    assert "<post>" in prompt

    ss = h.session_state
    assert ss["cb_post_edit"].startswith("A pause can outweigh")
    assert ss["cb_count"] == 2
    assert [r["kind"] for r in rows(h.tmp / "generations.csv")] == ["generate", "refine"]


def test_custom_refine_instruction(h):
    generate(h)
    h.inputs["cb_custom_instruction"] = "Open with an office scene"
    h.openai.responses.append(REFINED)
    h.run(clicks=["refine_custom_btn"])
    assert "Open with an office scene" in h.openai.calls[1]["messages"][1]["content"]


def test_share_link_after_manual_edit_commits_new_version(h):
    generate(h)
    first = h.session_state["cb_version"]
    h.inputs["cb_post_edit"] = "Edited by a human."
    h.run(clicks=["share_btn"])

    ss = h.session_state
    assert ss["cb_share_version"] != first and ss["cb_version"] == ss["cb_share_version"]
    assert h.store.get_post(ss["cb_share_version"])["post"] == "Edited by a human."
    assert [r["kind"] for r in rows(h.tmp / "generations.csv")] == ["generate", "edit"]
    assert any(f"/?t={ss['cb_share_version']}" in c for c in h.out["code"])
    assert zh("share_local_warning") in h.out["caption"]


def test_share_link_without_edit_reuses_version(h):
    generate(h)
    v = h.session_state["cb_version"]
    h.run(clicks=["share_btn"])
    assert h.session_state["cb_share_version"] == v
    assert len(rows(h.tmp / "generations.csv")) == 1


def test_tester_page_shows_english_post_and_saves_feedback(h):
    generate(h)
    h.run(clicks=["share_btn"])
    version = h.session_state["cb_share_version"]

    h.new_visitor()                       # 全新访客，带测试链接进入
    h.query_params["t"] = version
    h.inputs[en("q_interest")] = 5
    h.inputs[en("consent")] = True
    h.run(clicks=[en("submit_feedback")])

    assert not h.out["error"], h.out["error"]
    assert h.session_state["ui_lang"] == "en"
    assert any("Ever noticed" in m for m in h.out["markdown"])
    assert en("feedback_thanks") in h.out["success"]

    saved = rows(h.tmp / "audience_feedback.csv")
    assert len(saved) == 1
    assert saved[0]["post_version"] == version and saved[0]["interest"] == "5"
    assert saved[0]["lang"] == "en" and saved[0]["post_text"].startswith("Ever noticed")


def test_tester_feedback_requires_consent(h):
    generate(h)
    version = h.session_state["cb_version"]
    h.new_visitor()
    h.query_params["t"] = version
    h.run(clicks=[en("submit_feedback")])
    assert en("consent_required") in h.out["error"]
    assert not (h.tmp / "audience_feedback.csv").exists()


def test_tester_page_rejects_bad_and_unknown_links(h):
    h.query_params["t"] = "bad;link"
    h.run()
    assert en("tester_bad_link") in h.out["error"]

    h.new_visitor()
    h.query_params["t"] = "20260101-000000-abcd"
    h.run()
    assert en("tester_not_found") in h.out["error"]


def test_in_page_feedback_targets_edited_version(h):
    generate(h)
    h.inputs["cb_post_edit"] = "Edited for in-person test."
    h.inputs[zh("consent")] = True
    h.run(clicks=[zh("submit_feedback")])
    saved = rows(h.tmp / "audience_feedback.csv")
    assert saved[0]["post_text"] == "Edited for in-person test."
    assert h.store.get_post(saved[0]["post_version"])["post"] == "Edited for in-person test."


def test_review_record_lists_confirmed_and_open_claims(h):
    generate(h)
    v = h.session_state["cb_base"]
    h.inputs[f"cb_claim_{v}_0"] = True
    h.inputs[f"cb_checked_{v}"] = ["Smithsonian: Tea Culture in China"]
    h.inputs[f"cb_verification_{v}"] = "partial"
    h.run(clicks=[zh("save_review_btn")])

    assert zh("review_saved") in h.out["success"]
    row = rows(h.tmp / "fact_review_log.csv")[0]
    assert row["claims_confirmed"] == "功夫茶的说法需要核实"
    assert row["claims_open"] == "“待客之道”的表述需要核实"
    assert row["verification_status"] == "partial"
    assert "asia.si.edu" in row["checked_sources"]


def test_verified_with_open_claims_warns(h):
    generate(h)
    v = h.session_state["cb_base"]
    h.inputs[f"cb_verification_{v}"] = "verified"
    h.run()
    assert zh("verify_open_claims", n=2) in h.out["warning"]


def test_review_state_resets_for_new_version(h):
    generate(h)
    v1 = h.session_state["cb_base"]
    h.inputs[f"cb_claim_{v1}_0"] = True
    h.openai.responses.append(RAW)
    h.run(clicks=[zh("generate_btn")])
    v2 = h.session_state["cb_base"]
    assert v1 != v2
    h.inputs = {}
    h.run()
    assert not h.session_state.get(f"cb_claim_{v2}_0")


@pytest.mark.parametrize("exc_name,key", [
    ("AuthenticationError", "err_auth"),
    ("RateLimitError", "err_rate"),
    ("APITimeoutError", "err_timeout"),
    ("APIConnectionError", "err_conn"),
])
def test_model_errors_show_friendly_message_and_cost_nothing(h, exc_name, key):
    h.openai.responses.append(getattr(h.openai, exc_name)("boom secret-token"))
    h.run(clicks=[zh("generate_btn")])
    assert zh(key) in h.out["error"]
    assert all("secret-token" not in e for e in h.out["error"])
    assert h.session_state.get("cb_count", 0) == 0
    assert rows(h.tmp / "generations.csv") == []


def test_empty_model_reply_and_unknown_error(h):
    h.openai.responses.append("")
    h.run(clicks=[zh("generate_btn")])
    assert zh("err_empty") in h.out["error"]

    h.openai.responses.append(ValueError("weird"))
    h.run(clicks=[zh("generate_btn")])
    assert zh("err_other") in h.out["error"]


def test_missing_api_key_message(h, monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY")
    h.run(clicks=[zh("generate_btn")])
    assert zh("no_api_key") in h.out["error"]
    assert h.openai.calls == []


def test_daily_limit_blocks_further_generation(h, monkeypatch):
    monkeypatch.setenv("DAILY_LIMIT", "1")
    generate(h)
    h.openai.responses.append(RAW)
    h.run(clicks=[zh("generate_btn")])
    assert len(h.openai.calls) == 1                       # 第二次没有调用模型
    assert zh("quota_daily_used") in h.out["warning"]


def test_session_limit_blocks_further_generation(h, monkeypatch):
    monkeypatch.setenv("SESSION_LIMIT", "1")
    generate(h)
    h.openai.responses.append(RAW)
    h.run(clicks=[zh("generate_btn")])
    assert len(h.openai.calls) == 1
    assert zh("quota_session_used") in h.out["warning"]


def test_overview_shows_metrics_and_admin_gate(h, monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "s3cret")
    generate(h)
    v = h.session_state["cb_version"]
    h.inputs[zh("consent")] = True
    h.inputs[zh("q_interest")] = 4
    h.run(clicks=[zh("submit_feedback")])
    h.inputs = {}
    h.run()
    assert (zh("metric_count"), 1) in h.out["metric"]
    assert (zh("metric_interest"), "4.0 / 5") in h.out["metric"]
    assert zh("sample_tiny", n=1) in h.out["caption"]
    assert h.out["download"] == []                          # 未输入口令，不展示

    h.inputs[zh("admin_password")] = "wrong"
    h.run()
    assert zh("admin_wrong") in h.out["error"] and h.out["download"] == []

    h.inputs[zh("admin_password")] = "s3cret"
    h.run()
    names = [label for label, _ in h.out["download"]]
    assert zh("admin_download", name="feedback.csv") in names
    assert v in h.out["download"][0][1].decode("utf-8-sig")


def test_admin_not_configured_hides_data(h):
    generate(h)
    h.run()
    assert zh("admin_not_set") in h.out["caption"]
    assert h.out["download"] == []


def test_review_is_saved_under_committed_edited_version_and_ticks_survive(h):
    generate(h)
    base = h.session_state["cb_base"]
    h.inputs[f"cb_claim_{base}_0"] = True
    h.inputs["cb_post_edit"] = "Edited before review is saved."
    h.run(clicks=[zh("save_review_btn")])

    row = rows(h.tmp / "fact_review_log.csv")[0]
    saved_version = row["post_version"]
    assert row["post_text"] == "Edited before review is saved."
    assert h.store.get_post(saved_version)["post"] == "Edited before review is saved."
    assert saved_version != base                           # 已落成新的“修改”版本

    assert h.session_state["cb_base"] == base               # 控件 key 不变
    assert h.session_state[f"cb_claim_{base}_0"] is True    # 已勾选的条目没有丢
    h.run(clicks=["share_btn"])
    assert h.session_state[f"cb_claim_{base}_0"] is True


def test_overlong_model_reply_is_truncated(h):
    generate(h, "【English Post】\n" + "tea " * 2000 + "\n【中文翻译】\n无")
    assert len(h.session_state["cb_post_edit"]) <= 1200
    assert not h.out["error"]
