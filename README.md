# 🍵 CultureBridge

**An AI-assisted prototype for co-creating cross-cultural social content — starting with Chinese tea culture for young professionals in the UK.**

CultureBridge 是一个面向英国年轻职场人、以中国茶文化为切入点的 AI 跨文化内容共创原型。它不是"一键生成文案"的工具，而是一条把**内容生成 → 文化审核 → 受众反馈**串起来的工作流：AI 负责起草，人负责判断文化事实，目标读者负责告诉你这段话到底有没有读懂、愿不愿意了解更多。

**在线演示：** https://culturebridge-dwbxqchgzdremscutzk5eh.streamlit.app/

<!--
截图放这里（建议 3 张：生成页、事实审核页、受众测试页），放到 docs/screenshots/ 后取消注释：

![生成页](docs/screenshots/generate.png)
![事实审核](docs/screenshots/review.png)
![受众测试](docs/screenshots/audience-test.png)
-->

---

## 项目背景

用大语言模型写社交媒体文案很容易，难的是三件事：

1. **读者是谁**：写给英国年轻职场人的内容，语气、平台习惯和文化背景都和写给国内读者不同。
2. **事实对不对**：关于文化的内容最容易出现"一概而论"、异域化、编造起源等问题，而模型写得越流畅，这些问题越不容易被发现。
3. **读者怎么想**：作者觉得好，不等于目标读者读得懂、愿意进一步了解。

CultureBridge 把这三件事做成一个可以反复迭代的流程，并且把"人工判断"留在每个关键环节里，而不是假装 AI 已经替你核实了。

## 工作流

```
 选择主题 / 平台 / 风格
          │
          ▼
 ① 生成英文短帖（可手动修改、可让模型"更短 / 更幽默"等继续改）
          │
          ▼
 ② 文化事实审核：关键词风险提示 + 参考来源 + 待核实清单逐条勾选
          │
          ▼
 ③ 受众测试：生成测试链接发给目标读者，他们在英文页面里打分
          │
          ▼
 ④ 反馈概览：按版本对比兴趣度 / 理解度 / 了解意愿，迭代下一版
```

## 功能

**内容生成**
- 5 个文化切入点 × 2 个平台（Instagram / LinkedIn）× 3 种文风，针对平台和文风分别给出写作指引。
- Prompt 明确要求：用英式英语、聚焦一个文化点、不编造历史和来源、不做健康功效声明、避免"神秘东方"式的异域化套话、避免把个别做法说成"所有中国人"。
- 短帖可以**手动修改**；也可以点"更短 / 更幽默 / 更有深度 / 更贴近职场"，或写一条自己的修改要求，让模型在**当前文本**基础上继续改。
- 显示词数，超出 100 词会提醒。
- 同时给出中文翻译、文化表达思路，方便非英语母语的创作者判断措辞。

**文化事实审核**
- 基于关键词的风险提示（绝对化表达、起源/"最早"说法、科学与健康声明、异域化词汇等）。**这只是提示，不是事实核查。**
- 把模型列出的"需要核实的内容"拆成**逐条勾选的清单**，并记录实际核对了哪些来源。
- 审核记录会保存"已确认 / 仍待核实"的条目；如果还有未确认条目，却把状态标成"已人工核验"，页面会警告。
- 审核状态按版本区分，重新生成或修改后不会沿用上一版的结论。

**受众测试**
- 一键生成**测试链接**（`/?t=<版本号>`）。目标读者打开后看到的是一个**英文页面**：一条短帖 + 三个评分问题 + 两个选填问题，约 1 分钟。
- 评分对应的是**修改后的那一版**短帖，原文随反馈一起保存，之后改动不会让历史数据对不上。
- 也支持当面测试：直接在创作者页面里填写。
- 匿名，提交前需勾选同意。

**反馈概览**
- 平均兴趣度 / 理解度 / 了解意愿，可切换"全部版本 / 仅当前版本"，并提供各版本对比。
- 样本量很小时会明确提示"仅供迭代参考"。

**其他**
- 创作者界面支持**中文 / English 切换**；测试页默认英文。
- **额度保护**：每次访问的生成次数上限 + 全站每日上限，避免公开演示耗尽 API 额度。
- 管理员口令保护的原始记录查看与 CSV 下载。

## 本地运行

```bash
git clone https://github.com/wenyimarius-ship-it/culturebridge.git
cd culturebridge
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env        # 然后填写 DEEPSEEK_API_KEY
streamlit run app.py
```

不配置 Supabase 也能跑：数据会写到本地 CSV（`generations.csv`、`audience_feedback.csv`、`fact_review_log.csv`，已在 `.gitignore` 中）。

## 配置项

本地写在 `.env`，部署在 Streamlit Cloud 时写在 **App settings → Secrets**（TOML 格式，值要加引号）。

| 键 | 必填 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 是 | 模型 API Key（也可用 `OPENAI_API_KEY`，需兼容 OpenAI 接口） |
| `ADMIN_KEY` | 否 | 管理员口令；不设置则页面里看不到原始反馈 |
| `SUPABASE_URL` / `SUPABASE_KEY` | 否 | 两项都填才启用持久存储；`SUPABASE_KEY` 必须是**服务端密钥** |
| `APP_URL` | 否 | 应用公开网址，用于拼接测试链接 |
| `SESSION_LIMIT` | 否 | 每次访问的生成上限，默认 15 |
| `DAILY_LIMIT` | 否 | 全站每日生成上限，默认 200 |
| `CULTUREBRIDGE_MODEL` | 否 | 更换模型，默认 `deepseek-chat` |

## 数据持久化（Supabase，推荐正式测试前配置）

Streamlit Cloud 的磁盘是临时的：应用重启或重新部署后，本地 CSV 会被清空，测试链接也会失效。早期版本只把数据写进 CSV，作者在后台看不到、也无法可靠汇总各位访客提交的反馈，因此后来加入了 Supabase 存储层。要认真收集反馈，请接 Supabase：

1. 在 [Supabase](https://supabase.com) 新建项目。
2. 打开 **SQL Editor**，粘贴并运行 [`supabase_schema.sql`](supabase_schema.sql)。
3. 在 **Project Settings → API Keys** 复制项目 URL 和 **secret key**（旧版叫 `service_role`）。
4. 把 `SUPABASE_URL` 和 `SUPABASE_KEY` 填进 Streamlit Secrets，重启应用。侧边栏会显示"数据存储：Supabase"。

**安全说明：** 三张表都开启了行级安全（RLS）且**没有任何策略**，所以公开的 publishable / anon key 完全读写不了这些表。应用只使用服务端密钥访问，该密钥**只能放在 Secrets / `.env` 里，绝不要提交到 GitHub，也不要用在前端**。

## 部署到 Streamlit Cloud

1. 把仓库推到 GitHub。
2. 在 [share.streamlit.io](https://share.streamlit.io) 新建应用，选择仓库和 `app.py`。
3. 在 **Advanced settings → Secrets** 填入上面的配置项。
4. 部署后，把 `APP_URL` 设成应用的实际网址，测试链接才会指向正确地址。

## 测试

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

- `tests/test_core.py`：解析模型输出、风险关键词、核实清单拆分、Prompt 构造、CSV 防注入、评分汇总。
- `tests/test_store.py`：本地与 Supabase 两种存储后端（用假的 HTTP 会话，不联网）。
- `tests/test_i18n.py`：中英文文案键与占位符一致，`app.py` 用到的键都存在。
- `tests/test_app_smoke.py`：用替身 Streamlit / OpenAI 把 `app.py` 整个脚本真正执行一遍，覆盖生成、追加要求、手动修改、测试链接、反馈保存、审核记录、额度上限、管理员口令等流程。

GitHub Actions 会在每次推送时自动运行（见 `.github/workflows/tests.yml`）。冒烟测试验证的是脚本逻辑和数据流，**不验证真实浏览器里的排版**，界面仍需要人眼检查。

## 项目结构

```
app.py                 Streamlit 界面与流程
cb_core.py             核心逻辑（不依赖 Streamlit）：解析、风险提示、Prompt、统计
cb_store.py            存储层：本地 CSV / Supabase，接口一致
i18n.py                中文 / English 界面文案
supabase_schema.sql    Supabase 建表与行级安全
tests/                 单元测试与冒烟测试
```

## 隐私与安全设计

- 受众反馈匿名，提交前需勾选同意，页面提示不要填写姓名、邮箱等个人信息。
- 原始反馈（含自由文本）**不对公开访客展示**，只有输入管理员口令才能查看和下载。
- CSV 导出对以 `=` `+` `-` `@` 开头的单元格加转义，防止在 Excel 中被当作公式执行。
- 用户输入（补充想法、修改要求、手动修改后的短帖）都限制长度，并在 Prompt 中被明确标注为"内容而非指令"，降低提示词注入的影响。
- 存储层的错误信息不会把服务端返回的细节或密钥展示给用户。
- 注意：生成内容会发送给第三方模型服务（DeepSeek）处理，请勿输入敏感信息。

## 已知局限

- **风险提示不是事实核查。** 关键词命中不等于错误，未命中也不等于正确。"待核实清单"来自模型自己的判断，模型可能遗漏它没意识到的错误。真正的核验必须由人对照来源完成。
- **参考来源是通用资料**，来源存在不代表它支持文案里的每一句话。
- **测试链接任何人拿到都能打开并提交**，没有防刷、去重或身份校验；匿名意味着同一个人可以重复提交。
- **全站每日上限**依赖存储里的记录，且只在页面层面限制；它是保护额度的"护栏"，不是防滥用方案。每次访问的上限刷新页面即可重置。
- **样本很小。** 少量志愿者的评分只能当作迭代线索，不能代表"英国年轻职场人"这个群体。
- 模型生成的英文是否"地道"，目前没有以英国母语者为准的系统评估。
- 目前只覆盖中国茶文化一个主题，平台限于 Instagram 和 LinkedIn。
- Streamlit Cloud 免费实例闲置后会休眠，首次访问可能需要几十秒唤醒。

## 后续方向

- 让英国母语读者参与"措辞是否自然、是否冒犯"的评审，而不只是打分。
- 为核实清单关联具体来源段落，而不是只记录"看过哪些来源"。
- 支持更多文化主题、更多平台，以及同一主题下的 A/B 版本对比。
- 受众测试加入简单的防重复与来源标记。

## 作者

本项目由 AI 辅助生成，作者杨衔旭负责的部分是：

- **需求与方向**：结合自己的求职方向，提出"AI × 文化"的切入点，以及"生成 → 审核 → 反馈"的流程思路；
- **页面与交互迭代**：试用中发现早期交互不顺手，逐轮提出修改意见，反复调整直到流程走通；
- **部署与数据回收**：把应用部署到 Streamlit Cloud，并排查、解决反馈数据无法留存的问题（见上文"数据持久化"）。

代码主要由 AI 生成，我在持续学习并尝试读懂其中的结构（存储层、测试、安全设计等）。项目持续迭代中，目前还没有系统的真实用户测试数据。
