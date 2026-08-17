-- Task 1: new tables for the site's hardcoded data.
-- Run this once in the Supabase SQL Editor (project lifeos), then tell Claude it's done.
-- Safe to re-run (IF NOT EXISTS everywhere).

create table if not exists workout_week (
  day text primary key,              -- 'MON','TUE',... matches the site's day codes
  day_order int not null,            -- 0=SUN..6=SAT, for sorting
  title text not null,
  focus text,
  rest boolean not null default false,
  blocks jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);
alter table workout_week enable row level security;
drop policy if exists workout_week_public_read on workout_week;
create policy workout_week_public_read on workout_week for select using (true);

create table if not exists events (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  date date not null,
  kind text not null,                -- 'finance'|'music'|'social'|'ledger' etc.
  amount numeric,                    -- only set when kind='ledger'
  notes text,
  created_at timestamptz not null default now(),
  unique (title, date)
);
alter table events enable row level security;
drop policy if exists events_public_read on events;
create policy events_public_read on events for select using (true);
