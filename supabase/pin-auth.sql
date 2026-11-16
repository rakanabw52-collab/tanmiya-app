-- Server-only PIN registry. No browser role can read hashes, register a PIN, or bypass throttling.
create schema if not exists hd_private;
revoke all on schema hd_private from public, anon, authenticated;
grant usage on schema hd_private to service_role;
create table hd_private.pin_credentials (
 user_id uuid primary key references auth.users(id) on delete cascade,
 pin_digest text not null unique check (pin_digest ~ '^[a-f0-9]{64}$'),
 updated_at timestamptz not null default now()
);
create table hd_private.pin_attempts (
 bucket text primary key, started_at timestamptz not null, attempts integer not null check(attempts>=0)
);
alter table hd_private.pin_credentials enable row level security;
alter table hd_private.pin_attempts enable row level security;
revoke all on all tables in schema hd_private from public, anon, authenticated;
grant select,insert,update,delete on all tables in schema hd_private to service_role;

create function public.hd_pin_claim(p_digest text, p_client text)
returns jsonb language plpgsql security invoker set search_path = '' as $$
declare k text; lim integer; span interval; rec record; uid uuid; wait_seconds integer:=0;
begin
 perform pg_catalog.pg_advisory_xact_lock(1147,1);
 for k,lim,span in select * from (values
  ('ip:'||p_client,5,interval '15 minutes'),('global:hour',10,interval '1 hour'),('global:day',30,interval '1 day')
 ) as v(k,lim,span) loop
  select * into rec from hd_private.pin_attempts where bucket=k;
  if found and rec.started_at+span>now() and rec.attempts>=lim then
   wait_seconds:=greatest(wait_seconds,ceil(extract(epoch from rec.started_at+span-now()))::integer);
  end if;
 end loop;
 if wait_seconds>0 then return jsonb_build_object('retry_after',wait_seconds); end if;
 for k,lim,span in select * from (values
  ('ip:'||p_client,5,interval '15 minutes'),('global:hour',10,interval '1 hour'),('global:day',30,interval '1 day')
 ) as v(k,lim,span) loop
  insert into hd_private.pin_attempts as a values(k,now(),1)
  on conflict(bucket) do update set attempts=case when a.started_at+span<=now() then 1 else a.attempts+1 end,
   started_at=case when a.started_at+span<=now() then now() else a.started_at end;
 end loop;
 delete from hd_private.pin_attempts where started_at<now()-interval '2 days';
 select c.user_id into uid from hd_private.pin_credentials c join public.profiles p on p.id=c.user_id
 where c.pin_digest=p_digest and p.role in ('owner','accountant');
 return jsonb_build_object('user_id',uid,'retry_after',0);
end $$;
create function public.hd_pin_success(p_client text) returns void
language plpgsql security invoker set search_path='' as $$
begin
 perform pg_catalog.pg_advisory_xact_lock(1147,1);
 update hd_private.pin_attempts set attempts=greatest(0,attempts-1)
 where bucket in ('ip:'||p_client,'global:hour','global:day');
end $$;
create function public.hd_pin_register(p_uid uuid,p_digest text) returns boolean
language plpgsql security invoker set search_path='' as $$
begin
 if not exists(select 1 from public.profiles where id=p_uid and role in ('owner','accountant')) then return false; end if;
 insert into hd_private.pin_credentials(user_id,pin_digest) values(p_uid,p_digest)
 on conflict(user_id) do update set pin_digest=excluded.pin_digest,updated_at=now();
 return true;
exception when unique_violation then return false;
end $$;
revoke all on function public.hd_pin_claim(text,text),public.hd_pin_success(text),public.hd_pin_register(uuid,text) from public,anon,authenticated;
grant execute on function public.hd_pin_claim(text,text),public.hd_pin_success(text),public.hd_pin_register(uuid,text) to service_role;

-- An authorized account cannot enumerate the short shared PIN namespace through registration collisions.
create function public.hd_pin_register_guard(p_uid uuid) returns integer
language plpgsql security invoker set search_path='' as $$
declare k text:='register:'||p_uid::text; rec record;
begin
 perform pg_catalog.pg_advisory_xact_lock(1147,2);
 select * into rec from hd_private.pin_attempts where bucket=k;
 if found and rec.started_at+interval '1 hour'>now() and rec.attempts>=5 then
  return ceil(extract(epoch from rec.started_at+interval '1 hour'-now()))::integer;
 end if;
 insert into hd_private.pin_attempts as a values(k,now(),1)
 on conflict(bucket) do update set attempts=case when a.started_at+interval '1 hour'<=now() then 1 else a.attempts+1 end,
  started_at=case when a.started_at+interval '1 hour'<=now() then now() else a.started_at end;
 return 0;
end $$;
revoke all on function public.hd_pin_register_guard(uuid) from public,anon,authenticated;
grant execute on function public.hd_pin_register_guard(uuid) to service_role;
