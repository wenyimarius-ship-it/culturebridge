-- CultureBridge 的 Supabase 建表脚本
-- 用法：Supabase 控制台 → SQL Editor → 粘贴整段 → Run
--
-- 安全模型：
--   * 三张表都开启 Row Level Security，并且不创建任何策略。
--   * 这样 anon / authenticated 角色（也就是公开的 publishable key）完全读写不了。
--   * 应用只用服务端密钥（secret key，或旧版 service_role key）访问，
--     该密钥绕过 RLS。它只能放在 Streamlit Secrets / .env 里，绝不能提交到 GitHub。

-- ---------- 1. 每次生成 / 修改 / 追加要求产生的短帖版本 ----------
create table if not exists public.generations (
    id          bigint generated always as identity primary key,
    created_at  timestamptz not null default now(),
    version     text        not null,
    topic       text,
    platform    text,
    style       text,
    kind        text        not null default 'generate',  -- generate / refine / edit
    model       text,
    post        text        not null
);

create index if not exists generations_version_idx    on public.generations (version);
create index if not exists generations_created_at_idx on public.generations (created_at);

-- ---------- 2. 受众反馈 ----------
create table if not exists public.feedback (
    id             bigint generated always as identity primary key,
    created_at     timestamptz not null default now(),
    post_version   text        not null,
    topic          text,
    platform       text,
    lang           text,
    post_text      text,
    interest       smallint    not null check (interest between 1 and 5),
    understanding  smallint    not null check (understanding between 1 and 5),
    learn_more     smallint    not null check (learn_more between 1 and 5),
    confusing_part text,
    comment        text
);

create index if not exists feedback_post_version_idx on public.feedback (post_version);

-- ---------- 3. 人工事实审核记录 ----------
create table if not exists public.fact_reviews (
    id                  bigint generated always as identity primary key,
    created_at          timestamptz not null default now(),
    post_version        text        not null,
    topic               text,
    verification_status text,
    checked_sources     text,
    claims_confirmed    text,
    claims_open         text,
    reviewer_note       text,
    post_text           text
);

create index if not exists fact_reviews_post_version_idx on public.fact_reviews (post_version);

-- ---------- 4. 行级安全：开启且不加策略 = 公开密钥一律拒绝 ----------
alter table public.generations  enable row level security;
alter table public.feedback     enable row level security;
alter table public.fact_reviews enable row level security;
