"""
Replaces the piano_plan kb row with the fuller operating document from
seed_batch/piano_resources.md. Preserves the 5-block daily structure
(90/60min), the classical repertoire sequence to Schubert D.960, the
blues/gospel curriculum phases, the 12-bar-every-session rule, the Friday
listening ritual, and the 8 key principles. Adds a shrink-priority note
(protect Block 4 before Block 3) and a weekly scale/book rotation so
Henry can answer "what's today's piano practice" concretely.

    py update_piano_kb_0819.py
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
        print(f"ERROR {method} {path}: {e.code} {e.read().decode()[:400]}")
        raise


PIANO_PLAN = (
    "PIANO MASTER PLAN (operating document, supersedes the old summary). Player type: blues/gospel/soul "
    "feel-first, songwriter with good ears and improv instinct, rebuilding foundational reading + theory. "
    "Bass clef reading is functional but slow, left-hand independence is the main technical gap, chord "
    "theory not yet fluent. Classical training is the gym, not the destination - goal is to become a more "
    "dangerous version of what he already is. Long-term goal: Schubert Piano Sonata D.960 in B-flat major, "
    "18-24 months out, learned as a blues player who also loves Schubert.\n\n"

    "SESSION LENGTH: full session 90min. Short session 60min - drop Block 5 entirely, shorten Block 2 to "
    "8min, everything else stays full length. Sunday is a rest day, 30-40min only - Block 2 and 5 dropped, "
    "just Block 1 (Hanon No.1/2 once each, maintenance only), Block 3 (one clean run-through) and Block 4 "
    "(12-bar in C/G/F once each, then close the books). PRIORITY IF A SESSION MUST SHRINK BELOW THE SHORT "
    "VERSION: protect Block 4 (blues) and the 12-bar ritual first - cut Block 3 (classical) before touching "
    "Block 4. Blues is the foundation and compounds daily; a skipped classical day is recoverable, a "
    "skipped 12-bar day breaks the streak.\n\n"

    "5 DAILY BLOCKS: "
    "(1) Hanon + scales, 12min - Hanon No.1-2 hands separate then together at quarter=60, slow and even "
    "beats fast and sloppy every time, focus on fingers 4/5 (weakest). Rotate C/G/F major scales (the "
    "three blues keys) plus matching blues scales daily (C blues: C-Eb-F-F#-G-Bb-C; G blues: "
    "G-Bb-C-C#-D-F-G; F blues: F-Ab-Bb-B-C-Eb-F). Hanon progression: wk1-2 No.1 only, wk3-4 add No.2, "
    "month 2 rotate ex.1-5 daily, month 3+ build toward 1-10. "
    "(2) Sight reading, 13min (8min short sessions) - rotating Mikrokosmos Vol.2-3 (primary, best for bass "
    "clef drilling), Alfred Baroque Era, Clementi Introduction, Grieg Lyric Pieces, Romantic Anthology, "
    "free choice Saturdays (World's Greatest Classical Music). Rule: always new material, never go back to "
    "fix mistakes, keep the pulse going even when missing notes. First 8 weeks: learn everything from the "
    "score, not by ear - the ear is a massive asset but right now it's a crutch blocking reading "
    "development. "
    "(3) Classical repertoire, 25min - one piece at a time, hands separate first then together in small "
    "4-8 bar sections, 2-4 weeks minimum per piece, score only, no YouTube learning for repertoire. "
    "(4) Blues & gospel, 20min - 12-BAR BLUES RITUAL: every single session, no exceptions, even rest days, "
    "run the 12-bar at least once in C, F, or G - this is the foundation and it compounds. Rotation: Junior "
    "Mance book one example/day, Ethel Caffie-Austin videos (one video, apply one thing immediately), free "
    "improv over blues changes, active listening (Otis Spann/Ray Charles/Professor Longhair - sit at the "
    "piano and find the notes). "
    "(5) Jazz theory, 20min (dropped on short sessions) - theory through music he already loves, not "
    "textbook grinding. Berkeley Harmony is a reference to consult, not a front-to-back grind.\n\n"

    "CLASSICAL SEQUENCE (do not rush, one piece at a time): 1.Satie Gymnopedie No.1 (now - already knows "
    "it, tone control/smooth LH) 2.Schubert Moment Musical No.3 in F minor (now - dark/rhythmic, LH drive) "
    "3.Grieg Arietta Op.12 No.1 (now - simple/lyrical, score reading) 4.Grieg Waltz Op.12 No.2 (now - "
    "rhythmic, builds on Arietta) 5.Bach Little Prelude BWV924 (mo.2 - finger independence, Bach intro) "
    "6.Bach Notebook Minuet in G & Musette in D (mo.2 - voice leading, both clefs) 7.Clementi Sonatinas "
    "(mo.3 - classical structure, two-hand coordination) 8.Chopin Nocturne Op.9 No.2 (mo.3 - lyrical RH "
    "over flowing LH, natural strength) 9.Mendelssohn Songs Without Words Op.19 No.1 (mo.4 - Romantic "
    "style, expressive) 10.Mozart K.545 1st mvt (mo.5 - classical form, evenness) 11.Bach French Suite "
    "No.2 Allemande (mo.6 - Bach at scale, full voice independence) 12.Beethoven Sonata No.1 1st mvt "
    "(mo.8 - dramatic, big technique jump) 13.Chopin Preludes Op.28 No.4/6/7/20 (mo.9 - short but deep, "
    "expressive range) 14.Beethoven Sonata No.2 (mo.12 - full sonata commitment) 15.Bach WTC Prelude in C "
    "(mo.14 - summit of early-intermediate Bach) then GOAL: Schubert Piano Sonata D.960 in B-flat "
    "(18-24mo).\n\n"

    "BLUES/GOSPEL CURRICULUM (Block 4 phases): mo.1-2 foundation - Junior Mance Ch.1 (Basic Blues "
    "Structures) one example/day, 12-bar in C/F/G with proper LH shuffle patterns (not block chords), "
    "Caffie-Austin LH comping videos specifically. mo.2-3 gospel & soul - one gospel progression/week from "
    "Caffie-Austin, learn one Ray Charles song by ear (\"What'd I Say\" or \"Hit the Road Jack\"), add "
    "turnarounds at bars 11-12 (I-VI-II-V or blues turnaround), start adding passing chords between main "
    "chords. mo.4+ jazz-blues crossover - jazz blues chord substitutions connecting blues to jazz "
    "vocabulary, Mark Levine shell voicings applied to blues progressions, Dick Hyman as historical survey "
    "of how stride/swing evolved from blues, Kurt Weill Centennial Anthology for unusual harmony "
    "(songwriting).\n\n"

    "JAZZ/THEORY CURRICULUM (Block 5): mo.1-3 Berkeley Jazz Piano (Santisi) front to back, chord "
    "voicings/fundamentals, run parallel with Berkeley Harmony. mo.1-6 Berkeley Harmony parallel track - "
    "reference when questions come up, pick songs he loves and name the chords. mo.4+ Mark Levine Jazz "
    "Piano Book - ch.1-4 first (two-hand/shell voicings), apply shell voicings directly to Block 4 blues, "
    "rest unfolds over 12mo. mo.3+ Jazz Standards Note for Note, one standard every 4-6 weeks, LH voicings "
    "only first. mo.6+ Dick Hyman Century of Jazz Piano - historical survey (stride/swing/bebop), "
    "advanced, let technique catch up first.\n\n"

    "WEEKLY ROTATION (so today's blocks are concrete): scales/blues-scales rotate C(Mon/Tue), G(Wed/Thu), "
    "F(Fri), all three(Sat), maintenance-only(Sun). Sight-reading book rotates Mikrokosmos(Mon/Tue/Thu), "
    "Alfred Baroque Era(Wed), Clementi(Fri), free choice(Sat), dropped(Sun). Block 4 12-bar key follows "
    "the scale of the day. Triads by weekday: Wed=major triads root position (C/F/G/D/A/E/Bb, say names "
    "aloud), Thu=minor triads same roots, Fri=dominant 7ths (C7/F7/G7).\n\n"

    "FRIDAY LISTENING RITUAL: every Friday in Block 4, close with one record, listen analytically only, "
    "no playing - Ray Charles \"Genius + Soul = Jazz,\" Junior Mance live, or Professor Longhair "
    "\"Tipitina.\" Active listening counts as practice.\n\n"

    "8 KEY PRINCIPLES: 1.From the score - learn repertoire by reading not by ear, at least the first 8 "
    "weeks. 2.Never stop during sight reading - keep the pulse, move forward. 3.Hands separate before "
    "hands together, always. 4.Slow and even beats fast and sloppy, every time. 5.12-bar blues every "
    "single session, no exceptions, even rest days. 6.Theory in context - always connect theory to music "
    "he loves, never abstract. 7.Active listening counts as practice - the Friday ritual is curriculum. "
    "8.Rest is part of learning - Sunday is a short day on purpose.\n\n"

    "CURRENT GAPS: bass clef reading (functional but slow, needs to become automatic), left-hand "
    "independence (main technical bottleneck), chord/7th theory fluency, sight-reading speed."
)


if __name__ == '__main__':
    print(f"New piano_plan content: {len(PIANO_PLAN)} chars.")
    existing = sb_request('GET', 'kb?dept=eq.piano_plan&select=content')
    if existing:
        print(f"Replacing existing piano_plan row ({len(existing[0]['content'])} chars)...")
        sb_request('PATCH', 'kb?dept=eq.piano_plan', {'content': PIANO_PLAN})
    else:
        print("No existing piano_plan row found, inserting...")
        sb_request('POST', 'kb', [{'dept': 'piano_plan', 'content': PIANO_PLAN}])
    print("Done.")
