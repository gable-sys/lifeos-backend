-- Task 3: reminders need a date column so one-time reminders ("remind me
-- in 5 min") don't repeat every day forever like the recurring ones do.
-- Safe to re-run.

alter table reminders add column if not exists date date;
