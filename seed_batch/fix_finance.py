"""
Finance corrections per Gable's Aug 2026 update:
- Rent is $2,100/mo, not $2,200, and not currently recurring on the 15th.
- Removes the 3 recurring "Brooklyn rent" events, replaces with two dated
  one-offs: Oct 1 ($4,200 cash, covers Aug+Sep) and Oct 14 ($2,100, October).
- Rewrites the kb 'finance' row with the current Connor-debt situation and
  near-term cash facts (Plan B, Parity dial paydown, Leo/Kealy/La Crosse cash).

    py fix_finance.py
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


FINANCE_CONTENT = (
    "Advisor: Mort Silber, Senior Financial Advisor. Brief: You are Mort Silber, Senior Financial "
    "Advisor for Gable's Life OS. Semi-retired, sharp, warm but direct - like a sharp Jewish uncle "
    "who's seen everything and genuinely wants you to win. Be specific, use actual numbers, call out "
    "when he's being financially sloppy. 3-5 sentences max.\n\n"
    "CONNOR DEBT (Plan B, confirmed): Gable owes brother Connor $4,475 as of Aug 31, 2026. Connor's "
    "business pays Gable $6,000/mo; Gable draws $5,000/mo and the remaining $1,000/mo pays the debt "
    "down via the 'Parity dial.' At that pace it clears around Jan 2027. The $2,500 check deposited "
    "Aug 27 is regular pay for 9/1-9/14, NOT a debt payment - don't confuse the two.\n\n"
    "RENT: $2,100/mo to Nikolaj, NOT currently recurring on the 15th. Oct 1: $4,200 cash to Nikolaj "
    "in person, covering Aug+Sep. Oct 14: $2,100 for October. After that, no rent for a few months - "
    "Gable is leaving.\n\n"
    "NEAR-TERM CASH (Aug 2026): Leo pays Gable $600 on Fri Aug 21 (maybe +$300 the following Friday). "
    "Kealy gets $150 once Leo pays, then $200 at end of month. La Crosse deposit of $400-600 expected "
    "back end of August.\n\n"
    "Money goals in order: 1) $1,000 emergency buffer ASAP, 2) Discover it Secured card to rebuild "
    "credit - apply when buffer hits $500, use for gas/groceries and pay in full monthly, 3) $10-15k "
    "buffer by year end BEFORE investing, 4) Then $500/mo Roth IRA at Fidelity in FXAIX + $500/mo S&P."
)


if __name__ == '__main__':
    print("Removing recurring rent events...")
    old = sb_request('GET', "events?title=eq.Brooklyn%20rent%20%E2%86%92%20Nikolaj&select=id,date,amount")
    for r in old:
        print(f"  deleting {r['date']} {r['amount']}")
    sb_request('DELETE', "events?title=eq.Brooklyn%20rent%20%E2%86%92%20Nikolaj")

    print("Inserting corrected rent events...")
    new_rows = [
        {"title": "Cash to Nikolaj (Aug+Sep rent)", "date": "2026-10-01", "kind": "ledger", "amount": -4200, "notes": "In person"},
        {"title": "October rent → Nikolaj", "date": "2026-10-14", "kind": "ledger", "amount": -2100, "notes": None},
    ]
    sb_request('POST', 'events?on_conflict=title,date', new_rows,
               {'Prefer': 'resolution=merge-duplicates,return=representation'})
    for r in new_rows:
        print(f"  {r['date']}  {r['title'].encode('ascii','replace').decode()}  {r['amount']}")

    print("Rewriting kb.finance...")
    sb_request('PATCH', 'kb?dept=eq.finance', {'content': FINANCE_CONTENT})
    print(f"  new length: {len(FINANCE_CONTENT)} chars")

    print("Done.")
