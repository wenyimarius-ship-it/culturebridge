-- Fresh-project schema. Hosted migration: ember_private_cloud_documents.
create table public.ember_cloud_documents (
 site text not null check (site in ('puzzle','city','cinema')),
 owner_hash text not null check (owner_hash ~ '^[a-f0-9]{64}$'),
 payload jsonb not null check (jsonb_typeof(payload)='object' and octet_length(payload::text)<=300000),
 revision bigint not null default 1 check (revision>0),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 primary key(site,owner_hash)
);
alter table public.ember_cloud_documents enable row level security;
grant select,insert,update,delete on public.ember_cloud_documents to service_role;
-- No policies for anon/authenticated. Access only via authenticated recovery
-- capabilities validated by the server-side ember-vault Edge Function.
