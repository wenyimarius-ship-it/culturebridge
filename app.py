import os
import json
import hmac
import html
import inspect
import threading
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from openai import (
    OpenAI,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    RateLimitError,
)

import cb_core as core
from cb_store import make_store
from i18n import translate


# =====================================================
# 1. 基础设置
# =====================================================

st.set_page_config(
    page_title="CultureBridge | 中国茶文化探索 · Tea Culture Explorer",
    page_icon="🍵",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_secret(name, default=None):
    """优先读环境变量，其次读 Streamlit Cloud 的 Secrets。"""
    value = os.getenv(name)
    if value:
        return value
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return value or default


def get_int_secret(name, default):
    try:
        return int(get_secret(name, default))
    except (TypeError, ValueError):
        return default


API_KEY = get_secret("DEEPSEEK_API_KEY") or get_secret("OPENAI_API_KEY")
API_BASE_URL = "https://api.deepseek.com"
MODEL_NAME = get_secret("CULTUREBRIDGE_MODEL", "deepseek-chat")

# 管理员口令：设置后才能在页面里查看原始反馈 / 下载 CSV
ADMIN_KEY = get_secret("ADMIN_KEY")

# Supabase：设置后数据持久保存，否则写本地 CSV（云端重启后会清空）
SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")

# 应用公开网址，用来拼接受众测试链接
APP_URL = get_secret(
    "APP_URL", "https://culturebridge-dwbxqchgzdremscutzk5eh.streamlit.app"
)

# 额度保护：每个访问会话上限 + 全站每日上限
MAX_PER_SESSION = get_int_secret("SESSION_LIMIT", 15)
DAILY_LIMIT = get_int_secret("DAILY_LIMIT", 200)

# 短帖输入框的长度上限（模型偶尔会超长，写入前先截断）
MAX_POST_CHARS = 1200


@st.cache_resource
def get_store():
    return make_store(BASE_DIR, SUPABASE_URL, SUPABASE_KEY)


store = get_store()


# =====================================================
# 2. 内容配置（主题 / 平台 / 风格 / 参考来源）
# =====================================================

ANGLES = {
    "ritual": {
        "zh": "为什么中国泡茶有时像一种仪式？",
        "en": "Why can preparing Chinese tea feel like a ritual?",
        "prompt": "Why can preparing Chinese tea feel like a ritual?",
    },
    "hospitality": {
        "zh": "为什么给客人倒茶能表达待客之道？",
        "en": "How can serving tea express hospitality?",
        "prompt": "How can serving tea express hospitality?",
    },
    "details": {
        "zh": "中国茶文化中有哪些值得探索的细节？",
        "en": "What details make Chinese tea culture worth exploring?",
        "prompt": "What details make Chinese tea culture worth exploring?",
    },
    "connect": {
        "zh": "一杯茶如何让人与人建立联系？",
        "en": "How can sharing tea help people connect?",
        "prompt": "How can sharing tea help people connect?",
    },
    "cuppa": {
        "zh": "喝惯英式茶的人，如何走近不加奶的中国茶？",
        "en": "If you love a British cuppa, how might you explore Chinese "
              "teas drunk without milk?",
        "prompt": "If you love a British cuppa, how might you explore "
                  "Chinese teas that are drunk without milk?",
    },
}

PLATFORMS = {
    "instagram": {
        "zh": "Instagram（图片与短帖）",
        "en": "Instagram (visual posts)",
        "name": "Instagram",
    },
    "linkedin": {
        "zh": "LinkedIn（职业社交）",
        "en": "LinkedIn (professional)",
        "name": "LinkedIn",
    },
}

STYLES = {
    "curious": {"zh": "好奇启发型", "en": "Curious", "name": "Curious"},
    "playful": {"zh": "轻松幽默型", "en": "Playful", "name": "Playful"},
    "reflective": {"zh": "深度思考型", "en": "Reflective", "name": "Reflective"},
}

# 示例参考资料：来源链接不等于具体文案已通过审核
SOURCES = [
    {
        "title": "Smithsonian: Tea Culture in China",
        "url": (
            "https://asia.si.edu/education/educator-resources/"
            "teaching-china-with-the-smithsonian/lesson-plans/"
            "tea-culture-in-china/"
        ),
        "note": {
            "zh": "介绍中国茶文化的历史、社会生活和茶具背景。",
            "en": "History, social life and tea wares in Chinese tea culture.",
        },
    },
    {
        "title": "UNESCO: Traditional tea processing techniques "
                 "and associated social practices in China",
        "url": (
            "https://ich.unesco.org/en/RL/"
            "traditional-tea-processing-techniques-and-associated-"
            "social-practices-in-china-01884"
        ),
        "note": {
            "zh": "介绍中国传统制茶技艺及相关社会实践。",
            "en": "Traditional tea processing techniques and the social "
                  "practices around them.",
        },
    },
    {
        "title": "Smithsonian: Exploring Chinese Teas and Tea Wares",
        "url": (
            "https://asia-archive.si.edu/learn/for-educators/"
            "teaching-china-with-the-smithsonian/videos/"
            "exploring-chinese-teas-and-tea-wares/"
        ),
        "note": {
            "zh": "介绍中国茶、功夫茶及茶具。",
            "en": "Chinese teas, gongfu tea and tea wares.",
        },
    },
]

VERIFY_STATES = ["pending", "partial", "verified"]


# =====================================================
# 3. 语言与页面样式
# =====================================================

tester_version = st.query_params.get("t")

# 受众测试页默认英文；创作者界面默认中文
st.session_state.setdefault("ui_lang", "en" if tester_version else "zh")


def language_selector():
    return st.radio(
        "语言 / Language",
        ["zh", "en"],
        format_func=lambda code: {"zh": "中文", "en": "English"}[code],
        key="ui_lang",
        horizontal=True,
    )


def t(key, **kwargs):
    return translate(st.session_state.get("ui_lang", "zh"), key, **kwargs)


st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 750;
        margin-bottom: 0.2rem;
    }

    .muted {
        color: #8E91A0;
        font-size: 0.9rem;
    }

    .step-label {
        display: inline-block;
        font-size: 0.78rem;
        font-weight: 650;
        letter-spacing: 0.04em;
        color: #C9704F;
        background: rgba(201, 112, 79, 0.12);
        border-radius: 999px;
        padding: 2px 10px;
        margin-bottom: 6px;
    }

    .post-card {
        background: #17191F;
        border: 1px solid #343741;
        border-radius: 16px;
        padding: 22px;
        margin: 10px 0 12px;
        color: #F5F5F7;
    }

    .post-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 18px;
    }

    .post-avatar {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        background: linear-gradient(135deg, #F6B8A8, #D9C8FF);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 23px;
    }

    .post-body {
        font-size: 1rem;
        line-height: 1.85;
        white-space: pre-wrap;
        overflow-wrap: anywhere;
    }

    .post-footer {
        border-top: 1px solid #343741;
        margin-top: 18px;
        padding-top: 12px;
        color: #A6A6B5;
        font-size: 0.82rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# 4. 通用小工具
# =====================================================

def stretch_kwargs(func):
    """让按钮在不同 Streamlit 版本下都能撑满宽度。"""
    try:
        params = inspect.signature(func).parameters
    except (TypeError, ValueError):
        return {}
    if "width" in params:
        return {"width": "stretch"}
    if "use_container_width" in params:
        return {"use_container_width": True}
    return {}


def render_post_card(text):
    """展示社交媒体风格的短帖卡片（正文已转义）。"""
    st.markdown(
        '<div class="post-card">'
        '<div class="post-header">'
        '<div class="post-avatar">🍵</div>'
        '<div><strong>culturebridge.stories</strong><br>'
        '<span class="muted">Tea culture · Cross-cultural stories</span>'
        '</div></div>'
        f'<div class="post-body">{html.escape(text, quote=True)}</div>'
        '<div class="post-footer">♡ Like　　♡ Comment　　↗ Share</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_copy_button(text):
    """用浏览器剪贴板 API 复制英文正文；转义 </ 防止破坏 <script>。"""
    post_json = json.dumps(text).replace("</", "<\\/")
    labels = json.dumps(
        {
            "done": t("copy_done"),
            "hint": t("copy_hint"),
            "fail": t("copy_fail"),
        }
    ).replace("</", "<\\/")

    components.html(
        f"""
        <button id="copy-btn" style="
            width:100%;padding:12px;border:0;border-radius:10px;
            background:#ff4b4b;color:white;font-size:15px;
            font-weight:600;cursor:pointer;">
            {html.escape(t("copy_btn"))}
        </button>
        <div id="copy-status" style="
            margin-top:6px;color:#A6A6B5;font-size:13px;"></div>
        <script>
        const postText = {post_json};
        const labels = {labels};
        const button = document.getElementById("copy-btn");
        const status = document.getElementById("copy-status");

        button.addEventListener("click", async () => {{
            try {{
                await navigator.clipboard.writeText(postText);
                button.innerText = labels.done;
                status.innerText = labels.hint;
            }} catch (e) {{
                status.innerText = labels.fail;
            }}
        }});
        </script>
        """,
        height=78,
    )


# =====================================================
# 5. 额度保护（每会话 + 全站每日）
# =====================================================

def today_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


@st.cache_resource
def _memory_usage():
    return {"date": today_utc(), "count": 0, "lock": threading.Lock()}


def memory_count():
    usage = _memory_usage()
    with usage["lock"]:
        if usage["date"] != today_utc():
            usage["date"] = today_utc()
            usage["count"] = 0
        return usage["count"]


def memory_incr():
    usage = _memory_usage()
    with usage["lock"]:
        if usage["date"] != today_utc():
            usage["date"] = today_utc()
            usage["count"] = 0
        usage["count"] += 1


@st.cache_data(ttl=60, show_spinner=False)
def persisted_today():
    return store.count_today()


def daily_used():
    """取“内存计数”和“存储里的计数”中较大的一个；存储不可用时只看内存。"""
    try:
        persisted = persisted_today()
    except Exception:
        persisted = 0
    return max(memory_count(), persisted)


def quota_state():
    used_session = st.session_state.get("cb_count", 0)
    remaining_session = max(MAX_PER_SESSION - used_session, 0)
    remaining_daily = max(DAILY_LIMIT - daily_used(), 0)
    return remaining_session, remaining_daily


def show_quota(slot):
    remaining_session, remaining_daily = quota_state()
    slot.caption(
        t(
            "quota_line",
            rs=remaining_session,
            ms=MAX_PER_SESSION,
            rd=remaining_daily,
            md=DAILY_LIMIT,
        )
    )


@st.cache_data(ttl=20, show_spinner=False)
def load_feedback():
    return store.list_feedback()


# =====================================================
# 6. 模型调用
# =====================================================

class ModelError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def call_model(user_prompt, temperature=0.7):
    """调用模型，返回原始文本；失败时抛出带错误码的 ModelError。"""
    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE_URL,
        timeout=60.0,
        max_retries=1,
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": core.SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )
    except AuthenticationError as e:
        code = "auth"
        error = e
    except RateLimitError as e:
        code = "rate"
        error = e
    except APITimeoutError as e:
        code = "timeout"
        error = e
    except APIConnectionError as e:
        code = "conn"
        error = e
    except Exception as e:
        code = "other"
        error = e
    else:
        text = (response.choices[0].message.content or "").strip()
        if not text:
            raise ModelError("empty")
        return text

    print(f"CultureBridge API error: {type(error).__name__}: {error}")
    raise ModelError(code) from error


# =====================================================
# 7. 受众反馈表单（创作者页与测试页共用）
# =====================================================

def render_feedback_form(form_key, resolve):
    """
    resolve() 返回 (版本号, 被评价的短帖原文, 主题, 平台)，仅在提交时调用，
    这样创作者在页面里改过短帖后，评分会对应修改后的版本。
    """
    with st.form(form_key):
        interest = st.slider(
            t("q_interest"), min_value=1, max_value=5, value=3,
            help=t("q_interest_help"),
        )
        understanding = st.slider(
            t("q_understanding"), min_value=1, max_value=5, value=3,
            help=t("q_understanding_help"),
        )
        learn_more = st.slider(
            t("q_learn_more"), min_value=1, max_value=5, value=3,
            help=t("q_learn_more_help"),
        )
        confusing = st.text_area(t("q_confusing"), max_chars=500)
        comment = st.text_area(t("q_comment"), max_chars=500)
        consent = st.checkbox(t("consent"), value=False)

        submitted = st.form_submit_button(
            t("submit_feedback"),
            type="primary",
            **stretch_kwargs(st.form_submit_button),
        )

    st.caption(t("no_personal_info"))

    if not submitted:
        return

    if not consent:
        st.error(t("consent_required"))
        return

    version, post_text, topic, platform = resolve()

    try:
        store.save_feedback(
            {
                "post_version": version,
                "topic": topic,
                "platform": platform,
                "lang": st.session_state.get("ui_lang", "zh"),
                "post_text": post_text,
                "interest": interest,
                "understanding": understanding,
                "learn_more": learn_more,
                "confusing_part": confusing.strip(),
                "comment": comment.strip(),
            }
        )
        load_feedback.clear()
        st.success(t("feedback_thanks"))
    except Exception as e:
        print(f"CultureBridge feedback save error: {type(e).__name__}: {e}")
        st.error(t("feedback_save_failed"))


# =====================================================
# 8. 受众测试页（?t=版本号）：只给测试者看，默认英文
# =====================================================

def render_tester_page(version):
    language_selector()

    if not core.valid_version(version):
        st.error(t("tester_bad_link"))
        st.stop()

    try:
        record = store.get_post(version)
    except Exception as e:
        print(f"CultureBridge get_post error: {type(e).__name__}: {e}")
        record = None

    if not record or not record.get("post"):
        st.error(t("tester_not_found"))
        st.stop()

    st.markdown(
        '<div class="main-title">🍵 CultureBridge</div>',
        unsafe_allow_html=True,
    )
    st.subheader(t("tester_title"))
    st.write(t("tester_intro"))

    render_post_card(record["post"])

    st.markdown("#### " + t("tester_form_title"))
    render_feedback_form(
        f"tester_form_{version}",
        lambda: (
            version,
            record["post"],
            record.get("topic", ""),
            record.get("platform", ""),
        ),
    )

    st.divider()
    st.caption(t("tester_footer"))
    st.stop()


if tester_version:
    render_tester_page(tester_version)


# =====================================================
# 9. 侧边栏
# =====================================================

with st.sidebar:
    language_selector()

    st.markdown("### 🍵 CultureBridge")
    st.caption(t("sidebar_tagline"))

    st.markdown("**" + t("sidebar_flow_title") + "**")
    st.markdown(t("sidebar_flow"))

    st.divider()
    quota_slot = st.empty()
    show_quota(quota_slot)

    if store.kind == "supabase":
        st.caption(t("storage_supabase"))
    else:
        st.caption(t("storage_local"))

    st.caption(t("sidebar_disclaimer"))


# =====================================================
# 10. 标题与说明
# =====================================================

st.markdown(
    '<div class="main-title">🍵 CultureBridge</div>',
    unsafe_allow_html=True,
)

st.subheader(t("subtitle"))
st.write(t("intro"))
st.caption(t("audience_caption"))

st.divider()


# =====================================================
# 11. 第一步：创建 / 修改短帖
# =====================================================

ss = st.session_state

left, right = st.columns([0.95, 1.15], gap="large")


def apply_result(raw, kind, meta):
    """把模型返回的内容写入会话，并记录这一版。"""
    post, translation, rationale, review = core.parse_result(raw)
    post = post[:MAX_POST_CHARS]
    topic_id, platform_id, style_id = meta

    ss["cb_ai_post"] = post
    ss["cb_post_edit"] = post
    ss["cb_logged_text"] = post
    ss["cb_translation"] = translation
    ss["cb_rationale"] = rationale
    ss["cb_review"] = review
    ss["cb_version"] = core.new_version()
    # base 只在“生成 / 追加要求”时变化；手动修改产生的新版本不会改变它，
    # 所以审核勾选等控件状态不会因为分享链接而丢失
    ss["cb_base"] = ss["cb_version"]
    ss["cb_topic"] = topic_id
    ss["cb_platform"] = platform_id
    ss["cb_style"] = style_id
    ss["cb_count"] = ss.get("cb_count", 0) + 1

    memory_incr()
    log_generation(kind, post)
    persisted_today.clear()


def log_generation(kind, post):
    """把这一版记入存储；失败不影响使用，只提示一次。"""
    try:
        store.log_generation(
            {
                "version": ss["cb_version"],
                "topic": ss.get("cb_topic", ""),
                "platform": ss.get("cb_platform", ""),
                "style": ss.get("cb_style", ""),
                "kind": kind,
                "model": MODEL_NAME,
                "post": post,
            }
        )
    except Exception as e:
        print(f"CultureBridge log error: {type(e).__name__}: {e}")
        ss["cb_store_warn"] = True


def ensure_committed_version():
    """保证当前（可能已被手动修改的）文本已存入某个版本，返回版本号。"""
    text = (ss.get("cb_post_edit") or "").strip()
    if text and text != (ss.get("cb_logged_text") or "").strip():
        ss["cb_version"] = core.new_version()
        ss["cb_logged_text"] = text
        log_generation("edit", text)
    return ss.get("cb_version", "")


with left:
    st.markdown('<span class="step-label">STEP 1</span>', unsafe_allow_html=True)
    st.markdown("### " + t("step1_title"))

    angle_id = st.selectbox(
        t("angle_label"),
        list(ANGLES.keys()),
        format_func=lambda key: ANGLES[key][ss.get("ui_lang", "zh")],
    )

    platform_id = st.radio(
        t("platform_label"),
        list(PLATFORMS.keys()),
        format_func=lambda key: PLATFORMS[key][ss.get("ui_lang", "zh")],
    )

    style_id = st.selectbox(
        t("style_label"),
        list(STYLES.keys()),
        format_func=lambda key: STYLES[key][ss.get("ui_lang", "zh")],
    )

    extra_note = st.text_input(
        t("extra_label"),
        max_chars=core.MAX_EXTRA_NOTE,
        placeholder=t("extra_placeholder"),
    ).strip()

    remaining_session, remaining_daily = quota_state()
    quota_exhausted = remaining_session <= 0 or remaining_daily <= 0

    generate = st.button(
        t("generate_btn"),
        type="primary",
        disabled=quota_exhausted,
        **stretch_kwargs(st.button),
    )

    if remaining_session <= 0:
        st.warning(t("quota_session_used"))
    elif remaining_daily <= 0:
        st.warning(t("quota_daily_used"))
    else:
        st.caption(t("generate_caption"))

    # ---- 处理“首次生成”和“追加要求”（来自右侧按钮的排队请求）----
    action = None
    if generate:
        action = ("generate", None)
    elif ss.get("cb_pending"):
        action = ("refine", ss.pop("cb_pending"))

    if action and not quota_exhausted:
        if not API_KEY:
            st.error(t("no_api_key"))
        else:
            user_prompt = None
            meta = None
            kind = action[0]

            if kind == "generate":
                user_prompt = core.build_user_prompt(
                    ANGLES[angle_id]["prompt"],
                    PLATFORMS[platform_id]["name"],
                    STYLES[style_id]["name"],
                    extra_note,
                )
                meta = (angle_id, platform_id, style_id)
            else:
                current = (ss.get("cb_post_edit") or "").strip()
                mode, payload = action[1]
                if mode == "preset" and payload in core.REFINE_PRESETS:
                    instruction = core.REFINE_PRESETS[payload]["instruction"]
                else:
                    instruction = payload

                topic_id = ss.get("cb_topic", angle_id)
                platform_now = ss.get("cb_platform", platform_id)
                style_now = ss.get("cb_style", style_id)

                if current and instruction:
                    user_prompt = core.build_refine_prompt(
                        current,
                        instruction,
                        PLATFORMS[platform_now]["name"],
                        STYLES[style_now]["name"],
                    )
                    meta = (topic_id, platform_now, style_now)

            if user_prompt:
                with st.spinner(t("spinner")):
                    try:
                        raw = call_model(
                            user_prompt,
                            0.7 if kind == "generate" else 0.6,
                        )
                    except ModelError as e:
                        st.error(t("err_" + e.code))
                        raw = None

                if raw:
                    apply_result(raw, kind, meta)
                    show_quota(quota_slot)

    if ss.pop("cb_store_warn", False):
        st.warning(t("store_warn"))


# =====================================================
# 12. 展示 / 编辑 / 追加要求
# =====================================================

with right:
    st.markdown("### " + t("post_heading"))

    if not ss.get("cb_version"):
        st.info(t("post_empty"))
    else:
        current_text = ss.get("cb_post_edit") or ""

        render_post_card(current_text)

        words = core.count_words(current_text)
        if words > core.WORD_LIMIT:
            st.warning(
                t("words_over", n=words, limit=core.WORD_LIMIT)
            )
        else:
            st.caption(t("words_ok", n=words, limit=core.WORD_LIMIT))

        render_copy_button(current_text)

        # ---- 手动修改 ----
        with st.expander(t("edit_expander")):
            st.text_area(
                t("edit_label"),
                key="cb_post_edit",
                height=220,
                max_chars=MAX_POST_CHARS,
            )
            st.caption(t("edit_hint"))

        # ---- 追加要求 ----
        st.markdown("**" + t("refine_title") + "**")

        preset_cols = st.columns(len(core.REFINE_PRESETS))
        for col, (preset_id, preset) in zip(
            preset_cols, core.REFINE_PRESETS.items()
        ):
            if col.button(
                preset[ss.get("ui_lang", "zh")],
                key=f"refine_{preset_id}",
                disabled=quota_exhausted,
                **stretch_kwargs(st.button),
            ):
                ss["cb_pending"] = ("preset", preset_id)
                st.rerun()

        custom_instruction = st.text_input(
            t("refine_custom_label"),
            key="cb_custom_instruction",
            max_chars=core.MAX_CUSTOM_INSTRUCTION,
            placeholder=t("refine_custom_placeholder"),
        ).strip()

        if st.button(
            t("refine_apply"),
            key="refine_custom_btn",
            disabled=quota_exhausted or not custom_instruction,
        ):
            ss["cb_pending"] = ("custom", custom_instruction)
            st.rerun()

        with st.expander(t("view_translation")):
            st.write(ss.get("cb_translation") or t("none_translation"))

        with st.expander(t("view_rationale")):
            st.write(ss.get("cb_rationale") or t("none_rationale"))

        with st.expander(t("view_model_review")):
            st.write(ss.get("cb_review") or t("none_review"))


# =====================================================
# 13. 第二至四步：审核 / 受众测试 / 反馈概览
# =====================================================

st.divider()

tab_review, tab_test, tab_overview = st.tabs(
    [t("tab_review"), t("tab_test"), t("tab_overview")]
)

version = ss.get("cb_version", "")
base = ss.get("cb_base", version)
text_now = (ss.get("cb_post_edit") or "").strip()
has_post = bool(version and text_now)


# ---------- 文化事实审核 ----------

with tab_review:
    st.markdown('<span class="step-label">STEP 2</span>', unsafe_allow_html=True)
    st.write(t("review_intro"))

    if not has_post:
        st.info(t("review_empty"))
    else:
        lang = ss.get("ui_lang", "zh")

        st.markdown("#### " + t("risk_title"))
        for risk in core.detect_risks(text_now, lang):
            st.warning(risk)
        st.caption(t("risk_caption"))

        st.markdown("#### " + t("sources_title"))
        for i, source in enumerate(SOURCES, start=1):
            st.markdown(f"**{i}. [{source['title']}]({source['url']})**")
            st.write(source["note"][lang])

        st.markdown("#### " + t("claims_title"))
        st.write(t("claims_intro"))

        if text_now != (ss.get("cb_ai_post") or "").strip():
            st.info(t("claims_stale"))

        claims = core.extract_claims(ss.get("cb_review", ""))
        checked_claims = []

        if not claims:
            st.caption(t("claims_none"))
        else:
            # 控件 key 带上版本号：重新生成或修改后会回到初始状态，
            # 不会沿用上一版的核验结论
            for index, claim in enumerate(claims):
                if st.checkbox(claim, key=f"cb_claim_{base}_{index}"):
                    checked_claims.append(claim)

            st.progress(len(checked_claims) / len(claims))
            st.caption(
                t("claims_progress", done=len(checked_claims), total=len(claims))
            )

        open_claims = [c for c in claims if c not in checked_claims]

        st.markdown("#### " + t("record_title"))

        checked_titles = st.multiselect(
            t("checked_sources_label"),
            [s["title"] for s in SOURCES],
            key=f"cb_checked_{base}",
        )

        verification = st.radio(
            t("status_label"),
            VERIFY_STATES,
            format_func=lambda key: t("status_" + key),
            index=0,
            key=f"cb_verification_{base}",
        )

        reviewer_note = st.text_area(
            t("note_label"),
            key=f"cb_reviewer_note_{base}",
            placeholder=t("note_placeholder"),
        )

        if verification == "verified":
            if open_claims:
                st.warning(t("verify_open_claims", n=len(open_claims)))
            elif not checked_titles:
                st.warning(t("verify_no_sources"))
            else:
                st.success(t("verify_done"))
        elif verification == "partial":
            st.warning(t("verify_partial"))
        else:
            st.warning(t("verify_pending"))

        if st.button(t("save_review_btn")):
            try:
                store.save_review(
                    {
                        "post_version": ensure_committed_version(),
                        "topic": ss.get("cb_topic", ""),
                        "verification_status": verification,
                        "checked_sources": " ; ".join(
                            s["url"] for s in SOURCES
                            if s["title"] in checked_titles
                        ),
                        "claims_confirmed": " | ".join(checked_claims),
                        "claims_open": " | ".join(open_claims),
                        "reviewer_note": reviewer_note,
                        "post_text": text_now,
                    }
                )
                st.success(t("review_saved"))
            except Exception as e:
                print(f"CultureBridge review save error: {type(e).__name__}: {e}")
                st.error(t("review_save_failed"))


# ---------- 受众测试 ----------

with tab_test:
    st.markdown('<span class="step-label">STEP 3</span>', unsafe_allow_html=True)
    st.write(t("test_intro"))

    if not has_post:
        st.info(t("test_empty"))
    else:
        st.markdown("#### " + t("share_title"))
        st.write(t("share_intro"))

        if st.button(t("share_btn"), key="share_btn"):
            ss["cb_share_version"] = ensure_committed_version()

        share_version = ss.get("cb_share_version")
        link_is_current = (
            share_version
            and share_version == ss.get("cb_version")
            and text_now == (ss.get("cb_logged_text") or "").strip()
        )

        if link_is_current:
            st.code(f"{APP_URL.rstrip('/')}/?t={share_version}", language=None)
            if store.kind != "supabase":
                st.caption(t("share_local_warning"))
        elif share_version:
            st.info(t("share_stale"))

        with st.expander(t("inpage_title")):
            st.caption(t("inpage_intro"))
            render_feedback_form(
                f"audience_form_{base}",
                lambda: (
                    ensure_committed_version(),
                    text_now,
                    ss.get("cb_topic", ""),
                    ss.get("cb_platform", ""),
                ),
            )


# ---------- 反馈概览 ----------

with tab_overview:
    st.markdown('<span class="step-label">STEP 4</span>', unsafe_allow_html=True)

    try:
        all_rows = load_feedback()
    except Exception as e:
        print(f"CultureBridge load feedback error: {type(e).__name__}: {e}")
        all_rows = []
        st.warning(t("overview_load_failed"))

    if not all_rows:
        st.info(t("overview_empty"))
    else:
        scope = st.radio(
            t("scope_label"),
            ["all", "current"],
            format_func=lambda key: t("scope_" + key),
            horizontal=True,
            disabled=not version,
        )

        if scope == "current" and version:
            rows = [r for r in all_rows if r.get("post_version") == version]
        else:
            rows = all_rows

        if not rows:
            st.info(t("overview_none_for_version"))
        else:
            count = len(rows)
            interest = core.mean_score(rows, "interest")
            understanding = core.mean_score(rows, "understanding")
            learn_more = core.mean_score(rows, "learn_more")

            c1, c2, c3, c4 = st.columns(4)
            c1.metric(t("metric_count"), count)
            c2.metric(t("metric_interest"), f"{interest} / 5")
            c3.metric(t("metric_understanding"), f"{understanding} / 5")
            c4.metric(t("metric_learn_more"), f"{learn_more} / 5")

            chart_df = pd.DataFrame(
                {t("chart_avg"): [interest, understanding, learn_more]},
                index=[
                    t("chart_interest"),
                    t("chart_understanding"),
                    t("chart_learn_more"),
                ],
            )
            st.bar_chart(chart_df)

            if count < 5:
                st.caption(t("sample_tiny", n=count))
            else:
                st.caption(t("sample_small"))

            summary = core.summarise_by_version(all_rows)
            if len(summary) > 1:
                st.markdown("**" + t("by_version_title") + "**")
                st.dataframe(
                    pd.DataFrame(summary[:10]).rename(
                        columns={
                            "version": t("col_version"),
                            "n": t("col_n"),
                            "interest": t("chart_interest"),
                            "understanding": t("chart_understanding"),
                            "learn_more": t("chart_learn_more"),
                        }
                    )
                )

    st.caption(
        t("storage_note_supabase")
        if store.kind == "supabase"
        else t("storage_note_local")
    )

    # 原始反馈含自由文本，不对公开访客展示：需要管理员口令
    with st.expander(t("admin_title")):
        if not ADMIN_KEY:
            st.caption(t("admin_not_set"))
        else:
            entered = st.text_input(t("admin_password"), type="password")
            if entered and hmac.compare_digest(
                entered.encode("utf-8"), ADMIN_KEY.encode("utf-8")
            ):
                for label_key, loader, file_name in (
                    ("admin_feedback", store.list_feedback, "feedback.csv"),
                    ("admin_reviews", store.list_reviews, "fact_reviews.csv"),
                ):
                    st.markdown("**" + t(label_key) + "**")
                    try:
                        data = loader()
                    except Exception as e:
                        print(f"CultureBridge admin load error: "
                              f"{type(e).__name__}: {e}")
                        data = []
                        st.warning(t("overview_load_failed"))

                    if data:
                        st.dataframe(data)
                        st.download_button(
                            t("admin_download", name=file_name),
                            data=core.rows_to_csv_bytes(data),
                            file_name=file_name,
                            mime="text/csv",
                            key=f"dl_{file_name}",
                        )
                    else:
                        st.caption(t("admin_no_records"))
            elif entered:
                st.error(t("admin_wrong"))


st.divider()
st.caption(t("footer"))
