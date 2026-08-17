"""
Workout split changed to 4-day, Thursday-Sunday (per life-os-status-2026-08-17.md).
Only Thursday's session is fully specified (sprints+chest+abs, with real
protocols given); Fri/Sat/Sun are marked as training days with content
not yet specified rather than guessing exercises Gable never gave.

    py update_workout_0817.py
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


def sb_upsert(table, rows, on_conflict):
    url = f"{SUPABASE_URL}/rest/v1/{table}?on_conflict={on_conflict}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=representation',
    }
    req = urllib.request.Request(url, data=json.dumps(rows).encode(), headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"ERROR: {e.code} {e.read().decode()[:400]}")
        raise


DAY_ORDER = {"SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6}

REST_DAY = {
    "focus": "4-day split (Thu-Sun) - early week is rest.",
    "blocks": [{"name": "Recovery", "ex": [{"nm": "Full rest", "rx": "—", "tip": "Consistency over volume."}]}],
}

WEEK = [
    {"d": "MON", "ttl": "Rest", "rest": True, **REST_DAY},
    {"d": "TUE", "ttl": "Rest", "rest": True, **REST_DAY},
    {"d": "WED", "ttl": "Rest", "rest": True, **REST_DAY},
    {
        "d": "THU", "ttl": "Sprints + Chest + Abs", "rest": False,
        "focus": "Eggs ~45min before training. Known template from the new 4-day split.",
        "blocks": [
            {"name": "Sprints", "ex": [
                {"nm": "Warm-up + build-ups", "rx": "10min easy + 2 build-ups @ 70-80%", "tip": "Cold sprinting risks the hamstrings."},
                {"nm": "Hard sprints", "rx": "6-8 × 20-30s", "tip": "90s rest between. Stop when times drop off, not at a rep count."},
            ]},
            {"name": "Chest", "ex": [
                {"nm": "Dips or bench", "rx": "4 sets heavy", "tip": "The V-taper progressive-loading movement."},
                {"nm": "Incline press", "rx": "3 sets", "tip": ""},
                {"nm": "Flyes", "rx": "2 sets high rep", "tip": ""},
            ]},
            {"name": "Abs", "ex": [
                {"nm": "Abs block", "rx": "—", "tip": "Standard ab work to close the session."},
            ]},
        ],
    },
    {
        "d": "FRI", "ttl": "Training day (4-day split)", "rest": False,
        "focus": "Exact exercises for this day haven't been specified yet - tell Henry the plan and it'll update here.",
        "blocks": [],
    },
    {
        "d": "SAT", "ttl": "Training day (4-day split)", "rest": False,
        "focus": "Exact exercises for this day haven't been specified yet - tell Henry the plan and it'll update here.",
        "blocks": [],
    },
    {
        "d": "SUN", "ttl": "Training day (4-day split)", "rest": False,
        "focus": "Exact exercises for this day haven't been specified yet - tell Henry the plan and it'll update here.",
        "blocks": [],
    },
]

if __name__ == '__main__':
    rows = [{
        "day": d["d"],
        "day_order": DAY_ORDER[d["d"]],
        "title": d["ttl"],
        "focus": d["focus"],
        "rest": d["rest"],
        "blocks": d["blocks"],
    } for d in WEEK]
    sb_upsert('workout_week', rows, 'day')
    print(f"Updated {len(rows)} workout_week rows for the 4-day Thu-Sun split.")
