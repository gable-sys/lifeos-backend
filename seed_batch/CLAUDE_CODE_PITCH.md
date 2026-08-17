# Life OS — Claude Code Brief: One Brain (Supabase Migration + Telegram Cleanup)

**Repos (both cloned locally):**
- `lifeos` — frontend. Single file: `index.html` (~260KB), deployed via Netlify (`stupendous-concha-2d70be.netlify.app`). Also contains `LIFEOS_MASTER_BIBLE.md` — read it first.
- `lifeos-backend` — Flask on Render (`lifeos-backend-nf15.onrender.com`). Single file: `app.py`. Auto-deploys on push (~45s, free tier sleeps ~50s cold start).

**Stack:** Flask + Supabase (project `lifeos`, REST via `sb_insert/sb_select/sb_update/sb_delete` helpers already in app.py) + Telegram bot ("Henry", persona = Henry Miller, claude-sonnet-4-6) + Plaid + Netlify frontend.

**Existing Supabase tables:** tasks, projects, notes, pending, chat_log, kb, state, reminders, workout_week.

**Env vars (Render):** PLAID_*, ANTHROPIC_API_KEY, GMAIL_*, SUPABASE url/key, TELEGRAM token, CRON_KEY (verify this one is actually set — /tick requires it).

---

## THE PROBLEM

The site (`index.html`) contains hardcoded JS `var` blocks holding real life data: `WORKOUT_WEEK`, `EVENTS`, `UPCOMING`, `todos`, finance context (income, rent to Nikolaj $2,200, Connor pay dates ~11th & 27th, Leo+Gus ~$1,200 split, money goals), reading/timetable data (`TT`), advisor personas (`ADV`), scholars (`SCHOLARS`).

Henry on Telegram reads only Supabase (`life_context()` in app.py = open tasks + active projects; `load_kb()` = kb table). **He cannot see any of the site's data. The site cannot be edited without redeploying.** Two brains, no shared memory.

## THE GOAL

One brain: Supabase is the single source of truth. Site reads from it; Henry reads from it; editing data never requires a redeploy.

---

## TASK 1 — Migrate site data into Supabase

1. Extract these `var` blocks from `index.html` into Supabase:
   - `WORKOUT_WEEK` → existing `workout_week` table
   - `EVENTS` / `UPCOMING` → new `events` table (id, title, date, kind, notes)
   - `todos` → merge into existing `tasks` table (dedupe by title)
   - Finance context block (income, rent, splits, goals) → `kb` table as row `key='FINANCE_CONTEXT'` (markdown text)
   - `TT` (daily timetable) → `kb` row `key='DAILY_TIMETABLE'`
   - `ADV` advisor personas + `SCHOLARS` → `kb` rows (`ADVISORS`, `SCHOLARS`) — site still renders them, Henry can reference them
2. **Leave hardcoded** (decorative, Henry doesn't need): quotes, tarot, moon phases, celestial lore, fortunes, memento mori, NYC events, glyphs, icons.
3. Site loads this data from Supabase on page load (fetch → render; fall back to a cached/default copy if fetch fails so the site never renders empty).
4. **Do not touch the visual identity.** Cream paper, terracotta/green, Fraunces/Spectral/IBM Plex Mono, hard-edged cards, box shadows — pixel-identical output, different data source.
5. Seed script or SQL for initial data load — idempotent, safe to re-run.

## TASK 2 — Expand Henry's context

Extend `life_context()` (or add a leaner variant) so Henry can see, per message: open tasks by category, active projects, this week's workout (from workout_week), next 7 days of events, and FINANCE_CONTEXT summary. Keep token budget sane — summarize, don't dump.

## TASK 3 — Telegram cleanup (Henry's voice + function)

1. **Reminders that fire:** "remind me to X at 4pm" → parse → `reminders` table → `/tick` cron delivers at time. Confirm `/tick` works with CRON_KEY; scheduled briefs are 8:30 AM, 12:30, 21:00 ET.
2. **Categorized todo log:** captured tasks get a `category` matching the site's exact department titles: Calendar, Finance, Workout, Music, Reading, Creative, Body, Lab, Library, Fridge, Closet, Wander. `/todo` lists open tasks grouped by category with one-tap done buttons.
3. **Strip ceremony:** confirmations are one short line in Henry's voice. No decorative buttons; inline keyboards only when action is genuinely needed (done/approve/disambiguate). Keep the existing JSON filing pattern but tighten replies.
4. Keep webhook locked to Gable's chat id. All keys stay in Render env vars.

## TASK 4 — Seed the kb table

Load these files (in this folder) into `kb`: ZEN_GUN_SPEC.md, DATING_SPEC.md, WORKOUT_SPEC.md. Also register reading-curriculum, piano-master-plan, guitar-master-plan, guitar-schedule (store as kb text extracted from the HTMLs, or link rows pointing at site pages — extract text, HTML is bloat in a prompt).

---

## WORKING RULES

- One task at a time, in order. Ship and verify each before the next.
- `python3 -m py_compile app.py` after every backend edit.
- For index.html (>260KB): edit on disk with Python splice scripts, validate JS with `node --check` on extracted script blocks before committing.
- Anchor-string replacement with `assert anchor in src` before every swap.
- Confirm with Gable before destructive changes (table drops, data overwrites).
- Gable is early in learning to code: plain language, one step at a time, honest when blocked.

## VERIFY DONE

- Send Henry "remind me to test in 5 min" → reminder fires.
- Send Henry "add buy bike parts" → files as task with category, one-line confirm.
- Ask Henry "what's my rent situation" → answers from FINANCE_CONTEXT.
- Ask Henry "what's today's workout" → answers from workout_week.
- Edit a workout_week row in Supabase → site reflects it on refresh, no redeploy.
- Site looks pixel-identical to before.
