"""
Replaces the workout_week rows with the current week's program from
seed_batch/WORKOUT_SPEC.md (the "THIS WEEK (counting today)" section).
Day 1 = today, mapped onto the actual weekday it falls on this week.

    py update_workout_week.py
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

# Day 1 of the spec = today = Monday (2026-08-17), so Day N maps to MON+N-1.
WEEK = [
    {
        "d": "MON", "ttl": "Big Park Upper Session", "rest": False,
        "focus": "Today's session — completed. Coming off sickness, kept it submaximal.",
        "blocks": [
            {"name": "Session", "ex": [
                {"nm": "Park upper-body session", "rx": "Completed", "tip": "Felt like a slog coming off sickness — done."},
            ]},
        ],
    },
    {
        "d": "TUE", "ttl": "Sprints · Delts · Abs", "rest": False,
        "focus": "Chest rests today (hit yesterday, recovers while sprinting). Sprints = the leg work. Keep it submaximal — still shaking off sickness.",
        "blocks": [
            {"name": "Warm-Up", "ex": [
                {"nm": "Jog + leg swings + strides", "rx": "6–8 min", "tip": "Warm up fully."},
            ]},
            {"name": "Sprints", "ex": [
                {"nm": "Sprints", "rx": "6 reps · ~30–50m", "tip": "Walk back between reps."},
            ]},
            {"name": "Delts", "ex": [
                {"nm": "Lateral raises", "rx": "4×15–20", "tip": ""},
                {"nm": "Lean-away laterals", "rx": "3×12–15/side", "tip": ""},
                {"nm": "DB overhead press", "rx": "3×15–20", "tip": ""},
                {"nm": "Rear delts (light)", "rx": "2×15", "tip": "Go light — watch the rotator cuff."},
            ]},
            {"name": "Abs", "ex": [
                {"nm": "Lying leg raises", "rx": "3×15", "tip": ""},
                {"nm": "Hollow hold", "rx": "3×30s", "tip": ""},
                {"nm": "Bicycle crunches", "rx": "3×20", "tip": ""},
                {"nm": "Plank", "rx": "2×45s", "tip": ""},
            ]},
        ],
    },
    {
        "d": "WED", "ttl": "Park · Pull + Dips + Push + Delts + Abs", "rest": False,
        "focus": "Beat last session's numbers. Dead hang first.",
        "blocks": [
            {"name": "Warm-Up", "ex": [
                {"nm": "Warm-up + dead hang", "rx": "—", "tip": "Decompression, grip, shoulder health."},
            ]},
            {"name": "Pull + Dips (superset)", "ex": [
                {"nm": "Pull-ups (wide)", "rx": "5×6–12", "tip": "Fresh — beat last session."},
                {"nm": "Dips (lean forward)", "rx": "4×6–12", "tip": "Moderate depth — rotator cuff."},
            ]},
            {"name": "Chins + Push (superset)", "ex": [
                {"nm": "Chin-ups", "rx": "3×8–12", "tip": ""},
                {"nm": "Wide push-ups", "rx": "3×max", "tip": ""},
            ]},
            {"name": "Rows & Push", "ex": [
                {"nm": "Inverted rows", "rx": "4×12–15", "tip": ""},
                {"nm": "Pike push-ups", "rx": "3×10–15", "tip": ""},
            ]},
            {"name": "Delts", "ex": [
                {"nm": "Lateral raises", "rx": "4×15–20", "tip": ""},
            ]},
            {"name": "Abs", "ex": [
                {"nm": "Captain's chair leg raises", "rx": "4×12–15", "tip": ""},
            ]},
        ],
    },
    {
        "d": "THU", "ttl": "Home · Chest + Delts + Legs + Abs", "rest": False,
        "focus": "Home = bar + DBs only. No dips/rows/pike.",
        "blocks": [
            {"name": "Chest", "ex": [
                {"nm": "DB floor press", "rx": "4×15–20", "tip": "Pause at the bottom."},
                {"nm": "Wide push-ups", "rx": "3×max", "tip": ""},
                {"nm": "DB flyes", "rx": "3×12–15", "tip": ""},
            ]},
            {"name": "Delts", "ex": [
                {"nm": "Lateral raises", "rx": "4×15–20", "tip": ""},
                {"nm": "Lean-away laterals", "rx": "3×12–15/side", "tip": ""},
                {"nm": "DB overhead press", "rx": "3×15–20", "tip": ""},
                {"nm": "Rear delts (light)", "rx": "—", "tip": ""},
            ]},
            {"name": "Legs", "ex": [
                {"nm": "Bulgarian split squats", "rx": "3×12–15/leg", "tip": "Ease in — DOMS history."},
                {"nm": "DB RDL", "rx": "3×15", "tip": ""},
                {"nm": "Single-leg calf raises", "rx": "3×15/leg", "tip": ""},
            ]},
            {"name": "Abs", "ex": [
                {"nm": "Lying leg raises", "rx": "—", "tip": ""},
                {"nm": "Hollow hold", "rx": "—", "tip": ""},
                {"nm": "Bicycle crunches", "rx": "—", "tip": ""},
                {"nm": "Plank", "rx": "—", "tip": ""},
            ]},
        ],
    },
    {
        "d": "FRI", "ttl": "Park · Pull + Dips + Rows + Pike + Delts + Abs", "rest": False,
        "focus": "Same shape as Wednesday — switch pull-up grip (neutral/close), keep dips moderate for the shoulder.",
        "blocks": [
            {"name": "Pull + Dips (superset)", "ex": [
                {"nm": "Pull-ups (neutral/close grip)", "rx": "5×6–12", "tip": "Switch grip from Wednesday."},
                {"nm": "Dips (lean forward)", "rx": "4×6–12", "tip": "Keep moderate — protect the shoulder."},
            ]},
            {"name": "Chins + Push (superset)", "ex": [
                {"nm": "Chin-ups", "rx": "3×8–12", "tip": ""},
                {"nm": "Wide push-ups", "rx": "3×max", "tip": ""},
            ]},
            {"name": "Rows & Push", "ex": [
                {"nm": "Inverted rows", "rx": "4×12–15", "tip": ""},
                {"nm": "Pike push-ups", "rx": "3×10–15", "tip": ""},
            ]},
            {"name": "Delts", "ex": [
                {"nm": "Lateral raises", "rx": "4×15–20", "tip": ""},
            ]},
            {"name": "Abs", "ex": [
                {"nm": "Captain's chair leg raises", "rx": "4×12–15", "tip": ""},
            ]},
        ],
    },
    {
        "d": "SAT", "ttl": "Legs + Sprints #2 + Calves + Abs", "rest": False,
        "focus": "Fresh legs — second sprint session of the week.",
        "blocks": [
            {"name": "Sprints", "ex": [
                {"nm": "Sprints", "rx": "6–8 reps", "tip": "Fresh legs."},
            ]},
            {"name": "Legs", "ex": [
                {"nm": "Goblet squats", "rx": "3×15", "tip": ""},
                {"nm": "Walking lunges", "rx": "3×12/leg", "tip": ""},
                {"nm": "Single-leg calf raises", "rx": "3×15/leg", "tip": ""},
            ]},
            {"name": "Delts", "ex": [
                {"nm": "Lateral raises", "rx": "4×15–20", "tip": "Keep width daily-ish."},
            ]},
            {"name": "Abs", "ex": [
                {"nm": "Abs", "rx": "—", "tip": "Standard ab block."},
            ]},
        ],
    },
    {
        "d": "SUN", "ttl": "Rest", "rest": True,
        "focus": "Full recovery. Eat big, sleep. If run-down from the sickness earlier in the week, take an extra rest day.",
        "blocks": [
            {"name": "Recovery", "ex": [
                {"nm": "Full rest", "rx": "—", "tip": "Optional: light laterals + dead hang only."},
            ]},
        ],
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
    print(f"Replaced {len(rows)} workout_week rows with this week's program.")
