-- Task 2: tasks need a category column so life_context() can group them.
-- (Task 3 will actually populate this from Telegram; for now it'll mostly be null.)
-- Safe to re-run.

alter table tasks add column if not exists category text;
