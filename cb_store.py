"""CultureBridge 数据存储层。

两种后端，接口完全一致：
- LocalStore：写本地 CSV。无需配置，但在 Streamlit Cloud 上重启后会被清空。
- SupabaseStore：写 Supabase（PostgREST），数据持久保存。

设置了 SUPABASE_URL 和 SUPABASE_KEY 时自动使用 Supabase。
"""

import csv
import re
from datetime import datetime, timezone
from pathlib import Path

import cb_core as core

GENERATION_FIELDS = [
    "created_at", "version", "topic", "platform", "style",
    "kind", "model", "post",
]

FEEDBACK_FIELDS = [
    "created_at", "post_version", "topic", "platform", "lang", "post_text",
    "interest", "understanding", "learn_more", "confusing_part", "comment",
]

REVIEW_FIELDS = [
    "created_at", "post_version", "topic", "verification_status",
    "checked_sources", "claims_confirmed", "claims_open",
    "reviewer_note", "post_text",
]

# 这些字段保存的是短帖原文，写入时不加转义前缀，避免读回来时文本被改动。
# 导出 CSV 时由 core.rows_to_csv_bytes 统一做公式注入防护。
RAW_TEXT_FIELDS = {"post", "post_text"}


class StoreError(Exception):
    """存储失败。消息里不包含服务端返回的细节，避免泄露信息。"""


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def today_prefix():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# =====================================================
# 本地 CSV
# =====================================================

class LocalStore:
    kind = "local"

    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.generations_file = self.base_dir / "generations.csv"
        self.feedback_file = self.base_dir / "audience_feedback.csv"
        self.review_file = self.base_dir / "fact_review_log.csv"

    # ---- 底层读写 ----

    @staticmethod
    def _read(path):
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8-sig", newline="") as f:
                return list(csv.DictReader(f))
        except (OSError, csv.Error):
            return []

    @staticmethod
    def _append(path, fields, row):
        row = dict(row)
        row.setdefault("created_at", now_iso())

        use_fields = fields
        exists = path.exists() and path.stat().st_size > 0

        # 文件已存在时沿用它原来的表头，避免旧文件与新列错位
        if exists:
            try:
                with open(path, "r", encoding="utf-8-sig", newline="") as f:
                    header = next(csv.reader(f), None)
                if header:
                    use_fields = header
            except (OSError, csv.Error):
                pass

        if "timestamp" in use_fields and "created_at" not in use_fields:
            row.setdefault("timestamp", row["created_at"])

        clean = {
            key: value if key in RAW_TEXT_FIELDS else core.safe_cell(value)
            for key, value in row.items()
        }

        try:
            with open(path, "a", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=use_fields, extrasaction="ignore"
                )
                if not exists:
                    writer.writeheader()
                writer.writerow(clean)
        except OSError as e:
            raise StoreError("local write failed") from e

    # ---- 对外接口 ----

    def log_generation(self, row):
        self._append(self.generations_file, GENERATION_FIELDS, row)

    def save_feedback(self, row):
        self._append(self.feedback_file, FEEDBACK_FIELDS, row)

    def save_review(self, row):
        self._append(self.review_file, REVIEW_FIELDS, row)

    def get_post(self, version):
        for row in reversed(self._read(self.generations_file)):
            if row.get("version") == version:
                return row
        return None

    def list_feedback(self, version=None):
        rows = self._read(self.feedback_file)
        if version:
            rows = [r for r in rows if r.get("post_version") == version]
        return rows

    def list_reviews(self):
        return self._read(self.review_file)

    def count_today(self):
        prefix = today_prefix()
        return sum(
            1
            for row in self._read(self.generations_file)
            if (row.get("created_at") or "").startswith(prefix)
            and row.get("kind") in ("generate", "refine")
        )


# =====================================================
# Supabase（PostgREST）
# =====================================================

class SupabaseStore:
    kind = "supabase"

    def __init__(self, url, key, session=None, timeout=10):
        if session is None:
            import requests  # 延迟导入：只有真正连 Supabase 时才需要
            session = requests.Session()

        self.base = url.rstrip("/") + "/rest/v1"
        self.session = session
        self.timeout = timeout

        self.headers = {"apikey": key, "Content-Type": "application/json"}
        # 旧版 JWT 形式的密钥需要同时放进 Authorization；新版 sb_secret_ 不需要
        if key.startswith("eyJ"):
            self.headers["Authorization"] = f"Bearer {key}"

    # ---- 底层请求 ----

    def _request(self, method, table, **kwargs):
        headers = dict(self.headers)
        headers.update(kwargs.pop("headers", {}))
        try:
            response = self.session.request(
                method,
                f"{self.base}/{table}",
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
        except Exception as e:  # 网络错误、超时等
            raise StoreError(f"{table}: network error") from e

        if response.status_code >= 300:
            raise StoreError(f"{table}: HTTP {response.status_code}")
        return response

    def _insert(self, table, row):
        self._request(
            "POST",
            table,
            json=row,
            headers={"Prefer": "return=minimal"},
        )

    def _select(self, table, params):
        return self._request("GET", table, params=params).json()

    # ---- 对外接口 ----

    def log_generation(self, row):
        self._insert("generations", row)

    def save_feedback(self, row):
        self._insert("feedback", row)

    def save_review(self, row):
        self._insert("fact_reviews", row)

    def get_post(self, version):
        if not core.valid_version(version):
            return None
        rows = self._select(
            "generations",
            {
                "select": "version,topic,platform,style,kind,post",
                "version": f"eq.{version}",
                "order": "id.desc",
                "limit": 1,
            },
        )
        return rows[0] if rows else None

    def list_feedback(self, version=None):
        params = {"select": "*", "order": "id.desc", "limit": 1000}
        if version:
            params["post_version"] = f"eq.{version}"
        return self._select("feedback", params)

    def list_reviews(self):
        return self._select(
            "fact_reviews",
            {"select": "*", "order": "id.desc", "limit": 1000},
        )

    def count_today(self):
        since = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
        response = self._request(
            "GET",
            "generations",
            params={
                "select": "id",
                "created_at": f"gte.{since}",
                "kind": "in.(generate,refine)",
            },
            headers={
                "Prefer": "count=exact",
                "Range-Unit": "items",
                "Range": "0-0",
            },
        )

        match = re.search(r"/(\d+)$", response.headers.get("Content-Range", ""))
        if match:
            return int(match.group(1))
        try:
            return len(response.json())
        except ValueError:
            return 0


def make_store(base_dir, supabase_url=None, supabase_key=None, session=None):
    """配置了 Supabase 就用 Supabase，否则退回本地 CSV。"""
    if supabase_url and supabase_key:
        return SupabaseStore(supabase_url, supabase_key, session=session)
    return LocalStore(base_dir)
