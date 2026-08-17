"""
Refreshes the events table: drops expired (past-dated) rows, then seeds
the next few recurring finance dates (rent + Connor's paychecks).

    py refresh_events.py
"""
import json
import os
import urllib.request
import urllib.error
from datetime import date, timedelta

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


def next_occurrences(day_of_month, count, start):
    """Next `count` dates landing on `day_of_month`, strictly after `start`."""
    out = []
    y, m = start.year, start.month
    while len(out) < count:
        try:
            d = date(y, m, day_of_month)
        except ValueError:
            d = None
        if d and d > start:
            out.append(d)
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


today = date.today()

RENT_DATES = next_occurrences(15, 3, today)         # next 3 rent due-dates
PAY11_DATES = next_occurrences(11, 3, today)          # next 3 Connor-11th paychecks
PAY27_DATES = next_occurrences(27, 3, today)          # next 3 Connor-27th paychecks

rows = []
for d in RENT_DATES:
    rows.append({"title": "Brooklyn rent → Nikolaj", "date": d.isoformat(), "kind": "ledger", "amount": -2200, "notes": None})
for d in PAY11_DATES + PAY27_DATES:
    rows.append({"title": "Connor check", "date": d.isoformat(), "kind": "ledger", "amount": 1800, "notes": None})

rows.sort(key=lambda r: r["date"])

if __name__ == '__main__':
    today_iso = today.isoformat()
    print(f"Dropping events with date < {today_iso} ...")
    sb_request('DELETE', f'events?date=lt.{today_iso}')
    print("  done.")

    print(f"Inserting {len(rows)} refreshed finance rows ...")
    sb_request(
        'POST', 'events?on_conflict=title,date', rows,
        {'Prefer': 'resolution=merge-duplicates,return=representation'},
    )
    for r in rows:
        print(f"  {r['date']}  {r['title'].encode('ascii', 'replace').decode():<28} {r['amount']:+d}")
    print("Done.")
