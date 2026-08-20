"""
Task 5: seed `timetable` with the site's current hardcoded TT array (index.html)
so the mini app has real data on first load instead of an empty schedule.
Safe to re-run — clears and re-inserts every time (this table is the mini app's
editable source of truth going forward; don't re-run after you've made edits
in the app, or you'll wipe them).

    py seed_miniapp_timetable.py
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
        print(f"  ERROR {method} {path}: {e.code} {e.read().decode()[:400]}")
        raise


# Straight port of the TT array from lifeos/index.html (~line 787).
TT = [
    {'s': '05:50', 'e': '06:00', 't': 'Meditate', 'd': 'Breathe, set the intention', 'dept': 'Mind'},
    {'s': '06:00', 'e': '06:45', 't': 'Workout', 'd': 'Stay consistent — the foundation', 'dept': 'Performance'},
    {'s': '06:45', 'e': '07:00', 't': 'Shower', 'd': '', 'dept': 'Body'},
    {'s': '07:00', 'e': '07:30', 't': 'Cook breakfast', 'd': 'Eat clean', 'dept': 'Food'},
    {'s': '07:30', 'e': '07:50', 't': 'Eat + read', 'd': 'No screens — food and a book', 'dept': 'Letters'},
    {'s': '08:00', 'e': '08:15', 't': '☀️ Morning sunlight', 'd': '10 min outside within an hour of waking', 'dept': 'Body'},
    {'s': '08:00', 'e': '12:00', 't': 'Work — HB360', 'd': 'Calls, clients, admin', 'dept': 'Work'},
    {'s': '12:00', 'e': '13:00', 't': 'Coffee + Write — Zen Gun', 'd': 'Open the creative studio', 'dept': 'Creative'},
    {'s': '13:00', 'e': '15:30', 't': 'Work — HB360', 'd': 'Afternoon grind', 'dept': 'Work'},
    {'s': '16:00', 'e': '17:00', 't': 'Read', 'd': 'Fiction, poetry, whatever pulls', 'dept': 'Letters'},
    {'s': '17:00', 'e': '18:00', 't': 'Cook + eat dinner', 'd': 'Eat clean', 'dept': 'Food'},
    {'s': '18:15', 'e': '19:30', 't': 'Zen Gun — write / music / edit', 'd': 'Evening creative block', 'dept': 'Creative'},
    {'s': '22:00', 'e': '22:05', 't': 'Castor oil — lashes + brows', 'd': '60 seconds', 'dept': 'Body'},
    {'s': '22:00', 'e': '22:30', 't': 'Hair — derma roll + minoxidil', 'd': 'Derma → wait 20–30 min → minox', 'dept': 'Body'},
]


if __name__ == '__main__':
    existing = sb_request('GET', 'timetable?select=id')
    if existing:
        for row in existing:
            sb_request('DELETE', f"timetable?id=eq.{row['id']}")
        print(f"  cleared {len(existing)} existing rows")

    rows = [
        {
            'start_time': item['s'],
            'end_time': item['e'],
            'title': item['t'],
            'notes': item['d'] or None,
            'dept': item['dept'],
            'sort_order': i,
        }
        for i, item in enumerate(TT)
    ]
    sb_request('POST', 'timetable', rows)
    print(f"  inserted {len(rows)} timetable rows")
    print("Done.")
