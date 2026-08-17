"""
Task 4: seed kb with condensed reference summaries of the spec docs in
seed_batch/. Sources are large (ZEN_GUN_SPEC.md, DATING_SPEC.md,
WORKOUT_SPEC.md, plus 4 large HTML plan pages) - kb rows here follow the
existing convention (condensed reference facts, not verbatim dumps) so
load_kb()'s per-message context stays a sane size. BUSINESS_SHELF.md is
deliberately excluded (different project).

    py seed_task4_kb.py
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


ROWS = {

"zen_gun_spec": (
"ZEN GUN - self-construction spec (compiled 2026-08-05). Mission: deliberate self-construction "
"(appearance, fitness, music, dating, sobriety). Looksmaxxing-first lens applies by default to "
"food/supplement/lifestyle advice, unasked. Bases: Brooklyn/DUMBO NYC + La Crosse WI.\n\n"
"COMMUNICATION RULES: terse, decision-forward, no lectures/hedging/moralizing/platitudes. Ranked "
"recommendations, not open menus. Defer immediately to his corrections on facts/timelines. "
"Sobriety/health = physiological framing only, never recovery-program language.\n\n"
"HAIR/SKIN nightly (in order): cleanse, dry 10-15min, rice milk toner, tretinoin every other night "
"(1 pea face, 1-2 peas scalp - hairline/temples/crown, keep from eyes), moisturizer, minoxidil "
"20-30min after tret (minox nightly regardless), castor oil lashes, mouth tape. AM: vitamin C serum, "
"SPF, finasteride+vitD+zinc. Verdict window on fin+minox+tret progress: Aug-Nov 2026.\n\n"
"SOBRIETY: targeting a 40-day streak through end of Aug 2026. Primary triggers: drinking with 'the "
"boys' (Gara/Leo/Gus) and family gatherings - not random days. Rule: no drinking with the boys; "
"possible light exception with Ellen only. NA beer is a validated tool. After a slip: no moralizing, "
"physiological recovery framing (rebound insomnia days 2-4, functional day 3, peak ~day 10-14).\n\n"
"NUTRITION: ~2,600 cal / 170g protein daily. Protein backloading is his main gap - front-load eggs "
"pre-workout, flag under-eating proactively. Protein rotation: beef/chicken/chickpeas/fish (~3x fish, "
"~3x beef/wk). Ray Peat framework partially: keep anti-seed-oil + dairy + morning light, skip extreme "
"juice protocols. Single burner both locations - sequential steps only, state seasoning per component.\n\n"
"DATING (per this spec): Ellen - established, sober dates going well. Bianca (Hinge) - wine date "
"proposed, no day/time/place confirmed, needs a concrete three-part offer; she has his number, not "
"vice versa. Ilona - date set. Skill gap: cold approach; floor of 2 openers/week, daytime/cafe. "
"Protocol: always close in person, never over text.\n\n"
"STYLE: Depop/eBay/Grailed, measurement-based (pit-to-pit) not tag size. Keystone: black waistcoat "
"over white tees. Vintage Levi's 501s in non-indigo (tan/khaki/olive/brown)."
),

"dating_spec": (
"DATING SPEC (consolidated 2026-08-05). Post-breakup rebuild after a ~7yr relationship with Betty "
"(split Aug/Sep 2025). Goal: grounded masculine presence, not performed detachment. Frameworks in "
"use: Corey Wayne (3% Man), Robert Glover (No More Mr. Nice Guy), Orion Taraban, Casey Zander - "
"shared vocab: wu wei, covert contract, scoreboard, the Betty spike, non-neediness, abundance. "
"Stack order: health/sobriety is bedrock -> tasks -> dating is downstream.\n\n"
"STATE (per this spec - note it predates/differs from Zen Gun spec on Ilona): Ellen - visual artist, "
"~20 dates, escalating (sex, overnights, deepening) but a slow flat texter, which is her baseline, "
"not a disinterest signal. Not yet exclusive. Next date weekend of Aug 12. Betty - renewed feelings "
"after a park meeting; she still has feelings too per Gara's report, but felt pursued too "
"aggressively during the breakup. Plan: text her after returning from La Crosse (~Aug 12-13) inviting "
"a proper evening out, only from a calm flat state. Ilona - first date fell through, inactive.\n\n"
"COMMUNICATION RULES: treat like a bro - direct, tactical, give the move not just the observation. "
"Name a pattern once per session then move on, never relitigate/moralize/repeat. He talks in "
"lowercase stream-of-consciousness voice dumps. Loses track of dates - ASK for explicit day "
"confirmation, never infer. Text drafts must sound like real texting (lowercase, casual). Declines "
"professional-support suggestions - don't re-pitch.\n\n"
"SETTLED RULES: Ellen's texting speed carries no signal - behavior is the scoreboard, not response "
"latency. Wayne's no-contact tactics do NOT apply to Ellen (already escalating, confirmed plans). "
"Only green-lit Betty move is from a calm/outcome-indifferent state, never mid-spike. 30-day "
"no-contact rekindling rule is thin pop psychology - the Betty question is a longer-arc variable, "
"not a 60-day project. Sliver of separation: give touch/attention with space, don't over-reciprocate "
"immediately.\n\n"
"PATTERNS TO WATCH (name once, redirect): the scoreboard loop (low state -> checking -> reading "
"rejection into neutral signals -> reassurance-seeking, regenerates with new surface content); the "
"Betty spike; anticipation as a drink trigger especially Betty-related - cover the window AFTER the "
"event too, not just before.\n\n"
"Hinge: Smart Photos on, NYC. Cut mirror selfies/motion-blur/heavy filters/other-women photos. Favor "
"candid mid-playing shots (piano/banjo). Message with a specific playful observation, propose a date "
"within 5-7 messages."
),

"workout_spec": (
"WORKOUT SPEC - Gable's training methodology (handoff doc, current as of Aug 2026). This week's "
"actual day-by-day session lives in the workout_week table; this is the durable method behind it. "
"Goals in priority order: 1) shoulder width (side/medial delts, lateral raises = driver), 2) V-taper "
"(wide lats via pull-ups + tight waist), 3) bigger/wider chest (dips + DB floor press/flyes), "
"4) visible abs (revealed by diet more than crunches), 5) legs/calves (chronically neglected, "
"sprints count), 6) neck (mostly passive). Arms already strong - maintenance only, no dedicated arm "
"block.\n\n"
"EQUIPMENT: Home (NYC) = pull-up/chin-up bar + light ~15lb dumbbells only - no dips/inverted-rows/"
"pike push-ups (need park setup). Park = dip bars, pull-up bars incl. a low one for inverted rows, "
"captain's chair, bench. Track for sprints.\n\n"
"STYLE: Calisthenics-forward high-rep 'spam' style (Maximilian on YouTube). Lateral raises "
"near-daily. Light DBs = buy back difficulty with higher reps/slow tempo/pauses/single-limb "
"versions, near failure. Dead hang + support hold most days. Warm-up: bounce/breathing then "
"shoulder pass-throughs/arm circles/leg swings. Superset opposites (pull+dip, floor press+laterals) "
"to save time; big lifts straight-set. Order: bodyweight/park work first, dumbbells last. ~5 "
"training days/wk. Progressive overload + logging - beat last session, then add load.\n\n"
"CAUTIONS: Rotator cuff history (soreness/sharp pain top-outer corner, esp. rear delt flyes) - "
"moderate dip depth, never two hard dip days back to back, go light/skip rear delts if flaring, stop "
"anything that pinches. Quad DOMS - ease into Bulgarian split squats/lunges, not to failure "
"especially first session back. Sprints = leg work, ~1-2x/wk, don't stack on a hard lift day. Cap "
"hard conditioning ~2x/wk. Always pair push with pull.\n\n"
"NUTRITION (the #1 lever - hard-gainer): calorie surplus + ~160g protein/day. Appetite drops after "
"training - eat anyway, especially post-workout. Consistency over 8-12 weeks matters more than "
"exercise swaps."
),

"reading_curriculum": (
"READING CURRICULUM: 2.5yr plan 2026-2028, ~2hrs/day, 8 quarters plus optional 6mo extension. "
"4 tracks: literary (quarterly canon below), science (~1 book/mo), tech (20-30min/day), Buddhist "
"(daily).\n\n"
"NOW READING: Bible (KJV), Aeschylus Oresteia, Montaigne Essays, Faulkner (Sound & Fury -> "
"Absalom, Absalom!), Caro The Path to Power, Foote Civil War Vol.1, Dumas Monte Cristo, Dickens "
"Oliver Twist, Chekhov/Wodehouse, Python + Sowell Basic Economics.\n\n"
"BUDDHIST TRACK (daily): Rahula (wk1) -> Dhammapada 1 chapter/day -> Bodhi -> Shantideva -> "
"Nagarjuna -> Matthiessen.\n\n"
"SCIENCE ANCHORS: White, Euclid, Thoreau, Lyell, Frazer, Leopold, Darwin -> Dawkins, Feynman, Kuhn, "
"Bronowski, Diamond, Primo Levi, Carson.\n\n"
"QUARTER PLAN: Q1 Jan-Mar - Bible core, Rabelais, Gilgamesh. Q2 Apr-Jun - Iliad, Odyssey, Sophocles "
"(Oedipus/Antigone), Thucydides. Q3 Jul-Sep - Plato (Republic, Symposium, Apology), Aristotle "
"Ethics, Virgil Aeneid, Stoics, Caesar. Q4 Oct-Dec - Dante, Cervantes Quixote I, Chaucer, "
"Machiavelli, Hobbes. Q5 (Yr2 Jan-Mar) - Shakespeare (Hamlet, Lear, Macbeth +3), Quixote II, Milton "
"Paradise Lost. Q6 Apr-Jun - Dostoevsky (C&P and Brothers K done; next Idiot, Demons), Tolstoy Anna "
"Karenina, Flaubert, Melville Moby-Dick, Eliot Middlemarch. Q7 Jul-Sep - Nietzsche, Whitman, Kafka, "
"Bulgakov, Mann Magic Mountain, finish Faulkner/Foote Vol.III. Q8 Oct-Dec - Joyce Ulysses (1 "
"episode/wk, ends 'yes'), Nabokov, Baker Peregrine, Genji, Mishima, Proust Swann's Way. Extension "
"(2028 H1): Tolstoy War & Peace, Proust II-III, Kierkegaard, Gibbon, McPhee."
),

"piano_plan": (
"PIANO MASTER PLAN. Daily practice 90 min (60 min shortened: drop Block 5, Block 2 to 8 min). "
"Sunday = rest day, 30-40 min, no Block 2/5. Player type: blues/gospel feel-first, building "
"classical foundation + jazz vocabulary. Long-term goal: Schubert Piano Sonata D.960 in B-flat, "
"18-24 months out. First 8 weeks: learn everything from the score, not by ear.\n\n"
"5 DAILY BLOCKS: (1) 12min Hanon+scales - Hanon No.1-2 hands separate then together at quarter=60, "
"major/blues scales in C,G,F; (2) 13min sight reading, rotating Mikrokosmos Vol.2-3 (primary), "
"Alfred Baroque Era, Clementi, Grieg Lyric Pieces, Romantic Anthology - never fix mistakes, keep "
"moving; (3) 25min classical repertoire, one piece 2-4 weeks minimum, hands separate then together, "
"score only; (4) 20min blues/gospel - Junior Mance book, Ethel Caffie-Austin videos, daily 12-bar "
"blues in C/F/G mandatory; (5) 20min jazz theory - Berkeley Jazz Piano + Harmony parallel; Mark "
"Levine from month 4+, Dick Hyman from month 6+.\n\n"
"CLASSICAL SEQUENCE (15 pieces to the goal): Satie Gymnopedie No.1, Schubert Moment Musical No.3, "
"Grieg Arietta/Waltz Op.12, Bach Little Prelude BWV924/Notebook Minuet in G (mo.2), Clementi "
"Sonatinas (mo.3), Chopin Nocturne Op.9 No.2 (mo.3), Mendelssohn Songs Without Words (mo.4), Mozart "
"K.545 (mo.5), Bach French Suite No.2 (mo.6), Beethoven Sonata No.1 (mo.8), Chopin Preludes Op.28 "
"(mo.9), Beethoven Sonata No.2 (mo.12), Bach WTC Prelude in C (mo.14), then Schubert D.960 "
"(18-24mo).\n\n"
"BLUES/GOSPEL PHASES: mo.1-2 foundation (Junior Mance Ch.1, shuffle, Caffie-Austin comping); mo.2-3 "
"gospel/soul (Ray Charles by ear, turnarounds); mo.4+ jazz-blues crossover (substitutions, Levine "
"shell voicings). Current gaps: bass clef reading, left-hand independence (main bottleneck), chord "
"theory fluency, sight-reading speed."
),

"guitar_master_plan": (
"GUITAR MASTER PLAN. 12-week curriculum (10 yrs playing, zero theory background). 30-45 min/day. "
"Weekly rotation: Mon=Blues, Tue=Jazz chords, Wed=Bluegrass flatpicking, Thu=Theory, Fri=Gypsy "
"jazz, Sat=Blues deep dive/licks, Sun=active listening only, no guitar.\n\n"
"PHASE 1 (wk1-4) Foundation: Mon - minor pentatonic/blues scale in A, positions 1-2 then flat5, "
"bending. Tue - shell chords (root-3rd-7th), then ii-V-I (Dm7-G7-Cmaj7). Wed - alternate picking, G "
"major scale 2 octaves, crosspicking wk3-4, tunes 'Angeline the Baker'/'Salt Creek'. Thu - "
"fretboard note names, intervals, chord construction, CAGED. Fri - la pompe rhythm, 'Minor Swing'. "
"Sat - BB King vibrato licks then SRV double-stops/turnarounds.\n\n"
"PHASE 2 (wk5-8) Expansion: blues adds dominant 7 licks/position mixing; jazz = Drop-2 voicings, "
"'Autumn Leaves' fully; flatpick = crosspicking 100bpm, 'Blackberry Blossom'; theory = modes "
"(Dorian, Mixolydian); gypsy = Django licks/arpeggios, 'All of Me'.\n\n"
"PHASE 3 (wk9-12) Soloing/repertoire: bebop blues, chord-tone soloing; jazz = guide-tone soloing, "
"bebop dominant scale, 'There Will Never Be Another You'; flatpick = 'Whiskey Before Breakfast', "
"120+bpm; theory = chord subs, tritone subs; gypsy = 'Djangology', 'Swing 42'.\n\n"
"Theory order: major scale/numbers > intervals > chord construction > CAGED > ii-V-I > modes > "
"arpeggios > bebop scales > chord subs. Milestones: wk2 notes on strings 6&5 + blues scale 2 "
"positions; wk4 ii-V-I with shell chords sounds musical; wk8 all 4 styles accessible, drop-2 "
"comping, flatpicking 100bpm clean; wk12 5+ standards playable, 2+ fiddle tunes above 120bpm, one "
"performable gypsy tune. Tools: iReal Pro, Amazing Slow Downer, Tempo metronome, GuitarTuna."
),

"guitar_schedule": (
"GUITAR PRACTICE SCHEDULE. Daily session (30-45 min): 5min warmup (chromatic/spider exercises, "
"metronome 60bpm); 15min primary focus (day's main topic - e.g. chord voicing in 3 keys, licks "
"slowed 50%); 10min secondary (flatpicking technique or applied theory); 5-15min freeplay (jam over "
"an iReal Pro backing track, no stopping to fix mistakes).\n\n"
"WEEKLY ROTATION: Mon = Jazz Chords & Comping (drop-2 voicings, shell chords, ii-V-I). Tue = "
"Flatpicking & Bluegrass (crosspicking, runs, fiddle tunes). Wed = Gypsy Jazz (la pompe, Manouche "
"licks, Django repertoire). Thu = Theory on the Neck (modes, chord-scale relationships, fretboard "
"mapping). Fri = Jazz Soloing (bebop scales, guide tones, melodic vocabulary). Sat = Repertoire Day "
"(full song run-throughs, rhythm+lead). Sun = Active Listening, no guitar, 2-3 records deeply.\n\n"
"Key resources: Adam Neely, Justin Guitar Jazz, DjangoBooks.com, Bryan Sutton/ArtistWorks, Peghead "
"Nation. Books: Chord Chemistry (Ted Greene), The Jazz Theory Book (Mark Levine), Fretboard Logic "
"(Bill Edwards).\n\n"
"MILESTONES: wks1-4 shell chords, ii-V-I in 3 keys, la pompe, 2 fiddle tunes. wks5-8 drop-2 all "
"string sets, dominant bebop scale, 3 gypsy standards (Minor Swing/Nuages/All of Me), crosspicking "
"80bpm. mo.3-4: 5+ jazz standards rhythm+solo, flatpicking 100bpm, guide-tone soloing. mo.5-6: jam "
"with others, full Django tune, bluegrass rhythm behind a singer."
),

}


if __name__ == '__main__':
    try:
        existing = {r['dept'] for r in sb_request('GET', 'kb?select=dept')}
    except Exception:
        existing = set()

    total_new = 0
    for dept, content in ROWS.items():
        total_new += len(content)
        if dept in existing:
            sb_request('PATCH', f'kb?dept=eq.{dept}', {'content': content})
            print(f"  updated {dept} ({len(content)} chars)")
        else:
            sb_request('POST', 'kb', [{'dept': dept, 'content': content}])
            print(f"  inserted {dept} ({len(content)} chars)")

    print(f"Total new content: {total_new} chars")
    print("Done.")
