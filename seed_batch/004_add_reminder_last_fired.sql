-- Dedup guard: prevents a reminder from firing twice inside one 15-min
-- catch-up window once a real external cron is polling /tick every few minutes.
alter table reminders add column if not exists last_fired date;
