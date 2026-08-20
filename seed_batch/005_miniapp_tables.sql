-- Task 5: tables for the Henry OS Mini App (Telegram web app).
-- Run this once in the Supabase SQL Editor (project lifeos), then tell Claude it's done.
-- Safe to re-run (IF NOT EXISTS everywhere).
--
-- Both tables are backend-only (service key) — no public select policy, unlike
-- workout_week/events. The mini app never talks to Supabase directly; it always
-- goes through lifeos-backend's /app/api/* routes.

-- Per-calendar-date workout completion. Keyed by date (not weekday) so marking
-- "Mon Aug 17" done doesn't retroactively mark every Monday done.
create table if not exists workout_done (
  date date primary key,
  day text not null,                 -- 'MON'..'SUN', denormalized for convenience
  created_at timestamptz not null default now()
);
alter table workout_done enable row level security;

-- The daily timetable (currently a hardcoded JS array in index.html's TT var).
-- This table becomes the editable source of truth for the mini app; the site's
-- hardcoded TT is untouched for now.
create table if not exists timetable (
  id uuid primary key default gen_random_uuid(),
  start_time text not null,          -- 'HH:MM' 24-hour
  end_time text,                     -- 'HH:MM' 24-hour, optional
  title text not null,
  notes text,
  dept text,                         -- short label, e.g. 'Performance', 'Letters' (matches site's TT.dept)
  sort_order int not null default 0,
  created_at timestamptz not null default now()
);
alter table timetable enable row level security;
