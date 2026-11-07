# CultureBridge 部署与 Ember Lab 接入

推荐 **Streamlit Community Cloud**：保留 Python 3.12、Streamlit 长进程、WebSocket 会话与现有 Secrets 管理，无需重写为前端。是否符合当前免费额度及使用条款，请在部署账户中确认。本轮未购买或启用任何服务，也未执行正式部署。

Vercel 的常规函数执行模型不适合直接托管此 Streamlit 长进程；还涉及 WebSocket、超时、临时磁盘问题。Ember Lab 在 Vercel 不要求所有交互项目都部署到 Vercel。首版用外链接入即可，无需 iframe 或域名配置。

## 本地运行

```bash
cd culturebridge
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip check
python -m pytest -q
python -m streamlit run app.py
```

生产只需 `pip install -r requirements.txt`。`requirements.lock` 固定本次验证的运行依赖；开发依赖另含 pytest。更新依赖时重新运行测试与浏览器检查。无需 Node 或 Docker。

不设置任何密钥即可体验 Demo，默认中国茶文化、Instagram、英国年轻职场人。Demo 为人工示例，不访问 API，额外偏好不参与生成；可手动编辑。真实 AI 模式使用原有 DeepSeek OpenAI SDK 兼容接口，默认 `deepseek-chat`，没有更换提供商。

## 服务端配置

| 变量 | 用途 | 是否必需 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | DeepSeek 请求认证，仅发往 `https://api.deepseek.com` | 仅真实生成 |
| `OPENAI_API_KEY` | 历史变量名兼容，仍请求 DeepSeek；不能用它切换提供商 | 不推荐新配置使用 |
| `CULTUREBRIDGE_MODEL` | 默认 `deepseek-chat`，须为当前提供商支持的模型 | 否 |
| `APP_URL` | 此次部署的实际 HTTPS 根地址，用于测试链接；空时禁止生成链接 | 分享测试链接需要 |
| `SESSION_LIMIT` / `DAILY_LIMIT` | 默认 15 / 200；仅限制真实生成，是额度护栏而非防刷认证 | 否 |
| `ADMIN_KEY` | 查看其他访客原始反馈与审核 CSV 的管理员口令 | 管理员功能需要 |
| `SUPABASE_URL` / `SUPABASE_KEY` | 已有 Supabase 服务的 URL 和服务端密钥，两项都设置才启用 | 否 |

在部署平台的服务端 Secrets／环境变量设置。Streamlit Cloud 使用 Secrets TOML，例如 `DEEPSEEK_API_KEY = "在平台安全填写"`；不要把实际值放在 README、源代码或浏览器里。代码保留本地 `.env` 和 Streamlit Secrets 兼容；`.env`、`.streamlit/secrets.toml` 及生成数据均被忽略。模型错误日志仅记异常类别，不输出服务端响应或密钥。不要在日志中手工打印环境变量。

## 免费轻量反馈保存

默认仍使用 `generations.csv`、`audience_feedback.csv`、`fact_review_log.csv`，不使用 JSONL。本地文件适合开发，云主机重启、重新部署或副本切换时不可靠，不能当作长期数据库。

每位用户提交反馈后，可下载**自己当前会话**的 CSV（包含短帖快照、版本、Interest、Understanding、Respect、补充了解意愿和自由意见）。不需要管理员口令；不能下载别人的自由文本。服务器写入失败时，会话副本仍可下载。请立即保存到自己的设备；刷新或断线后会话可能消失。此方案不提供跨设备同步或长期问卷收集保证。没有引入浏览器 localStorage 或偷偷记录个人数据。

需要正式跨访客持续收集时，可继续使用仓库已有的 Supabase 后端：

1. 使用现有项目或自行评估可用免费额度，不必购买套餐。
2. 先备份数据，在 SQL Editor 执行 `supabase_schema.sql`。末尾是增量 `respect` 字段迁移；旧数据保持 NULL，不伪造历史评分。既有部署也必须先执行迁移，再部署新代码。
3. 在 Secrets 设置项目 URL 和服务端密钥。公开 anon/publishable key 不适用。三张表开启 RLS，无公共访问策略；应用凭服务端密钥访问。
4. 验证重启后测试链接、短帖与反馈仍存在。未执行真实 Supabase 连接验证前，不宣称长期存储就绪。

旧本地 CSV 首次追加时原子补齐缺失列，保留原始行、额外字段和旧 timestamp；旧 Respect 留空。进程内锁防止同一进程多个会话同时迁移或写入；不支持跨进程／多副本数据库级并发保证。

## Community Cloud 发布步骤

1. 审阅并合并 `codex/culturebridge-phase-3-4`，或在独立预发布应用中选该分支。不要把未合并分支误认为 main 已更新。
2. 在 Streamlit Community Cloud 选择 `wenyimarius-ship-it/culturebridge`、目标分支、入口 `app.py`，高级设置选择 Python 3.12。
3. 可先不配置模型密钥部署 Demo；若启用真实生成，将已有 DeepSeek 密钥安全填入 Secrets。新 API 调用可能消耗已有提供商余额。
4. 如用 Supabase，先执行上述 schema 迁移；不用则采用用户 CSV 导出，并保留临时存储提示。
5. 获取平台实际提供的 HTTPS 地址，设置 `APP_URL`，重启应用。勿复用另一部署地址。
6. 在该**实际公网地址**检查：无密钥 Demo、生成／复制、Cultural Lens 待核验状态、Audience Lab 提交与下载、手机端、重启后存储语义；若启用 AI，再检查真实生成。
7. 所有需要的公网检查通过后，才标记已上线。本轮没有登录部署平台或发布应用；README 中历史地址不能证明新分支已部署。

## Ember Lab 接入数据（由 Ember Lab 后续独立任务修改）

| 字段语义 | 发布前 | 公网验证通过后 |
| --- | --- | --- |
| 名称 | CultureBridge | CultureBridge |
| URL | 留空，不启用跳转 | Streamlit 实际提供并验收的 HTTPS 根地址 |
| 状态 | `deployment-pending` | `live` |
| 描述 | 中国茶文化内容共创 · Demo 与 AI 模式 | 同左，按实际是否配置密钥注明 |
| 返回链接 | `https://lab.mariustang.com` | 同左 |

以上字段为语义建议，不假定 Ember Lab 的实际配置 schema。已有历史候选地址：`https://culturebridge-dwbxqchgzdremscutzk5eh.streamlit.app/`，本轮未验证该地址状态或其部署版本。不要在新版本验收前将其冒充本次交付 URL。本任务不更改 Ember Lab、DNS、Cloudflare 或任何域名绑定。

## 可选真实浏览器回归

`python -m pytest -q` 不依赖 Playwright。浏览器回归脚本需单独安装 `playwright==1.62.0`，并准备 Chromium（系统 `chromium` 或 `python -m playwright install chromium`）。脚本会实际提交测试反馈，必须针对隔离的本地测试实例，勿直接对生产问卷执行。

```bash
# 在另一个终端，使用不含 .env / Secrets 的临时目录，避免读取真实配置与写入正式数据
mkdir -p /tmp/culturebridge-smoke
cp app.py cb_core.py cb_store.py cb_demo.py i18n.py /tmp/culturebridge-smoke/
env -u DEEPSEEK_API_KEY -u OPENAI_API_KEY -u SUPABASE_URL -u SUPABASE_KEY \
  .venv/bin/python -m streamlit run /tmp/culturebridge-smoke/app.py --server.port=8501

# 安装 Playwright 的 Python 环境中执行
python scripts/browser_smoke.py --url http://127.0.0.1:8501
```

检查移动端生成、真实剪贴板内容、待核验状态、审核保存、反馈提交与 CSV 下载，以及 360 / 390 / 1280px 页面横向溢出。默认输出证据到临时目录，不提交问卷数据到仓库。
