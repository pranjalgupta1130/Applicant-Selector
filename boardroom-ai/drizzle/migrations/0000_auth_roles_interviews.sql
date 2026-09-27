create type public.app_role as enum ('admin', 'candidate');

create table public.profiles (
  id uuid primary key,
  email text,
  full_name text,
  neurodivergent boolean,
  conditions text[] not null default '{}',
  created_at timestamptz not null default now()
);
grant select, insert, update on public.profiles to authenticated;
grant all on public.profiles to service_role;
alter table public.profiles enable row level security;

create table public.user_roles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null,
  role public.app_role not null,
  unique (user_id, role)
);
grant select on public.user_roles to authenticated;
grant all on public.user_roles to service_role;
alter table public.user_roles enable row level security;

create or replace function public.has_role(_user_id uuid, _role public.app_role)
returns boolean language sql stable security definer set search_path = public as $$
  select exists (select 1 from public.user_roles where user_id = _user_id and role = _role)
$$;

create policy "Own roles readable" on public.user_roles for select to authenticated
  using (user_id = auth.uid() or public.has_role(auth.uid(), 'admin'));

create policy "Own profile readable" on public.profiles for select to authenticated
  using (id = auth.uid() or public.has_role(auth.uid(), 'admin'));
create policy "Own profile insert" on public.profiles for insert to authenticated
  with check (id = auth.uid());
create policy "Own profile update" on public.profiles for update to authenticated
  using (id = auth.uid()) with check (id = auth.uid());

create or replace function public.ensure_profile()
returns void language plpgsql security definer set search_path = public as $$
declare u record;
begin
  if auth.uid() is null then return; end if;
  select id, email, raw_user_meta_data into u from auth.users where id = auth.uid();
  insert into public.profiles (id, email, full_name)
    values (u.id, u.email, coalesce(u.raw_user_meta_data->>'full_name', u.raw_user_meta_data->>'name'))
    on conflict (id) do nothing;
  if not exists (select 1 from public.user_roles where user_id = u.id) then
    insert into public.user_roles (user_id, role) values (u.id, 'candidate');
  end if;
end $$;
grant execute on function public.ensure_profile() to authenticated;

create table public.interviews (
  id uuid primary key default gen_random_uuid(),
  candidate_id uuid not null,
  candidate_name text,
  role_id text not null,
  role_title text not null,
  status text not null default 'in_progress',
  answers jsonb not null default '[]',
  integrity_events jsonb not null default '[]',
  warnings int not null default 0,
  report jsonb,
  overall_score int,
  created_at timestamptz not null default now(),
  completed_at timestamptz
);
grant select, insert, update on public.interviews to authenticated;
grant all on public.interviews to service_role;
alter table public.interviews enable row level security;
create policy "Candidate reads own, admin reads all" on public.interviews for select to authenticated
  using (candidate_id = auth.uid() or public.has_role(auth.uid(), 'admin'));
create policy "Candidate creates own" on public.interviews for insert to authenticated
  with check (candidate_id = auth.uid());
create policy "Candidate updates own open interview" on public.interviews for update to authenticated
  using (candidate_id = auth.uid() and status = 'in_progress')
  with check (candidate_id = auth.uid());