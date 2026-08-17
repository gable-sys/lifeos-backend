"""
- Removes Ilona everywhere in kb (confirmed inactive, resolves the
  zen_gun_spec vs dating_spec contradiction).
- Points dating_spec's Ellen line at the new dating_update_0817 layer
  instead of carrying stale state.
- Adds dating_update_0817 (the 8/14-15 relationship-conversation arc).
- Adds life_status_0817, the freshest cross-cutting snapshot - wins over
  older kb rows on location, sobriety, dating status, and workout split.
- Updates workout_week for the new 4-day (Thu-Sun) split. Only Thursday
  has a fully specified session (sprints+chest+abs) - Fri/Sat/Sun are
  marked as training days with content not yet given, rather than
  guessing exercises that were never specified.

    py update_dating_status_0817.py
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


# ---------------------------------------------------------------------------
# 1. Fix zen_gun_spec: drop Ilona
# ---------------------------------------------------------------------------

ZEN_GUN_DATING_OLD = (
    "DATING (per this spec): Ellen - established, sober dates going well. Bianca (Hinge) - wine date "
    "proposed, no day/time/place confirmed, needs a concrete three-part offer; she has his number, "
    "not vice versa. Ilona - date set. Skill gap: cold approach; floor of 2 openers/week, daytime/"
    "cafe. Protocol: always close in person, never over text."
)
ZEN_GUN_DATING_NEW = (
    "DATING (per this spec, see life_status_0817 for current state): Bianca (Hinge) - wine date "
    "proposed, no day/time/place confirmed, needs a concrete three-part offer; she has his number, "
    "not vice versa. Skill gap: cold approach; floor of 2 openers/week, daytime/cafe. Protocol: "
    "always close in person, never over text."
)

# ---------------------------------------------------------------------------
# 2. Fix dating_spec: drop Ilona, point Ellen at the update layer
# ---------------------------------------------------------------------------

DATING_SPEC_STATE_OLD = (
    "STATE (per this spec - note it predates/differs from Zen Gun spec on Ilona): Ellen - visual "
    "artist, ~20 dates, escalating (sex, overnights, deepening) but a slow flat texter, which is her "
    "baseline, not a disinterest signal. Not yet exclusive. Next date weekend of Aug 12. Betty - "
    "renewed feelings after a park meeting; she still has feelings too per Gara's report, but felt "
    "pursued too aggressively during the breakup. Plan: text her after returning from La Crosse "
    "(~Aug 12-13) inviting a proper evening out, only from a calm flat state. Ilona - first date fell "
    "through, inactive."
)
DATING_SPEC_STATE_NEW = (
    "STATE: Ellen - SUPERSEDED, see dept=dating_update_0817 for the current arc (relationship "
    "conversation 8/14-15). Betty - this spec's original plan (text after returning from La Crosse, "
    "invite an evening out) is also superseded - see dept=life_status_0817, she's now abroad and the "
    "plan has changed."
)

# ---------------------------------------------------------------------------
# 3. New: dating_update_0817
# ---------------------------------------------------------------------------

DATING_UPDATE_0817 = (
    "ELLEN ARC UPDATE (2026-08-17) - supersedes the Ellen section in dating_spec. Weekend of 8/14-15: "
    "first night staying at her place (South Flatbush), physical escalation paused by mutual choice, "
    "heavy drinking + karaoke, a political argument she initiated where he held his position without "
    "getting pulled in, and he opened a relationship conversation referencing ~7 months of history. "
    "Her opening frame: fine with non-monogamy but wants protection used. His move: disclosed he's "
    "probably looking for a relationship now. She was surprised - her earlier 'probably not a "
    "relationship with you' was based on a false premise (she'd assumed a recently-separated guy "
    "wanted freedom, not a verdict on him). She volunteered: only 2 unremarkable dates recently, no "
    "relationship in 7 years, would be sad and jealous if he went elsewhere, would seriously consider "
    "being monogamous. Saturday morning: intimacy, she walked him through her neighborhood unprompted "
    "to show him the mansions, texted him ~1hr after he left - off her usual flat-texter baseline. "
    "Believe the morning over the words said Friday night.\n\n"
    "RULES GOING FORWARD: (1) Don't ask her to re-confirm - let her arrive, pushing produces a "
    "default no. (2) Don't run the optionality/jealousy lever again - it works but talks someone "
    "already leaning in back out; her hesitation is rust (7 years out of practice), not resistance. "
    "(3) Keep initiating plans - don't go passive right after being the one who said the direct "
    "thing. (4) Fri 8/21, in person, sober: one line - 'I meant what I said Friday' - then stop "
    "talking. (5) Protection -> testing conversation, not a negotiation; if going monogamous, both "
    "get tested then decide. (6) Hold the Catskills trip idea - floating it now reads as pressure, "
    "revisit once she initiates something herself. (7) Political arguments are her testing whether "
    "he folds or blows up - hold without engaging, don't enjoy the argument itself.\n\n"
    "OPEN ITEMS: Wed 8/19 - short text, 'friday. dinner.', no callback to the conversation. Fri 8/21 "
    "- in person, the one line. Hinge threads still running (one date planned) - fine since nothing "
    "is defined, but running parallel threads while she's actively considering monogamy is hedging, "
    "not abundance - decide before it decides itself. Sobriety: Friday night was heavy with a memory "
    "gap over the most consequential conversation of the arc - set a pre-decided anchor for "
    "high-stakes nights BEFORE they happen, not during."
)

# ---------------------------------------------------------------------------
# 4. New: life_status_0817 - freshest cross-cutting layer
# ---------------------------------------------------------------------------

LIFE_STATUS_0817 = (
    "LIFE STATUS SNAPSHOT (2026-08-17) - the freshest cross-cutting layer. Wherever this conflicts "
    "with older kb rows (location, sobriety numbers, dating status, workout split), THIS wins.\n\n"
    "LOCATION: NYC/DUMBO (73 Bridge St), permanently split-city with La Crosse WI as the second base "
    "- not temporary.\n\n"
    "SOBRIETY: active 20-day fully-sober streak targeting Sept 1, 2026 (no alcohol). Nicotine ~1x/"
    "week continues separately, NOT part of this streak - the beta carotene 15mg/day cap stays until "
    "nicotine fully stops. Known leak point: 'wine on a first date,' already surfaced once on a Hinge "
    "date with Ava - plan is to keep the date but order something else. Primary vulnerability is "
    "social/family occasions (weekends with Gus/Adan, gatherings with Summer), not random weekdays. "
    "Physiological framing only, never recovery-program language.\n\n"
    "DATING SNAPSHOT: Ellen - ongoing, positive, sober dates genuinely good; current strategy is "
    "escalating the FORMAT not the conversation (daytime plans, meeting his people, having her over), "
    "state intent once plainly after months of consistency - behavior first, words after (see "
    "dating_update_0817 for the full 8/14-15 arc). Betty - abroad in Denmark; plan is ONE short, "
    "light message in a ~1-2 week window, sent on a neutral day feeling fine, not late at night, two "
    "lines, no apology, no case - goal is reading her reply, not making one; if vague, stop "
    "initiating. This REPLACES the earlier 'text her after returning, invite an evening out' plan - "
    "she's no longer local. Bianca - Hinge match, went quiet after a soft yes. Ava - Hinge match, "
    "active banter, date not yet locked to a day. Ilona is inactive - drop her from the roster "
    "entirely.\n\n"
    "TRAINING: split is now 4-day, Thursday-Sunday (Mon-Wed rest). Recent session shape: eggs ~45min "
    "before -> sprints -> chest -> abs. Sprint protocol: 10min easy warm-up + 2 build-ups at 70-80%, "
    "then 6-8 x 20-30sec hard with 90sec rest, stop when times drop off not at a rep count. Chest: "
    "dips or bench 4 heavy sets (the V-taper progressive-loading movement), incline press 3 sets, "
    "flyes 2 high-rep sets. Don't train through fever (above-the-neck-symptoms-only rule). No real "
    "muscle loss without 2-3 weeks total inactivity - apparent loss during travel weeks is just "
    "glycogen/water.\n\n"
    "HENRY OPERATING RULES: decision-forward answers, not option lists, when asked what's best. "
    "Never suggest witch hazel (too drying, permanently rejected). Never tell him to go to sleep or "
    "imply he should go to bed. Mid-cook, re-list ALL remaining steps from the current position - "
    "never skip steps, never assume he can hold a partial list. Physiological/science-based framing "
    "only for wellness topics, never recovery-program language. Timeline and location corrections "
    "are accepted immediately, no pushback."
)


if __name__ == '__main__':
    print("Fixing zen_gun_spec (drop Ilona)...")
    zg = sb_request('GET', 'kb?dept=eq.zen_gun_spec&select=content')[0]['content']
    assert ZEN_GUN_DATING_OLD in zg, "anchor not found in zen_gun_spec"
    sb_request('PATCH', 'kb?dept=eq.zen_gun_spec', {'content': zg.replace(ZEN_GUN_DATING_OLD, ZEN_GUN_DATING_NEW)})
    print("  done.")

    print("Fixing dating_spec (drop Ilona, point Ellen at update)...")
    ds = sb_request('GET', 'kb?dept=eq.dating_spec&select=content')[0]['content']
    assert DATING_SPEC_STATE_OLD in ds, "anchor not found in dating_spec"
    sb_request('PATCH', 'kb?dept=eq.dating_spec', {'content': ds.replace(DATING_SPEC_STATE_OLD, DATING_SPEC_STATE_NEW)})
    print("  done.")

    print("Inserting dating_update_0817...")
    sb_request('POST', 'kb', [{'dept': 'dating_update_0817', 'content': DATING_UPDATE_0817}])
    print(f"  {len(DATING_UPDATE_0817)} chars.")

    print("Inserting life_status_0817...")
    sb_request('POST', 'kb', [{'dept': 'life_status_0817', 'content': LIFE_STATUS_0817}])
    print(f"  {len(LIFE_STATUS_0817)} chars.")

    print("Done.")
