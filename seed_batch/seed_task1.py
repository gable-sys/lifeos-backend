"""
Task 1 seed script: moves hardcoded index.html data into Supabase.

Run once after 001_create_tables.sql has been applied:
    py seed_task1.py          (Windows)
    python3 seed_task1.py     (Render / Mac / Linux)

Reads SUPABASE_URL / SUPABASE_SERVICE_KEY from a .env file in this script's
parent directory (same format app.py expects). Safe to re-run: workout_week
and events use upsert, tasks/kb only insert rows that don't already exist.
"""
import json
import os
import urllib.request
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(os.path.dirname(HERE), '.env')


def load_env(path):
    env = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()
    return env


env = load_env(ENV_PATH)
SUPABASE_URL = env['SUPABASE_URL']
SUPABASE_KEY = env['SUPABASE_SERVICE_KEY']


def sb_request(method, path, body=None, extra_headers=None):
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
    }
    if extra_headers:
        headers.update(extra_headers)
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        print(f"  ERROR {method} {path}: {e.code} {e.read().decode()[:300]}")
        raise


def sb_select(table, query):
    return sb_request('GET', f'{table}?{query}')


def sb_upsert(table, rows, on_conflict):
    return sb_request(
        'POST', f'{table}?on_conflict={on_conflict}', rows,
        {'Prefer': 'resolution=merge-duplicates,return=representation'},
    )


def sb_insert(table, rows):
    return sb_request('POST', table, rows, {'Prefer': 'return=representation'})


# ---------------------------------------------------------------------------
# 1. WORKOUT_WEEK -> workout_week table
# ---------------------------------------------------------------------------

WORKOUT_WEEK = [
    {"d": "SUN", "ttl": "Steady Run · Abs · Posture", "focus": "Easy aerobic + core. Week 2 starts Monday.", "rest": False, "blocks": [
        {"name": "Run", "ex": [
            {"nm": "Steady-state run", "rx": "25–35 min", "tip": "Conversational pace. Nasal breathing."},
        ]},
        {"name": "Core + Posture", "ex": [
            {"nm": "Hanging leg raises", "rx": "3 × 12", "tip": "Control it."},
            {"nm": "Russian twists", "rx": "3 × 20", "tip": "Hold the 15."},
            {"nm": "Plank", "rx": "3 × 45s", "tip": "Full brace."},
            {"nm": "Posture block", "rx": "10 min", "tip": "Chin tucks, wall angels, APT correction, doorway stretch."},
        ]},
    ]},
    {"d": "MON", "ttl": "Shoulders · Chest · Triceps", "focus": "Push day — V-taper width. Depressed shoulders, slow laterals. GtG warm-up first.", "rest": False, "blocks": [
        {"name": "GtG Warm-Up", "ex": [
            {"nm": "Lateral raises (light)", "rx": "2 × 15", "tip": "Warm the medial delt. Shoulders DOWN."},
            {"nm": "Face pulls", "rx": "2 × 20", "tip": "Opens rear delt, preps rotator cuff."},
        ]},
        {"name": "Delts — the width", "ex": [
            {"nm": "Elevated pike push-ups", "rx": "4 × 10–12", "tip": "Feet high. Full ROM. Width overload."},
            {"nm": "DB lateral raises", "rx": "4 × 15–20", "tip": "Lead with elbow. No swing. Slow negative."},
            {"nm": "DB overhead press", "rx": "3 × 12", "tip": "Pack shoulders DOWN — delts fire, traps quiet."},
            {"nm": "DB rear delt flye", "rx": "3 × 15", "tip": "3D shoulders + posture. Hinge 45°."},
        ]},
        {"name": "Chest", "ex": [
            {"nm": "Push-ups", "rx": "3 × 15", "tip": "Full lockout, controlled descent."},
            {"nm": "DB floor press", "rx": "3 × 12", "tip": "Pause at the bottom."},
        ]},
        {"name": "Triceps + Arms", "ex": [
            {"nm": "Close-grip push-ups", "rx": "3 × max", "tip": "Triceps = 2/3 of arm size."},
            {"nm": "DB overhead extension", "rx": "2 × 12", "tip": "Full stretch behind head."},
        ]},
        {"name": "Neck", "ex": [
            {"nm": "Isometric holds", "rx": "2 rounds × 4 directions", "tip": "10–15s each. Fwd, back, both sides."},
        ]},
    ]},
    {"d": "TUE", "ttl": "Sprints · Legs · Calves", "focus": "Cardio first on fresh legs. Best day to sprint.", "rest": False, "blocks": [
        {"name": "Sprints", "ex": [
            {"nm": "Warm-up jog + leg swings", "rx": "8 min", "tip": "Non-negotiable. Cold hamstrings tear."},
            {"nm": "All-out sprints", "rx": "6–8 × 20–40m", "tip": "Full recovery between. Walk back. 85–95% effort."},
        ]},
        {"name": "Legs", "ex": [
            {"nm": "Bulgarian split squats", "rx": "3 × 12/leg", "tip": "Rear foot elevated. Hold 15s DB."},
            {"nm": "Goblet squats", "rx": "3 × 15", "tip": "DB at chest. Sit deep, drive knees out."},
            {"nm": "Walking lunges", "rx": "3 × 12/leg", "tip": "Finisher. Hold the 15s."},
        ]},
        {"name": "Calves", "ex": [
            {"nm": "Standing calf raises", "rx": "4 × 20–25", "tip": "Full stretch at bottom. Pause at top."},
            {"nm": "Single-leg calf raises", "rx": "2 × 15/leg", "tip": "Chase the burn."},
        ]},
    ]},
    {"d": "WED", "ttl": "Back · Biceps · Abs", "focus": "V-taper width from the back. Pull-ups are king.", "rest": False, "blocks": [
        {"name": "Pull — V-taper", "ex": [
            {"nm": "Wide-grip pull-ups", "rx": "4 × max", "tip": "Wide lats = the flare of the V."},
            {"nm": "Chin-ups", "rx": "3 × max", "tip": "Supinated grip — extra biceps."},
            {"nm": "DB rows", "rx": "3 × 12/arm", "tip": "Row to hip, squeeze the blade."},
            {"nm": "Face pulls", "rx": "3 × 15", "tip": "Posture. Upper back. Do these."},
        ]},
        {"name": "Biceps", "ex": [
            {"nm": "DB curls", "rx": "3 × 12–15", "tip": "Full ROM, no swing, squeeze at top."},
            {"nm": "Hammer curls", "rx": "2 × 12", "tip": "Brachialis + forearm thickness."},
        ]},
        {"name": "Abs", "ex": [
            {"nm": "Hanging leg raises", "rx": "3 × 12", "tip": "No swinging."},
            {"nm": "Hollow hold", "rx": "3 × 30s", "tip": "Low back pressed down."},
        ]},
        {"name": "Neck", "ex": [
            {"nm": "Isometric holds", "rx": "2 rounds", "tip": "All 4 directions, 10–15s each."},
        ]},
    ]},
    {"d": "THU", "ttl": "Shoulders (Peak) · Chest · Abs", "focus": "Highest volume shoulder day. Burn the medial delt.", "rest": False, "blocks": [
        {"name": "Delts — full send", "ex": [
            {"nm": "Elevated pike push-ups", "rx": "4 × 10–12", "tip": "Feet as high as possible."},
            {"nm": "DB overhead press", "rx": "4 × 12–15", "tip": "Pack down, 3s slow negatives."},
            {"nm": "DB lateral raises", "rx": "4 × 20 + partials", "tip": "Full set then 10 partials. Burns."},
            {"nm": "DB rear delt flye", "rx": "3 × 15", "tip": "Don't skip."},
            {"nm": "Upright rows (wide grip)", "rx": "3 × 12", "tip": "Wide grip hits medial delt. Elbows no higher than shoulders."},
        ]},
        {"name": "Chest", "ex": [
            {"nm": "Decline push-ups", "rx": "3 × max", "tip": "Feet elevated = upper chest."},
            {"nm": "DB floor press", "rx": "3 × 12", "tip": "Pause at bottom."},
        ]},
        {"name": "Abs", "ex": [
            {"nm": "Lying leg raises", "rx": "3 × 15", "tip": "Slow descent."},
            {"nm": "Plank", "rx": "3 × 45s", "tip": "No sag."},
        ]},
    ]},
    {"d": "FRI", "ttl": "Travel · Optional Light Session", "focus": "Back to Brooklyn. Light or rest — listen to your body.", "rest": False, "blocks": [
        {"name": "Optional", "ex": [
            {"nm": "Pull-ups", "rx": "3 × max", "tip": "Maintain the stimulus."},
            {"nm": "DB lateral raises", "rx": "3 × 20", "tip": "Never skip laterals."},
            {"nm": "Neck isometrics", "rx": "2 rounds", "tip": "Easy, on the road."},
        ]},
        {"name": "Posture", "ex": [
            {"nm": "Chin tucks", "rx": "2 × 15", "tip": "Corrects forward head posture."},
            {"nm": "Doorway pec stretch", "rx": "2 × 30s/side", "tip": "Chest opens, posture resets."},
            {"nm": "Wall angels", "rx": "2 × 10", "tip": "Shoulder blade control."},
        ]},
    ]},
    {"d": "SAT", "ttl": "Rest", "focus": "Standing day off. Eat 2600 cal, sleep.", "rest": True, "blocks": [
        {"name": "Recovery", "ex": [
            {"nm": "Full rest", "rx": "—", "tip": "Creatine, protein, sleep."},
        ]},
    ]},
]

DAY_ORDER = {"SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6}


def seed_workout_week():
    print("Seeding workout_week...")
    rows = [{
        "day": d["d"],
        "day_order": DAY_ORDER[d["d"]],
        "title": d["ttl"],
        "focus": d["focus"],
        "rest": d["rest"],
        "blocks": d["blocks"],
    } for d in WORKOUT_WEEK]
    sb_upsert('workout_week', rows, 'day')
    print(f"  {len(rows)} days upserted.")


# ---------------------------------------------------------------------------
# 2. EVENTS + UPCOMING -> events table
# ---------------------------------------------------------------------------

EVENTS = [
    {"date": "2026-06-01", "t": "Connor debt clears", "type": "finance"},
    {"date": "2026-06-14", "t": "Guitar review", "type": "music"},
    {"date": "2026-06-17", "t": "Ellen — Bird book gift", "type": "social"},
    {"date": "2026-06-19", "t": "Shuffleboard · Golrokh", "type": "social"},
]

# UPCOMING used short 'Jun 13' style dates with no year; site data is all June 2026.
UPCOMING = [
    {"date": "2026-06-13", "label": "Connor check", "amount": 1800},
    {"date": "2026-06-15", "label": "Leo rent share", "amount": 1200},
    {"date": "2026-06-15", "label": "Brooklyn rent → Nikolaj", "amount": -2200},
    {"date": "2026-06-27", "label": "Connor check", "amount": 1800},
    {"date": "2026-06-30", "label": "La Crosse lease ends", "amount": 0},
]


def seed_events():
    print("Seeding events...")
    rows = [{"title": e["t"], "date": e["date"], "kind": e["type"], "amount": None, "notes": None} for e in EVENTS]
    rows += [{"title": u["label"], "date": u["date"], "kind": "ledger", "amount": u["amount"], "notes": None} for u in UPCOMING]
    sb_upsert('events', rows, 'title,date')
    print(f"  {len(rows)} events upserted.")


# ---------------------------------------------------------------------------
# 3. todos (cork board cards) -> tasks table, dedupe by title
#    Skipping the sobriety-streak card ("Day N sober") - it's a computed
#    display, not a real to-do.
# ---------------------------------------------------------------------------

TODOS = [
    {"title": "Shoulders today", "notes": "Push day. V-taper width. Laterals slow and controlled. GtG warm-up."},
    {"title": "Get quarters, laundry", "notes": "Laundry day. Need quarters from store."},
    {"title": "Olaplex No.3 + Moroccan Oil", "notes": "Olaplex: damp hair 10min, shampoo out. Moroccan: half pump on towel-dry. Both from Amazon or Sally Beauty."},
    {"title": "Tinted SPF 30+", "notes": "Swap morning sunscreen. Evens redness, reads like nothing. ~$20-30. Get it Thursday."},
    {"title": "Black vest, no lapels", "notes": "Depop: black waistcoat / black vest M. Single-breasted, no lapels. Wool or cotton. $25-40. KEYSTONE piece."},
    {"title": "Brooklyn rent $2,200 Jun 15", "notes": "Wise IBAN transfer to Nikolaj. Must land by 15th."},
    {"title": "Invisalign, book July", "notes": "Brooklyn Family Orthodontics + Dr. Pewarski second opinion. $3500-4500 = go in-office. Book before you leave La Crosse."},
    {"title": "La Crosse lease ends Jun 30", "notes": "Talk with Leo about extension vs move. Decide this week."},
    {"title": "Madison County, open it", "notes": "Madison County Church Suicide Corner. Slow-moving. Time out of mind. Dreamlike. Open the file and write one sentence."},
]


def seed_todos():
    print("Seeding tasks from cork board todos...")
    existing = sb_select('tasks', 'select=title')
    existing_titles = {t['title'] for t in existing}
    new_rows = [{"title": t["title"], "notes": t["notes"], "status": "open"} for t in TODOS if t["title"] not in existing_titles]
    if not new_rows:
        print("  Nothing new (already migrated).")
        return
    sb_insert('tasks', new_rows)
    print(f"  {len(new_rows)} tasks inserted ({len(TODOS) - len(new_rows)} already existed).")


# ---------------------------------------------------------------------------
# 4. SCHOLARS -> kb row (dept='scholars')
# ---------------------------------------------------------------------------

SCHOLARS_SUMMARY = (
    "Visiting Scholars Gable can chat with on the site (8-bit character, floating chat): "
    "Ernest Hemingway (Paris, 1926) - writing craft, courage, the expatriate life. "
    "Marcus Aurelius (Rome, 170 AD) - Stoic philosophy, self-discipline. "
    "Mark Twain (Hartford, 1885) - wit, American life. "
    "Napoleon Bonaparte (Paris, 1804) - ambition, command, strategy. "
    "Simone de Beauvoir (Paris, 1949) - existentialism, freedom. "
    "Henry Miller (Paris, 1934) - creative abandon, Tropic of Cancer. "
    "Jorge Luis Borges (Buenos Aires, 1955) - libraries, labyrinths, infinity. "
    "Edmond Dantes (Monte Cristo, 1838) - revenge, reinvention, patience. "
    "Fyodor Dostoevsky (St. Petersburg, 1866) - suffering, redemption, debt. "
    "Hunter S. Thompson (Woody Creek, 1971) - gonzo, fear and loathing. "
    "Socrates (Athens, 399 BC) - the examined life, questioning everything. "
    "Nikola Tesla (New York, 1899) - invention, obsession, the future."
)


def seed_scholars_kb():
    print("Seeding kb row 'scholars'...")
    existing = sb_select('kb', "dept=eq.scholars&select=dept")
    if existing:
        sb_request('PATCH', 'kb?dept=eq.scholars', {"content": SCHOLARS_SUMMARY})
        print("  Updated existing row.")
    else:
        sb_insert('kb', [{"dept": "scholars", "content": SCHOLARS_SUMMARY}])
        print("  Inserted new row.")


if __name__ == '__main__':
    seed_workout_week()
    seed_events()
    seed_todos()
    seed_scholars_kb()
    print("Done.")
