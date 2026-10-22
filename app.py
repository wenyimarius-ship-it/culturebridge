

import os
import re
import html
import csv
from pathlib import Path
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from openai import OpenAI


# =====================================================
# 1. 基础设置
# =====================================================

st.set_page_config(
    page_title="CultureBridge | 中国茶文化探索",
    page_icon="🍵",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

API_KEY = (
    os.getenv("DEEPSEEK_API_KEY")
    or os.getenv("OPENAI_API_KEY")
)

API_BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"

FEEDBACK_FILE = BASE_DIR / "audience_feedback.csv"

# 示例参考资料：来源链接不等于具体文案已通过审核
SOURCES = [
    {
        "title": "Smithsonian：Tea Culture in China",
        "url": (
            "https://asia.si.edu/education/educator-resources/"
            "teaching-china-with-the-smithsonian/lesson-plans/"
            "tea-culture-in-china/"
        ),
        "note": "介绍中国茶文化的历史、社会生活和茶具背景。",
    },
    {
        "title": "UNESCO：Traditional tea processing techniques "
                "and associated social practices in China",
        "url": (
            "https://ich.unesco.org/en/RL/"
            "traditional-tea-processing-techniques-and-associated-"
            "social-practices-in-china-01884"
        ),
        "note": "介绍中国传统制茶技艺及相关社会实践。",
    },
    {
        "title": "Smithsonian：Exploring Chinese Teas and Tea Wares",
        "url": (
            "https://asia-archive.si.edu/learn/for-educators/"
            "teaching-china-with-the-smithsonian/videos/"
            "exploring-chinese-teas-and-tea-wares/"
        ),
        "note": "介绍中国茶、功夫茶及茶具。",
    },
]


# =====================================================
# 2. 页面样式
# =====================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 750;
        margin-bottom: 0.2rem;
    }

    .muted {
        color: #A6A6B5;
        font-size: 0.9rem;
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

    .status-pending {
        color: #F5C26B;
        font-weight: 600;
    }

    .status-verified {
        color: #57D99A;
        font-weight: 600;
    }

    .status-risk {
        color: #FF8585;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# 3. 小工具：文件、文本与结果解析
# =====================================================

def parse_result(text):
    """将 DeepSeek 返回的内容拆成不同区块。"""

    def extract(heading, next_headings):
        match = re.search(
            re.escape(heading),
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return ""

        start = match.end()
        end = len(text)

        for next_heading in next_headings:
            next_match = re.search(
                re.escape(next_heading),
                text[start:],
                flags=re.IGNORECASE,
            )
            if next_match:
                end = min(end, start + next_match.start())

        return text[start:end].strip()

    post = extract(
        "【English Post】",
        ["【中文翻译】", "【文化表达思路】", "【需要核实的内容】"],
    )
    translation = extract(
        "【中文翻译】",
        ["【文化表达思路】", "【需要核实的内容】"],
    )
    rationale = extract(
        "【文化表达思路】",
        ["【需要核实的内容】"],
    )
    review = extract("【需要核实的内容】", [])

    if not post:
        post = text.strip()

    return post, translation, rationale, review


def detect_risks(post):
    """
    只做简单的关键词风险提示，不是事实核查器。
    命中关键词不等于错误；未命中也不等于事实正确。
    """
    checks = [
        (
            r"\ball Chinese people\b|\bevery Chinese person\b",
            "可能把不同地区、家庭和个人的做法概括成统一习俗。",
        ),
        (
            r"\ball Chinese families\b|\bevery family\b",
            "可能过度概括家庭实践，建议补充地域或情境限定。",
        ),
        (
            r"\balways\b|\bnever\b|\bmust\b",
            "绝对化表达可能掩盖文化实践中的差异。",
        ),
        (
            r"\bfor thousands of years\b|\bancient origin\b",
            "涉及历史时间或起源，建议查证可靠历史来源。",
        ),
        (
            r"\bscientifically proven\b|\bproves that\b",
            "涉及科学结论，需要可靠研究支持。",
        ),
    ]

    found = []
    for pattern, message in checks:
        if re.search(pattern, post, flags=re.IGNORECASE):
            found.append(message)

    if not found:
        found.append(
            "未发现预设关键词风险；这不代表文案中的事实已经核实。"
        )

    return found


def load_feedback():
    """读取已保存的受众反馈。"""
    if not FEEDBACK_FILE.exists():
        return []

    try:
        with open(FEEDBACK_FILE, "r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except (OSError, csv.Error):
        return []


def save_feedback(record):
    """将一条受众反馈追加保存到 CSV。"""
    fieldnames = [
        "timestamp",
        "post_version",
        "interest",
        "understanding",
        "learn_more",
        "confusing_part",
        "comment",
    ]

    file_exists = FEEDBACK_FILE.exists()

    with open(FEEDBACK_FILE, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(record)


# =====================================================
# 4. 标题与说明
# =====================================================

st.markdown(
    '<div class="main-title">🍵 CultureBridge</div>',
    unsafe_allow_html=True,
)

st.subheader("中国茶文化探索 · Tea Culture Explorer")

st.write(
    "把文化知识转化成有吸引力、可讨论、愿意分享的社交内容。"
)

st.caption(
    "目标受众：英国年轻职场人｜传播目标：激发兴趣，鼓励进一步了解"
)

st.divider()


# =====================================================
# 5. 创建短帖
# =====================================================

ANGLE_OPTIONS = {
    "为什么中国泡茶有时像一种仪式？":
        "Why can preparing Chinese tea feel like a ritual?",
    "为什么给客人倒茶能表达待客之道？":
        "How can serving tea express hospitality?",
    "中国茶文化中有哪些值得探索的细节？":
        "What details make Chinese tea culture worth exploring?",
    "一杯茶如何让人与人建立联系？":
        "How can sharing tea help people connect?",
}

PLATFORM_OPTIONS = {
    "Instagram（图片与短帖）": "Instagram",
    "LinkedIn（职业社交）": "LinkedIn",
}

STYLE_OPTIONS = {
    "好奇启发型": "Curious",
    "轻松幽默型": "Playful",
    "深度思考型": "Reflective",
}

left, right = st.columns([0.95, 1.15], gap="large")

with left:
    st.markdown("### 🎯 第一步：创建文化短帖")

    angle_label = st.selectbox(
        "选择文化主题切入点",
        list(ANGLE_OPTIONS.keys()),
    )

    platform_label = st.radio(
        "选择发布平台",
        list(PLATFORM_OPTIONS.keys()),
    )

    style_label = st.selectbox(
        "选择文案风格",
        list(STYLE_OPTIONS.keys()),
    )

    generate = st.button(
        "✨ 生成文化短帖",
        type="primary",
        use_container_width=True,
    )

    st.caption("生成内容为 AI 初稿，发布前请人工核实文化事实。")


if generate:
    if not API_KEY:
        st.error(
            "没有找到 API Key。请检查项目根目录中的 .env 文件，"
            "确认 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 已正确填写。"
        )
    else:
        system_prompt = """
You are CultureBridge, a cross-cultural storytelling editor.

Audience: young professionals in the United Kingdom.
Topic: Chinese tea culture.
Goal: spark curiosity and encourage further learning.

Write natural, engaging British English.

Rules:
- Keep the English social post under 100 words.
- Focus on one specific cultural idea.
- Use concrete details and an inviting question.
- Do not claim that all Chinese people share the same practices.
- Do not invent historical facts, sources, statistics or research.
- Do not claim any source has been verified.
- Clearly separate the English post from the Chinese explanation.
- Give cautious, specific suggestions for human fact review.

Return exactly these headings:

【English Post】
English post only.

【中文翻译】
Chinese translation.

【文化表达思路】
Brief explanation in Chinese.

【需要核实的内容】
Claims requiring human review.
If uncertain, state that the claim needs verification.
"""

        user_prompt = f"""
文化切入点：{ANGLE_OPTIONS[angle_label]}
目标受众：英国年轻职场人
发布平台：{PLATFORM_OPTIONS[platform_label]}
文案风格：{STYLE_OPTIONS[style_label]}
传播目标：激发兴趣，让读者愿意进一步了解中国茶文化。

请以自然的英国英语写作，并用开放式问题邀请读者互动。
"""

        with st.spinner("正在连接 DeepSeek，生成短帖……"):
            try:
                client = OpenAI(
                    api_key=API_KEY,
                    base_url=API_BASE_URL,
                    timeout=60.0,
                    max_retries=1,
                )

                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                )

                raw = (response.choices[0].message.content or "").strip()

                if not raw:
                    st.error("模型没有返回内容，请重试。")
                else:
                    post, translation, rationale, review = parse_result(raw)

                    st.session_state["cb_post"] = post
                    st.session_state["cb_translation"] = translation
                    st.session_state["cb_rationale"] = rationale
                    st.session_state["cb_review"] = review
                    st.session_state["cb_version"] = datetime.now().strftime(
                        "%Y%m%d-%H%M%S"
                    )
                    st.session_state["cb_topic"] = angle_label
                    st.session_state["cb_platform"] = platform_label

            except Exception as e:
                st.error(
                    f"DeepSeek 调用失败：{type(e).__name__}。"
                    "请检查终端中的详细错误、API Key、账户额度和网络。"
                )
                print(f"CultureBridge API error: {type(e).__name__}: {e}")


# =====================================================
# 6. 展示生成结果
# =====================================================

with right:
    st.markdown("### 📝 第二步：你的文化短帖")

    post = st.session_state.get("cb_post", "")

    if not post:
        st.info("👈 选择参数并点击「生成文化短帖」。")
    else:
        st.success("短帖生成成功！")

        safe_post = html.escape(post, quote=True)

        st.markdown(
            '<div class="post-card">'
            '<div class="post-header">'
            '<div class="post-avatar">🍵</div>'
            '<div><strong>culturebridge.stories</strong><br>'
            '<span class="muted">Tea culture · Cross-cultural stories</span>'
            '</div></div>'
            f'<div class="post-body">{safe_post}</div>'
            '<div class="post-footer">♡ Like　　♡ Comment　　↗ Share</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # 使用浏览器剪贴板 API 复制纯英文正文
        post_json = __import__("json").dumps(post)

        components.html(
            f"""
            <button id="copy-btn" style="
                width:100%;padding:12px;border:0;border-radius:10px;
                background:#ff4b4b;color:white;font-size:15px;
                font-weight:600;cursor:pointer;">
                📋 复制英文短帖
            </button>
            <div id="copy-status" style="
                margin-top:6px;color:#A6A6B5;font-size:13px;"></div>
            <script>
            const postText = {post_json};
            const button = document.getElementById("copy-btn");
            const status = document.getElementById("copy-status");

            button.addEventListener("click", async () => {{
                try {{
                    await navigator.clipboard.writeText(postText);
                    button.innerText = "✓ 已复制英文短帖";
                    status.innerText = "可以粘贴到社交媒体编辑框。";
                }} catch (e) {{
                    status.innerText =
                      "浏览器限制了自动复制，请手动选择卡片正文复制。";
                }}
            }});
            </script>
            """,
            height=78,
        )

        with st.expander("📖 查看中文翻译"):
            st.write(st.session_state.get("cb_translation", "暂无翻译。"))

        with st.expander("💡 查看文化表达思路"):
            st.write(st.session_state.get("cb_rationale", "暂无说明。"))

        with st.expander("🧾 查看模型提出的核实建议"):
            st.write(st.session_state.get("cb_review", "暂无建议。"))


# =====================================================
# 7. 新功能 A：文化事实审核
# =====================================================

st.divider()
st.header("🔎 第三步：文化事实审核")

st.write(
    "查看可参考的文化资料，并记录人工核验状态。"
    "来源存在不代表每一句文案都得到该来源支持。"
)

if not st.session_state.get("cb_post"):
    st.info("生成一条短帖后，即可对照来源开展人工审核。")
else:
    post = st.session_state["cb_post"]
    risks = detect_risks(post)

    st.markdown("#### 风险提示")

    for risk in risks:
        st.warning(risk)

    st.caption(
        "以上是基于关键词的初步风险提示，不是自动事实核查。"
    )

    st.markdown("#### 参考来源")

    for i, source in enumerate(SOURCES, start=1):
        st.markdown(f"**{i}. [{source['title']}]({source['url']})**")
        st.write(source["note"])

    st.markdown("#### 人工核验记录")

    st.write(
        "逐条对照来源，确认来源是否确实支持文案中的相关表述。"
    )

    verification = st.radio(
        "当前文案的审核状态",
        [
            "待人工核验",
            "已检查来源，但仍有待核实内容",
            "已人工核验当前版本",
        ],
        index=0,
        key="cb_verification",
    )

    reviewer_note = st.text_area(
        "审核备注（例如：需要核对具体茶类、地域或冲泡方法）",
        key="cb_reviewer_note",
        placeholder="写下需要进一步核实的事实或修改建议……",
    )

    if verification == "已人工核验当前版本":
        st.success(
            "你已将当前版本标记为人工核验完成。"
            "请确保每一条关键事实都能被来源支持。"
        )
    elif verification == "已检查来源，但仍有待核实内容":
        st.warning("当前版本仍有待核实内容，不建议直接发布。")
    else:
        st.warning("当前版本尚未完成核验。")

    if st.button("保存本次审核记录"):
        audit_file = BASE_DIR / "fact_review_log.csv"
        exists = audit_file.exists()

        with open(
            audit_file, "a", encoding="utf-8-sig", newline=""
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "post_version",
                    "topic",
                    "verification_status",
                    "reviewer_note",
                    "sources",
                ],
            )

            if not exists:
                writer.writeheader()

            writer.writerow({
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "post_version": st.session_state.get("cb_version", ""),
                "topic": st.session_state.get("cb_topic", ""),
                "verification_status": verification,
                "reviewer_note": reviewer_note,
                "sources": " ; ".join(s["url"] for s in SOURCES),
            })

        st.success("审核记录已保存到 fact_review_log.csv。")


# =====================================================
# 8. 新功能 B：受众测试
# =====================================================

st.divider()
st.header("🧪 第四步：受众测试")

st.write(
    "邀请目标受众评价短帖是否吸引人、是否容易理解，"
    "以及是否愿意进一步了解中国茶文化。"
)

if not st.session_state.get("cb_post"):
    st.info("请先生成短帖，再开展受众测试。")
else:
    st.markdown("#### 请以读者的角度评价这条英文短帖")

    with st.form("audience_feedback_form"):
        interest = st.slider(
            "1. 这条短帖有多吸引你？",
            min_value=1,
            max_value=5,
            value=3,
            help="1 = 完全不吸引，5 = 非常吸引",
        )

        understanding = st.slider(
            "2. 你觉得自己理解了短帖想表达的文化含义吗？",
            min_value=1,
            max_value=5,
            value=3,
            help="1 = 完全不理解，5 = 完全理解",
        )

        learn_more = st.slider(
            "3. 读完后，你有多愿意进一步了解中国茶文化？",
            min_value=1,
            max_value=5,
            value=3,
            help="1 = 完全不愿意，5 = 非常愿意",
        )

        confusing = st.text_area(
            "有没有让你困惑、难以理解或不太可信的地方？（选填）"
        )

        comment = st.text_area(
            "你希望进一步了解什么？（选填）"
        )

        consent = st.checkbox(
            "我同意将本次匿名评价用于 CultureBridge Demo 的内容改进。",
            value=False,
        )

        submitted = st.form_submit_button(
            "提交匿名评价",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if not consent:
            st.error("请先确认是否同意提交匿名评价。")
        else:
            record = {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "post_version": st.session_state.get("cb_version", ""),
                "interest": interest,
                "understanding": understanding,
                "learn_more": learn_more,
                "confusing_part": confusing.strip(),
                "comment": comment.strip(),
            }

            try:
                save_feedback(record)
                st.success(
                    "感谢你的反馈！匿名评价已保存到本地 CSV 文件。"
                )
            except OSError as e:
                st.error(f"反馈保存失败：{e}")


# =====================================================
# 9. 受众测试结果概览
# =====================================================

st.subheader("📊 受众反馈概览")

feedback_rows = load_feedback()

if not feedback_rows:
    st.info(
        "目前还没有保存的问卷。"
        "提交几条测试反馈后，这里会显示汇总结果。"
    )
else:
    def mean_score(field):
        values = []
        for row in feedback_rows:
            try:
                values.append(float(row[field]))
            except (ValueError, KeyError):
                pass
        return round(sum(values) / len(values), 2) if values else 0

    count = len(feedback_rows)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("有效反馈数", count)
    c2.metric("平均兴趣度", f"{mean_score('interest')} / 5")
    c3.metric("平均理解度", f"{mean_score('understanding')} / 5")
    c4.metric("进一步了解意愿", f"{mean_score('learn_more')} / 5")

    st.caption(
        "这些分数是当前本地 CSV 中的反馈汇总。"
        "小样本结果仅供迭代参考，不代表所有英国年轻职场人的意见。"
    )

    with st.expander("查看已收集的反馈记录"):
        st.dataframe(feedback_rows, use_container_width=True)

st.divider()

st.caption(
    "CultureBridge Demo · AI 辅助跨文化传播原型。"
    "事实核验需要人工判断；受众评分是自愿提供的反馈。"
)

