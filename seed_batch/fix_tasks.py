"""
Todo cleanup: backfill categories on the migrated June tasks, prune the
ones that are stale one-off items from that batch (mark done or delete).

    py fix_tasks.py
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


def sb_request(method, path, body=None):
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
    }
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        print(f"  ERROR {method} {path}: {e.code} {e.read().decode()[:300]}")
        raise


# id -> (action, category)  action in {'delete', 'done', 'open'}
PLAN = {
    "8dc5901a-7377-4ba3-8a7d-9e24217d77aa": ("delete", None),                # Shoulders today - superseded by workout_week
    "08b142b4-8b9e-432a-8f96-cd9de7807744": ("delete", None),                # Brooklyn rent $2,200 Jun 15 - wrong amount + duplicates events
    "184ca244-6e1c-4b48-85d4-1dd21c8c1c6c": ("delete", None),                # La Crosse lease ends Jun 30 - fully expired admin note
    "a44e587b-4e42-4de4-a246-9a7a5c90099d": ("done", "Closet"),              # Get quarters, laundry
    "93f68e80-af55-4a5a-a9f7-db648d7445c9": ("done", "Body"),                # Olaplex No.3 + Moroccan Oil
    "11c19e1d-e37b-41dc-999b-92403654c78c": ("done", "Body"),                # Tinted SPF 30+
    "61c52716-28e1-41c3-8ac1-29f02e7ff457": ("done", "Closet"),              # Black vest, no lapels
    "5e17805e-e1c5-4ddf-a6be-9d80e8fa8b3e": ("done", "Body"),                # Invisalign, book July
    "4caac259-8521-446e-b8d8-c80ca7243b10": ("open", "Creative"),            # Madison County, open it
    "73eb4270-7c45-4459-b1bf-b790627d03cc": ("open", "Workout"),             # Ex, workout, periodic check-ins
}

if __name__ == '__main__':
    for tid, (action, category) in PLAN.items():
        if action == 'delete':
            sb_request('DELETE', f'tasks?id=eq.{tid}')
            print(f"  deleted {tid}")
        elif action == 'done':
            sb_request('PATCH', f'tasks?id=eq.{tid}', {'status': 'done', 'category': category})
            print(f"  done + categorized ({category}): {tid}")
        else:
            sb_request('PATCH', f'tasks?id=eq.{tid}', {'category': category})
            print(f"  categorized ({category}): {tid}")
    print("Done.")
