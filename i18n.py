"""界面文案：中文 / English。

用法：translate("zh", "quota_line", rs=3, ms=15, rd=100, md=200)
两种语言的键必须完全一致、占位符也必须一致（有单元测试检查）。
"""

# 记录查不到的键，方便测试发现遗漏
MISSING = set()

STRINGS = {
    "zh": {
        # ---- 复制按钮 ----
        "copy_btn": "📋 复制英文短帖",
        "copy_done": "✓ 已复制英文短帖",
        "copy_hint": "可以粘贴到社交媒体编辑框。",
        "copy_fail": "浏览器限制了自动复制，请手动选择卡片正文复制。",

        # ---- 额度 / 存储 ----
        "quota_line": "剩余生成次数：本次访问 {rs}/{ms}，今日全站 {rd}/{md}",
        "quota_session_used": "本次访问的生成次数已用完，刷新页面可重新开始。",
        "quota_daily_used": "今日全站的生成额度已用完，请明天再来。",
        "storage_supabase": "💾 数据存储：Supabase（持久保存）",
        "storage_unavailable": "云端存储连接失败。当前不要提交反馈，请稍后重试。",
        "storage_local": "💾 数据存储：本地临时文件（云端重启后可能清空）",
        "store_warn": "这一版没能记录到存储中，但不影响继续使用。",

        # ---- 反馈表单 ----
        "q_interest": "1. 这条短帖有多吸引你？",
        "q_interest_help": "1 = 完全不吸引，5 = 非常吸引",
        "q_understanding": "2. 你觉得自己理解了短帖想表达的文化含义吗？",
        "q_understanding_help": "1 = 完全不理解，5 = 完全理解",
        "q_learn_more": "3. 读完后，你有多愿意进一步了解中国茶文化？",
        "q_learn_more_help": "1 = 完全不愿意，5 = 非常愿意",
        "q_confusing": "有没有让你困惑、难以理解或不太可信的地方？（选填）",
        "q_comment": "你希望进一步了解什么？（选填）",
        "consent": "我同意将本次匿名评价用于 CultureBridge Demo 的内容改进。",
        "submit_feedback": "提交匿名评价",
        "no_personal_info": "请勿在评价中填写姓名、邮箱等个人信息。",
        "consent_required": "请先勾选同意，再提交匿名评价。",
        "feedback_thanks": "感谢你的反馈！匿名评价已保存。",
        "feedback_save_failed": "反馈保存失败，请稍后再试。",

        # ---- 受众测试页 ----
        "tester_bad_link": "这个测试链接无效。",
        "tester_not_found": "找不到这条短帖，链接可能已失效，请联系发给你链接的人。",
        "tester_title": "给一条关于中国茶文化的短帖打分",
        "tester_intro": "只需约 1 分钟：读一读下面的短帖，再回答 3 个简短问题。"
                        "回答完全匿名，只用于改进内容。短帖是 AI 辅助的草稿。",
        "tester_form_title": "你的看法",
        "tester_footer": "CultureBridge 是一个 AI 辅助跨文化传播原型，评分为自愿提供的匿名反馈。",

        # ---- 侧边栏 ----
        "sidebar_tagline": "AI 跨文化内容共创原型",
        "sidebar_flow_title": "工作流",
        "sidebar_flow": (
            "1. 选择主题、平台与风格，生成并修改英文短帖\n"
            "2. 对照来源，逐条完成文化事实审核\n"
            "3. 把测试链接发给目标读者，收集匿名反馈\n"
            "4. 查看反馈概览，迭代下一版"
        ),
        "sidebar_disclaimer": "AI 生成内容仅为初稿，发布前必须人工核实文化事实。",

        # ---- 标题 ----
        "subtitle": "中国茶文化探索 · Tea Culture Explorer",
        "intro": "把文化知识转化成有吸引力、可讨论、愿意分享的社交内容。",
        "audience_caption": "目标受众：英国年轻职场人｜传播目标：激发兴趣，鼓励进一步了解",

        # ---- 第一步 ----
        "step1_title": "🎯 创建文化短帖",
        "angle_label": "选择文化主题切入点",
        "platform_label": "选择发布平台",
        "style_label": "选择文案风格",
        "extra_label": "补充想法（选填）",
        "extra_placeholder": "例如：可以提到办公室里的下午茶时间",
        "generate_btn": "✨ 生成文化短帖",
        "generate_caption": "生成内容为 AI 初稿，发布前请人工核实文化事实。",
        "no_api_key": "没有找到 API Key。本地运行请检查 .env 文件；"
                      "部署在 Streamlit Cloud 请在 Secrets 中填写 DEEPSEEK_API_KEY。",
        "err_auth": "API Key 无效或已过期，请检查 Secrets / .env 中的密钥。",
        "err_rate": "请求过于频繁或账户额度不足，请稍后再试。",
        "err_timeout": "模型响应超时，请重试一次。",
        "err_conn": "无法连接到模型服务，请检查网络后重试。",
        "err_other": "模型调用失败，详细信息已写入日志。",
        "err_empty": "模型没有返回内容，请重试。",
        "spinner": "正在生成短帖……",

        # ---- 展示 / 编辑 / 追加要求 ----
        "post_heading": "📝 你的文化短帖",
        "post_empty": "👈 选择参数并点击「生成文化短帖」。",
        "words_over": "当前约 {n} 词，超过 {limit} 词，建议再缩短。",
        "words_ok": "约 {n} 词（目标：{limit} 词以内）",
        "edit_expander": "✏️ 手动修改短帖",
        "edit_label": "英文短帖（修改后，核实清单、测试链接和反馈都会对应修改后的版本）",
        "edit_hint": "修改会即时反映在上方卡片中。",
        "refine_title": "让模型继续修改",
        "refine_custom_label": "或写一条自己的修改要求",
        "refine_custom_placeholder": "例如：开头换成一个办公室场景",
        "refine_apply": "按这条要求修改",
        "view_translation": "📖 查看中文翻译",
        "none_translation": "暂无翻译。",
        "view_rationale": "💡 查看文化表达思路",
        "none_rationale": "暂无说明。",
        "view_model_review": "🧾 查看模型提出的核实建议",
        "none_review": "暂无建议。",

        # ---- 标签页 ----
        "tab_review": "🔎 文化事实审核",
        "tab_test": "🧪 受众测试",
        "tab_overview": "📊 反馈概览",

        # ---- 审核 ----
        "review_intro": "查看可参考的文化资料，逐条核对待核实内容，并记录人工核验状态。"
                        "来源存在不代表每一句文案都得到该来源支持。",
        "review_empty": "生成一条短帖后，即可对照来源开展人工审核。",
        "risk_title": "风险提示",
        "risk_caption": "以上是基于关键词的初步提示，不是自动事实核查。",
        "sources_title": "参考来源",
        "claims_title": "待核实清单",
        "claims_intro": "下面是模型指出的需要核实的内容，请对照来源逐条确认，确认后打勾。",
        "claims_stale": "你已修改过短帖，下面的清单基于 AI 初稿，请自行补充新增的表述。",
        "claims_none": "模型没有给出可拆分的核实条目，请在备注里自行记录。",
        "claims_progress": "已确认 {done} / {total} 条",
        "record_title": "人工核验记录",
        "checked_sources_label": "本次实际核对了哪些来源？",
        "status_label": "当前文案的审核状态",
        "status_pending": "待人工核验",
        "status_partial": "已检查来源，但仍有待核实内容",
        "status_verified": "已人工核验当前版本",
        "note_label": "审核备注（例如：需要核对具体茶类、地域或冲泡方法）",
        "note_placeholder": "写下需要进一步核实的事实或修改建议……",
        "verify_open_claims": "你标记为“已人工核验”，但还有 {n} 条待核实内容没有确认。",
        "verify_no_sources": "你标记为“已人工核验”，但还没有勾选核对过的来源，建议补充。",
        "verify_done": "已标记为人工核验完成，所有清单条目都已确认。",
        "verify_partial": "当前版本仍有待核实内容，不建议直接发布。",
        "verify_pending": "当前版本尚未完成核验。",
        "save_review_btn": "保存本次审核记录",
        "review_saved": "审核记录已保存。",
        "review_save_failed": "审核记录保存失败，请稍后再试。",

        # ---- 受众测试（创作者页）----
        "test_intro": "把测试链接发给目标读者（英国年轻职场人），他们会看到一个英文评分页；"
                      "也可以在当面测试时直接在本页填写。",
        "test_empty": "请先生成短帖，再开展受众测试。",
        "share_title": "分享测试链接",
        "share_intro": "链接对应当前这一版短帖（包含你的手动修改）。修改短帖后需要重新生成链接。",
        "share_btn": "🔗 生成受众测试链接",
        "share_local_warning": "当前使用本地临时存储：应用重启后链接会失效，反馈也会丢失。"
                               "正式测试前请配置 Supabase。",
        "share_stale": "短帖已修改，之前的链接对应旧版本。请重新点击按钮生成新链接。",
        "inpage_title": "当面测试：直接在本页填写",
        "inpage_intro": "适合现场请人看一眼并打分。评分会记录到当前版本。",

        # ---- 概览 ----
        "overview_load_failed": "暂时无法读取反馈数据。",
        "overview_empty": "目前还没有保存的问卷。提交几条测试反馈后，这里会显示汇总结果。",
        "scope_label": "统计范围",
        "scope_all": "全部版本",
        "scope_current": "仅当前版本",
        "overview_none_for_version": "当前版本还没有收到反馈。",
        "metric_count": "有效反馈数",
        "metric_interest": "平均兴趣度",
        "metric_understanding": "平均理解度",
        "metric_learn_more": "进一步了解意愿",
        "chart_avg": "平均分",
        "chart_interest": "兴趣度",
        "chart_understanding": "理解度",
        "chart_learn_more": "了解意愿",
        "sample_tiny": "目前仅有 {n} 条反馈，样本很小，结果只适合作为迭代线索。",
        "sample_small": "小样本结果仅供迭代参考，不代表所有英国年轻职场人的意见。",
        "by_version_title": "各版本对比",
        "col_version": "版本",
        "col_n": "反馈数",
        "storage_note_supabase": "反馈保存在 Supabase 数据库中。",
        "storage_note_local": "反馈保存在应用服务器的 CSV 文件中；云端应用重启或重新部署后可能被清空，"
                              "重要数据请及时导出。",

        # ---- 管理员 ----
        "admin_title": "🔐 管理员：查看原始记录 / 下载 CSV",
        "admin_not_set": "尚未设置 ADMIN_KEY。在 .env 或 Streamlit Secrets 中添加 "
                         "ADMIN_KEY 后，可在此查看原始记录并下载。",
        "admin_password": "管理员口令",
        "admin_feedback": "受众反馈",
        "admin_reviews": "审核记录",
        "admin_download": "下载 {name}",
        "admin_no_records": "暂无记录。",
        "admin_wrong": "口令不正确。",

        "footer": "CultureBridge Demo · AI 辅助跨文化传播原型。"
                  "事实核验需要人工判断；受众评分是自愿提供的反馈。",
    },

    "en": {
        # ---- Copy button ----
        "copy_btn": "📋 Copy English post",
        "copy_done": "✓ Copied",
        "copy_hint": "You can now paste it into a social media editor.",
        "copy_fail": "Your browser blocked automatic copying; please select "
                     "the text in the card and copy it manually.",

        # ---- Quota / storage ----
        "quota_line": "Generations left: this visit {rs}/{ms}, site today {rd}/{md}",
        "quota_session_used": "You have used all generations for this visit. "
                              "Refresh the page to start again.",
        "quota_daily_used": "Today's site-wide generation quota is used up. "
                            "Please come back tomorrow.",
        "storage_supabase": "💾 Storage: Supabase (persistent)",
        "storage_unavailable": "Cloud storage is unavailable. Please wait before submitting feedback.",
        "storage_local": "💾 Storage: temporary local files "
                         "(may be wiped when the cloud app restarts)",
        "store_warn": "This version could not be saved to storage, but you "
                      "can keep working.",

        # ---- Feedback form ----
        "q_interest": "1. How engaging did you find this post?",
        "q_interest_help": "1 = not at all, 5 = very engaging",
        "q_understanding": "2. How well did you understand the cultural idea "
                           "the post was getting at?",
        "q_understanding_help": "1 = not at all, 5 = completely",
        "q_learn_more": "3. After reading, how much would you like to learn "
                        "more about Chinese tea culture?",
        "q_learn_more_help": "1 = not at all, 5 = very much",
        "q_confusing": "Anything confusing, unclear or hard to believe? (optional)",
        "q_comment": "What would you like to know more about? (optional)",
        "consent": "I agree that my anonymous response may be used to improve "
                   "this CultureBridge demo.",
        "submit_feedback": "Submit anonymous feedback",
        "no_personal_info": "Please do not include your name, email or other "
                            "personal information.",
        "consent_required": "Please tick the consent box before submitting.",
        "feedback_thanks": "Thank you! Your anonymous feedback has been saved.",
        "feedback_save_failed": "Sorry, your feedback could not be saved. "
                                "Please try again later.",

        # ---- Tester page ----
        "tester_bad_link": "This feedback link is not valid.",
        "tester_not_found": "We couldn't find this post. The link may have "
                            "expired, so please check with the person who "
                            "sent it to you.",
        "tester_title": "Quick feedback on a short post about Chinese tea culture",
        "tester_intro": "This takes about a minute: read the post below, then "
                        "answer three short questions. Your answers are "
                        "anonymous and are only used to improve the content. "
                        "The post is an AI-assisted draft.",
        "tester_form_title": "What did you think?",
        "tester_footer": "CultureBridge is an AI-assisted cross-cultural "
                         "communication prototype. Ratings are voluntary and "
                         "anonymous.",

        # ---- Sidebar ----
        "sidebar_tagline": "AI cross-cultural content co-creation prototype",
        "sidebar_flow_title": "Workflow",
        "sidebar_flow": (
            "1. Pick a topic, platform and style; generate and edit the post\n"
            "2. Check the cultural facts against sources, claim by claim\n"
            "3. Send the test link to target readers and collect feedback\n"
            "4. Review the feedback summary and iterate"
        ),
        "sidebar_disclaimer": "AI output is only a draft. Always verify "
                              "cultural facts before publishing.",

        # ---- Title ----
        "subtitle": "Tea Culture Explorer · 中国茶文化探索",
        "intro": "Turn cultural knowledge into social content that is "
                 "engaging, discussable and worth sharing.",
        "audience_caption": "Target audience: young professionals in the UK | "
                            "Goal: spark curiosity and further learning",

        # ---- Step 1 ----
        "step1_title": "🎯 Create a cultural post",
        "angle_label": "Choose a cultural angle",
        "platform_label": "Choose a platform",
        "style_label": "Choose a style",
        "extra_label": "Extra idea (optional)",
        "extra_placeholder": "e.g. mention an afternoon tea break at the office",
        "generate_btn": "✨ Generate post",
        "generate_caption": "Output is an AI draft; verify cultural facts "
                            "before publishing.",
        "no_api_key": "No API key found. Locally, check your .env file; on "
                      "Streamlit Cloud, add DEEPSEEK_API_KEY under Secrets.",
        "err_auth": "The API key is invalid or has expired. Check the key in "
                    "Secrets or .env.",
        "err_rate": "Too many requests or the account quota is used up. "
                    "Please try again later.",
        "err_timeout": "The model took too long to respond. Please try once more.",
        "err_conn": "Could not reach the model service. Check your network "
                    "and try again.",
        "err_other": "The model call failed; details were written to the log.",
        "err_empty": "The model returned nothing. Please try again.",
        "spinner": "Writing the post…",

        # ---- Display / edit / refine ----
        "post_heading": "📝 Your post",
        "post_empty": "👈 Choose your options and click “Generate post”.",
        "words_over": "About {n} words, over the {limit}-word target. "
                      "Consider shortening it.",
        "words_ok": "About {n} words (target: under {limit})",
        "edit_expander": "✏️ Edit the post by hand",
        "edit_label": "English post (the claims checklist, test link and "
                      "feedback all follow your edited version)",
        "edit_hint": "Your changes show up in the card above straight away.",
        "refine_title": "Ask the model to revise",
        "refine_custom_label": "Or write your own revision request",
        "refine_custom_placeholder": "e.g. open with an office scene",
        "refine_apply": "Revise with this request",
        "view_translation": "📖 Chinese translation",
        "none_translation": "No translation yet.",
        "view_rationale": "💡 Cultural framing notes",
        "none_rationale": "No notes yet.",
        "view_model_review": "🧾 Claims the model suggests checking",
        "none_review": "No suggestions yet.",

        # ---- Tabs ----
        "tab_review": "🔎 Fact review",
        "tab_test": "🧪 Audience test",
        "tab_overview": "📊 Feedback summary",

        # ---- Review ----
        "review_intro": "Look at reference sources, check each flagged claim, "
                        "and record the human review status. A source "
                        "existing does not mean it supports every sentence.",
        "review_empty": "Generate a post first, then review it against sources.",
        "risk_title": "Risk hints",
        "risk_caption": "These are keyword-based hints, not automated fact checking.",
        "sources_title": "Reference sources",
        "claims_title": "Claims to verify",
        "claims_intro": "These are the claims the model says need checking. "
                        "Confirm each one against a source, then tick it.",
        "claims_stale": "You have edited the post, so this list is based on "
                        "the AI draft. Add any new claims yourself.",
        "claims_none": "The model gave no separable claims; record your "
                       "checks in the note instead.",
        "claims_progress": "{done} / {total} claims confirmed",
        "record_title": "Human review record",
        "checked_sources_label": "Which sources did you actually check?",
        "status_label": "Review status of this version",
        "status_pending": "Awaiting human review",
        "status_partial": "Sources checked, some claims still open",
        "status_verified": "Human-verified (this version)",
        "note_label": "Reviewer note (e.g. check the tea type, region or "
                      "brewing method)",
        "note_placeholder": "Write down facts to verify or changes to make…",
        "verify_open_claims": "You marked this as human-verified, but {n} "
                              "claim(s) are still unconfirmed.",
        "verify_no_sources": "You marked this as human-verified, but no "
                             "checked sources are selected.",
        "verify_done": "Marked as human-verified; every listed claim is confirmed.",
        "verify_partial": "Some claims are still open; do not publish yet.",
        "verify_pending": "This version has not been reviewed yet.",
        "save_review_btn": "Save this review",
        "review_saved": "Review saved.",
        "review_save_failed": "The review could not be saved. Please try again later.",

        # ---- Audience test (creator page) ----
        "test_intro": "Send the test link to target readers (UK young "
                      "professionals); they get an English rating page. You "
                      "can also fill the form in here during an in-person test.",
        "test_empty": "Generate a post first, then run an audience test.",
        "share_title": "Share a test link",
        "share_intro": "The link points to the current version of the post, "
                       "including your manual edits. Create a new link after "
                       "editing.",
        "share_btn": "🔗 Create audience test link",
        "share_local_warning": "You are using temporary local storage: the "
                               "link and feedback will be lost when the app "
                               "restarts. Configure Supabase before real tests.",
        "share_stale": "The post has changed, so the earlier link points to an "
                       "older version. Click the button again for a new link.",
        "inpage_title": "In-person test: fill in here",
        "inpage_intro": "Handy when someone is looking at your screen. The "
                        "rating is recorded against the current version.",

        # ---- Overview ----
        "overview_load_failed": "Feedback data cannot be loaded right now.",
        "overview_empty": "No feedback saved yet. Submit a few test responses "
                          "and the summary will appear here.",
        "scope_label": "Scope",
        "scope_all": "All versions",
        "scope_current": "Current version only",
        "overview_none_for_version": "No feedback for the current version yet.",
        "metric_count": "Responses",
        "metric_interest": "Avg. interest",
        "metric_understanding": "Avg. understanding",
        "metric_learn_more": "Want to learn more",
        "chart_avg": "Average score",
        "chart_interest": "Interest",
        "chart_understanding": "Understanding",
        "chart_learn_more": "Learn more",
        "sample_tiny": "Only {n} response(s) so far; treat the numbers as "
                       "hints for iteration only.",
        "sample_small": "Small-sample results are only a guide and do not "
                        "represent all UK young professionals.",
        "by_version_title": "Versions compared",
        "col_version": "Version",
        "col_n": "Responses",
        "storage_note_supabase": "Feedback is stored in a Supabase database.",
        "storage_note_local": "Feedback is stored in CSV files on the app "
                              "server and may be wiped when the cloud app "
                              "restarts or redeploys; export important data.",

        # ---- Admin ----
        "admin_title": "🔐 Admin: raw records / CSV download",
        "admin_not_set": "ADMIN_KEY is not set. Add it to .env or Streamlit "
                         "Secrets to view and download raw records here.",
        "admin_password": "Admin password",
        "admin_feedback": "Audience feedback",
        "admin_reviews": "Fact reviews",
        "admin_download": "Download {name}",
        "admin_no_records": "No records yet.",
        "admin_wrong": "Incorrect password.",

        "footer": "CultureBridge Demo · an AI-assisted cross-cultural "
                  "communication prototype. Fact checking needs human "
                  "judgement; audience ratings are voluntary feedback.",
    },
}


def translate(lang, key, **kwargs):
    """取文案；语言缺失时退回中文，键缺失时返回键名并记录。"""
    table = STRINGS.get(lang) or STRINGS["zh"]
    text = table.get(key)

    if text is None:
        text = STRINGS["zh"].get(key)

    if text is None:
        MISSING.add(key)
        return key

    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return text

    return text
