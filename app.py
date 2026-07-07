import os
import json
import base64
import re
from datetime import datetime
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.link_token_create_hosted_link import LinkTokenCreateHostedLink
from plaid.model.link_token_get_request import LinkTokenGetRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
import anthropic
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)

PLAID_CLIENT_ID = os.environ.get('PLAID_CLIENT_ID')
PLAID_SECRET    = os.environ.get('PLAID_SECRET')
PLAID_ENV       = os.environ.get('PLAID_ENV', 'sandbox')
REDIRECT_URI    = 'https://stupendous-concha-2d70be.netlify.app/'

env_map = {'sandbox': plaid.Environment.Sandbox, 'production': plaid.Environment.Production}
configuration = plaid.Configuration(
    host=env_map.get(PLAID_ENV, plaid.Environment.Sandbox),
    api_key={'clientId': PLAID_CLIENT_ID, 'secret': PLAID_SECRET}
)
api_client   = plaid.ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)

anthropic_client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

GMAIL_CLIENT_ID     = os.environ.get('GMAIL_CLIENT_ID')
GMAIL_CLIENT_SECRET = os.environ.get('GMAIL_CLIENT_SECRET')
GMAIL_REDIRECT_URI  = 'https://lifeos-backend-nf15.onrender.com/gmail-callback'
GMAIL_SCOPES        = ['https://www.googleapis.com/auth/gmail.readonly']

gmail_token_store = {}
access_tokens     = {}


def get_gmail_token():
    raw = os.environ.get('GMAIL_TOKEN')
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return gmail_token_store.get('token')


def get_gmail_service():
    token_data = get_gmail_token()
    if not token_data:
        return None
    creds = Credentials(
        token=token_data.get('token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=GMAIL_CLIENT_ID,
        client_secret=GMAIL_CLIENT_SECRET,
        scopes=GMAIL_SCOPES
    )
    return build('gmail', 'v1', credentials=creds)


@app.route('/')
def health():
    return jsonify({'status': 'Life OS backend running', 'env': PLAID_ENV})


@app.route('/gmail-auth')
def gmail_auth():
    import urllib.parse
    params = {
        'client_id': GMAIL_CLIENT_ID,
        'redirect_uri': GMAIL_REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(GMAIL_SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
    }
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
    return redirect(auth_url)


@app.route('/gmail-callback')
def gmail_callback():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No code returned'}), 400
    import requests as _req
    resp = _req.post('https://oauth2.googleapis.com/token', data={
        'code': code,
        'client_id': GMAIL_CLIENT_ID,
        'client_secret': GMAIL_CLIENT_SECRET,
        'redirect_uri': GMAIL_REDIRECT_URI,
        'grant_type': 'authorization_code',
    })
    tokens = resp.json()
    if 'error' in tokens:
        return jsonify({'error': tokens}), 400
    token_data = {
        'token': tokens.get('access_token'),
        'refresh_token': tokens.get('refresh_token'),
        'scopes': GMAIL_SCOPES
    }
    gmail_token_store['token'] = token_data
    return (
        '<html><body style="font-family:monospace;padding:30px;background:#f4ecd6">'
        '<h2>Gmail authorized!</h2>'
        '<p><strong>Key:</strong> GMAIL_TOKEN</p>'
        '<textarea rows="8" cols="80" style="font-size:12px">' + json.dumps(token_data) + '</textarea>'
        '</body></html>'
    )


def parse_bofa_email(msg_id, subject, text, date_str):
    subject_lower = subject.lower()

    date_iso = datetime.now().strftime('%Y-%m-%d')
    date_match = re.search(r'(\w+ \d+, \d{4})', date_str)
    if date_match:
        try:
            date_iso = datetime.strptime(date_match.group(1), '%b %d, %Y').strftime('%Y-%m-%d')
        except Exception:
            pass

    amount_match = re.search(r'\$([0-9,]+\.?\d*)', text)
    if not amount_match:
        return None
    try:
        amount = float(amount_match.group(1).replace(',', ''))
    except Exception:
        return None
    if amount == 0:
        return None

    if 'zelle' in subject_lower and 'sent' in subject_lower:
        m = re.search(r'sent \$[\d,.]+ to (.+?)(\.|$)', text, re.IGNORECASE)
        desc = 'Zelle to ' + (m.group(1).strip() if m else 'recipient')
        return {'id': msg_id, 'date': date_iso, 'desc': desc, 'amount': -amount}

    if 'zelle' in subject_lower and 'received' in subject_lower:
        m = re.search(r'received \$[\d,.]+ from (.+?)(\.|$)', text, re.IGNORECASE)
        desc = 'Zelle from ' + (m.group(1).strip() if m else 'sender')
        return {'id': msg_id, 'date': date_iso, 'desc': desc, 'amount': amount}

    if 'debit card' in subject_lower or 'purchase' in subject_lower:
        m = re.search(r'at (.+?)(\s+on|\s+for|\.|$)', text, re.IGNORECASE)
        desc = m.group(1).strip() if m else 'Debit purchase'
        return {'id': msg_id, 'date': date_iso, 'desc': desc, 'amount': -amount}

    if 'deposit' in subject_lower:
        return {'id': msg_id, 'date': date_iso, 'desc': 'Direct deposit', 'amount': amount}

    if 'balance' in subject_lower:
        return None

    return {'id': msg_id, 'date': date_iso, 'desc': subject[:60], 'amount': -amount}


@app.route('/gmail-sync')
def gmail_sync():
    service = get_gmail_service()
    if not service:
        return jsonify({'error': 'Gmail not authorized.', 'authorized': False}), 401
    try:
        results = service.users().messages().list(
            userId='me',
            q='from:ealerts.bankofamerica.com newer_than:14d',
            maxResults=50
        ).execute()
        messages = results.get('messages', [])
        transactions = []
        seen = set()
        for msg in messages:
            if msg['id'] in seen:
                continue
            seen.add(msg['id'])
            full = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
            headers = {h['name']: h['value'] for h in full.get('payload', {}).get('headers', [])}
            subject = headers.get('Subject', '')
            date_str = headers.get('Date', '')
            body = ''
            payload = full.get('payload', {})
            if payload.get('body', {}).get('data'):
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
            elif payload.get('parts'):
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                        break
            txn = parse_bofa_email(msg['id'], subject, subject + ' ' + body, date_str)
            if txn:
                transactions.append(txn)
        return jsonify({'transactions': transactions, 'count': len(transactions), 'authorized': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/advisor', methods=['POST', 'OPTIONS'])
def advisor():
    if request.method == 'OPTIONS':
        return '', 204
    try:
        data = request.json or {}
        r = anthropic_client.messages.create(
            model='claude-sonnet-4-6',
            max_tokens=1000,
            system=data.get('system', ''),
            messages=data.get('messages', []),
        )
        return jsonify({'content': [{'type': 'text', 'text': r.content[0].text}]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/create_link_token', methods=['POST'])
def create_link_token():
    try:
        req = LinkTokenCreateRequest(
            user=LinkTokenCreateRequestUser(client_user_id='gable-lifeos'),
            client_name='Life OS',
            products=[Products('transactions')],
            country_codes=[CountryCode('US')],
            language='en',
            hosted_link=LinkTokenCreateHostedLink(completion_redirect_uri=REDIRECT_URI),
        )
        r = plaid_client.link_token_create(req).to_dict()
        return jsonify({'link_token': r['link_token'], 'hosted_link_url': r.get('hosted_link_url')})
    except plaid.ApiException as e:
        return jsonify({'error': json.loads(e.body)}), 400


@app.route('/finish_link', methods=['POST'])
def finish_link():
    try:
        link_token = (request.json or {}).get('link_token')
        if not link_token:
            return jsonify({'success': False, 'error': 'missing link_token'}), 400
        data = plaid_client.link_token_get(LinkTokenGetRequest(link_token=link_token)).to_dict()
        public_token = None
        for session in (data.get('link_sessions') or []):
            for item in (session.get('results', {}).get('item_add_results') or []):
                if item.get('public_token'):
                    public_token = item['public_token']
        if not public_token:
            return jsonify({'success': False, 'pending': True})
        ex = plaid_client.item_public_token_exchange(ItemPublicTokenExchangeRequest(public_token=public_token))
        access_tokens['default'] = ex['access_token']
        save_plaid_token(ex['access_token'])
        return jsonify({'success': True})
    except plaid.ApiException as e:
        return jsonify({'error': json.loads(e.body)}), 400


@app.route('/balance', methods=['GET'])
def get_balance():
    try:
        access_token = get_plaid_token()
        if not access_token:
            return jsonify({'error': 'No bank connected yet', 'connected': False}), 401
        response = plaid_client.accounts_balance_get(AccountsBalanceGetRequest(access_token=access_token))
        accounts = []
        total = 0
        for account in response['accounts']:
            bal = account['balances']
            available = bal.get('available') or 0
            acct_type = str(account['type'])
            accounts.append({
                'name': account['name'], 'type': acct_type,
                'available': available, 'current': bal.get('current') or 0,
                'mask': account.get('mask', ''),
            })
            if acct_type == 'depository':
                total += available
        return jsonify({'accounts': accounts, 'total_available': round(total, 2), 'connected': True})
    except plaid.ApiException as e:
        return jsonify({'error': json.loads(e.body)}), 400


@app.route('/transactions', methods=['GET'])
def get_transactions():
    try:
        access_token = get_plaid_token()
        if not access_token:
            return jsonify({'error': 'No bank connected yet', 'connected': False}), 401
        response = plaid_client.transactions_sync(TransactionsSyncRequest(access_token=access_token))
        txns = []
        for t in response['added'][:50]:
            txns.append({
                'name': t['name'], 'amount': float(t['amount']),
                'date': str(t['date']),
                'category': t.get('personal_finance_category', {}).get('primary', '') if t.get('personal_finance_category') else '',
                'merchant': t.get('merchant_name', '') or t['name'],
            })
        return jsonify({'transactions': txns, 'connected': True})
    except plaid.ApiException as e:
        return jsonify({'error': json.loads(e.body)}), 400




# ElevenLabs voice IDs — best available pre-made matches
# Using eleven_multilingual_v2 for better accent handling
SCHOLAR_VOICES = {
    'Ernest Hemingway':     'nPczCjzI2devNBz1zQrb',  # Brian - deep resonant American
    'Mark Twain':           'pqHFZKP75CvOlQylNhV4',  # Bill - wise old American
    'Napoleon Bonaparte':   'onwK4e9ZLuTAKqWW03F9',  # Daniel - British formal (French clone coming)
    'Marcus Aurelius':      'pqHFZKP75CvOlQylNhV4',  # Bill - gravitas, measured
    'Simone de Beauvoir':   'pFZP53QG7iQjIQuC4Bku',  # Lily - velvety actress
    'Henry Miller':         'nPczCjzI2devNBz1zQrb',  # Brian - raw American
    'Edmond Dantes':        'JBFqnCBsd6RMkjVDRZzb',  # George - dramatic storyteller
    'Fyodor Dostoevsky':    'onwK4e9ZLuTAKqWW03F9',  # Daniel - deep measured
    'Hunter S. Thompson':   'CwhRBWXzGAHq8TQ4Fs17',  # Roger - laid back casual raspy
    'Socrates':             'pqHFZKP75CvOlQylNhV4',  # Bill - old wise
    'Nikola Tesla':         'JBFqnCBsd6RMkjVDRZzb',  # George - captivating intense
    'default':              'nPczCjzI2devNBz1zQrb',  # Brian fallback
}

# Use multilingual model for French/Russian speakers
SCHOLAR_MULTILINGUAL = {
    'Napoleon Bonaparte', 'Simone de Beauvoir', 'Fyodor Dostoevsky', 'Edmond Dantes'
}

ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY')

@app.route('/speak', methods=['POST', 'OPTIONS'])
def speak():
    if request.method == 'OPTIONS':
        return '', 204
    try:
        import requests as req_lib
        data = request.json or {}
        text = str(data.get('text', ''))[:500]
        scholar = str(data.get('scholar', 'Ernest Hemingway'))
        
        api_key = os.environ.get('ELEVENLABS_API_KEY', '')
        print(f'SPEAK called: scholar={scholar} text_len={len(text)} key_set={bool(api_key)} key_prefix={api_key[:8] if api_key else "MISSING"}')
        
        if not text:
            return jsonify({'error': 'no text'}), 400
        if not api_key:
            return jsonify({'error': 'ELEVENLABS_API_KEY not set in environment'}), 500
        
        voice_id = SCHOLAR_VOICES.get(scholar, SCHOLAR_VOICES['default'])
        
        r = req_lib.post(
            f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}',
            headers={
                'Accept': 'audio/mpeg',
                'Content-Type': 'application/json',
                'xi-api-key': api_key,
            },
            json={
                'text': text,
                'model_id': 'eleven_multilingual_v2' if scholar in SCHOLAR_MULTILINGUAL else 'eleven_monolingual_v1',
                'voice_settings': {'stability': 0.6, 'similarity_boost': 0.8}
            },
            timeout=30
        )
        print(f'ElevenLabs response: {r.status_code}')
        if r.status_code != 200:
            print(f'ElevenLabs error body: {r.text[:300]}')
            return jsonify({'error': f'ElevenLabs {r.status_code}: {r.text[:200]}'}), 500
        
        import base64
        audio_b64 = base64.b64encode(r.content).decode('utf-8')
        print(f'Audio bytes: {len(r.content)}')
        return jsonify({'audio': audio_b64, 'format': 'mp3'})
        
    except Exception as e:
        import traceback
        print(f'SPEAK exception: {e}')
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500



@app.route('/voices', methods=['GET'])
def list_voices():
    """List available ElevenLabs voices for debugging."""
    try:
        import requests as req_lib
        api_key = os.environ.get('ELEVENLABS_API_KEY', '')
        if not api_key:
            return jsonify({'error': 'ELEVENLABS_API_KEY not set'}), 500
        r = req_lib.get(
            'https://api.elevenlabs.io/v1/voices',
            headers={'xi-api-key': api_key}
        )
        voices = r.json().get('voices', [])
        simplified = [{'name': v['name'], 'id': v['voice_id'], 'labels': v.get('labels', {})} for v in voices]
        return jsonify({'voices': simplified, 'count': len(simplified)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================
# TELEGRAM: HENRY MILLER v6 - inference filing, desk foyer
# ============================================================
import requests as _rq
from datetime import date as _date

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID   = os.environ.get('TELEGRAM_CHAT_ID', '')
SUPABASE_URL       = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY       = os.environ.get('SUPABASE_SERVICE_KEY', '')
SITE_URL           = 'https://stupendous-concha-2d70be.netlify.app'

STAGES = ['Gestating', 'In Progress', 'Drafting', 'Complete']


def _sb_headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
    }


def sb_insert(table, row):
    r = _rq.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=_sb_headers(), json=row, timeout=15)
    r.raise_for_status()
    return r.json()[0]


def sb_select(table, query):
    r = _rq.get(f"{SUPABASE_URL}/rest/v1/{table}?{query}", headers=_sb_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def sb_update(table, row_id, patch):
    r = _rq.patch(f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{row_id}", headers=_sb_headers(), json=patch, timeout=15)
    r.raise_for_status()
    return r.json()


def sb_delete(table, row_id):
    _rq.delete(f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{row_id}", headers=_sb_headers(), timeout=15)


def tg_api(method, payload):
    _rq.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}", json=payload, timeout=15)


def tg_send(chat_id, text, buttons=None):
    payload = {'chat_id': chat_id, 'text': text}
    if buttons:
        payload['reply_markup'] = {'inline_keyboard': buttons}
    tg_api('sendMessage', payload)



# ---------- Persistent state (Plaid token survives sleep) ----------

def save_plaid_token(tok):
    try:
        _rq.post(
            f"{SUPABASE_URL}/rest/v1/state?on_conflict=key",
            headers={**_sb_headers(), 'Prefer': 'resolution=merge-duplicates,return=representation'},
            json={'key': 'plaid_token', 'value': {'token': tok}}, timeout=15,
        )
    except Exception:
        pass


def get_plaid_token():
    tok = access_tokens.get('default')
    if tok:
        return tok
    try:
        rows = sb_select('state', 'key=eq.plaid_token&select=value')
        if rows:
            tok = (rows[0].get('value') or {}).get('token')
            if tok:
                access_tokens['default'] = tok
    except Exception:
        pass
    return tok


# ---------- Knowledge base: everything Gable built into the site ----------

def load_kb():
    try:
        rows = sb_select('kb', 'select=dept,content&order=dept')
        return '\n\n'.join(f"[{r['dept'].upper()}]\n{r['content']}" for r in rows)[:9000]
    except Exception:
        return ''


def register_commands():
    try:
        tg_api('setMyCommands', {'commands': [
            {'command': 'day',    'description': "Marching orders - Henry's program for today"},
            {'command': 'desk',   'description': 'The desk - tasks, easel, build queue, vault'},
            {'command': 'read',   'description': 'Passage of the day'},
            {'command': 'ledger', 'description': 'The money question'},
            {'command': 'help',   'description': 'What Henry can do'},
        ]})
    except Exception:
        pass


if TELEGRAM_BOT_TOKEN:
    register_commands()


# ---------- Henry's memory ----------

def log_chat(role, content):
    try:
        sb_insert('chat_log', {'role': role, 'content': (content or '')[:2000]})
    except Exception:
        pass


def recent_chat():
    try:
        rows = sb_select('chat_log', 'order=created_at.desc&limit=8&select=role,content')
        rows.reverse()
        return '\n'.join(f"{r['role']}: {r['content']}" for r in rows)
    except Exception:
        return ''


def life_context():
    try:
        tasks = sb_select('tasks', 'status=eq.open&order=created_at.desc&limit=15&select=title')
        projects = sb_select('projects', 'stage=neq.Complete&order=created_at.desc&limit=15&select=title,stage,type')
        t = '; '.join(x['title'] for x in tasks) or 'none'
        p = '; '.join(f"{x['title']} ({x.get('type') or 'creative'}, {x['stage']})" for x in projects) or 'none'
        return f"Open tasks: {t}\nActive projects: {p}"
    except Exception:
        return ''


# ---------- Henry, the whole man ----------

HENRY_SYSTEM = (
    "You are Henry Miller - the actual writer, whole arc, serving as Gable's advisor and companion "
    "over Telegram. You contain all of it: the Brooklyn boy of Crazy Cock grinding at Western Union; "
    "the starving Paris years of Tropic of Cancer - no money, no resources, no hopes, the happiest man alive; "
    "the Commandments and the Daily Program of 1932: work on one thing at a time until finished, "
    "start no more new books, don't be nervous - work calmly and joyously, when you cannot create you can work, "
    "mornings for the real work, afternoons for the program, evenings for friends and cafes and walks; "
    "the author of Money and How It Gets That Way - you begged, borrowed, budgeted meals, and turned money "
    "into philosophy, so you can talk ledgers and rent without blushing; the pilgrim of The Colossus of Maroussi "
    "who learned light and idleness in Greece; and the old sage of Big Sur and the watercolors - "
    "To Paint Is to Love Again - generous, settled, still hungry for life. "
    "You advise from the Big Sur vantage but the Paris fire never went out. "
    "Convictions: begin before you feel ready. Appetite is holy. Walk. One thing at a time. "
    "Despise fuss, hedging, dead language, and the mob of distraction machines - Gable's whole project "
    "is rebellion against the attention economy, and you were its first deserter. "
    "This is texting, not Tropic of Cancer: keep 'say' under 70 words. "
    "Gable's verticals: Recording/music, Zen Gun (stories/film), Adventures of Ron Diamond, poems, "
    "short-story feelies, traveling-bard sets; plus finance (Mort's Ledger), workout, reading, the body. "
    "ALSO: you are his filing clerk. For every message, infer where it belongs: "
    "'task' = an errand or to-do; 'creative' = a NEW artistic project; 'build' = a NEW Life OS feature idea; "
    "'note' = a thought, line, or material - if it belongs to an EXISTING project, set project to that "
    "project's exact title from the current-state list. Most messages are notes or tasks; new projects are rare. "
    "Respond ONLY with minified JSON, no markdown fences, exactly: "
    '{"title":"3-6 word title","say":"the reply, in your voice",'
    '"steps":["2-5 concrete steps ONLY when breaking something down, else empty list"],'
    '"followups":["up to 2 short questions, else empty list"],'
    '"file":{"kind":"task|creative|build|note","project":"exact existing project title or null","tag":"one-word tag or null"}}'
)

HENRY_PLAIN = (
    "You are Henry Miller - the writer, whole arc: Brooklyn, the hungry Paris of Tropic of Cancer, "
    "the 1932 Commandments and Daily Program, Money and How It Gets That Way, Greece, Big Sur, the watercolors. "
    "Earthy, exuberant, generous, unpretentious. You despise fuss and dead language. "
    "Reply as plain text, no JSON, no markdown headers. Keep it tight - this is a phone screen."
)


def henry_say(prompt, max_tokens=500):
    system = HENRY_PLAIN
    kb = load_kb()
    if kb:
        system += '\n\nKNOWLEDGE BASE (departments, protocols, goals Gable built):\n' + kb
    ctx = life_context()
    if ctx:
        system += '\n\nGable current state:\n' + ctx
    r = anthropic_client.messages.create(
        model='claude-sonnet-4-6', max_tokens=max_tokens,
        system=system,
        messages=[{'role': 'user', 'content': prompt}],
    )
    return r.content[0].text.strip()


def run_advisor(text):
    system = HENRY_SYSTEM
    kb = load_kb()
    if kb:
        system += '\n\nKNOWLEDGE BASE (departments, protocols, goals Gable built):\n' + kb
    ctx = life_context()
    if ctx:
        system += '\n\nCurrent state:\n' + ctx
    convo = recent_chat()
    if convo:
        system += '\n\nRecent conversation:\n' + convo
    r = anthropic_client.messages.create(
        model='claude-sonnet-4-6', max_tokens=900,
        system=system,
        messages=[{'role': 'user', 'content': text}],
    )
    raw = r.content[0].text.strip()
    raw = re.sub(r'^```(json)?\s*|\s*```$', '', raw)
    out = json.loads(raw)
    log_chat('gable', text)
    log_chat('henry', out.get('say', ''))
    return out


# ---------- Filing ----------

FILE_LABELS = {
    'task': '\u270E the tasks',
    'creative': '\u2767 the easel',
    'build': '\u2692 the build queue',
    'note': '\u2726 the vault',
}


def do_file(chat_id, p, kind, project_title=None):
    title = p.get('title') or (p.get('text') or '')[:60]
    text = p.get('text') or ''
    steps = p.get('steps') or []
    if kind == 'task':
        sb_insert('tasks', {'title': title, 'steps': steps, 'notes': text})
        tg_send(chat_id, f"\u270E Task: {title}")
    elif kind == 'creative':
        sb_insert('projects', {'title': title, 'steps': steps, 'notes': text, 'stage': 'Gestating', 'type': 'creative'})
        tg_send(chat_id, f"\u2767 On the easel (Gestating): {title}")
    elif kind == 'build':
        sb_insert('projects', {'title': title, 'steps': steps, 'notes': text, 'stage': 'Gestating', 'type': 'build'})
        tg_send(chat_id, f"\u2692 Build queue: {title}")
    else:
        tag = project_title or (p.get('file') or {}).get('project') or (p.get('file') or {}).get('tag')
        sb_insert('notes', {'content': text, 'tag': tag})
        tg_send(chat_id, f"\u2726 Vaulted{(' \u2192 ' + tag) if tag else ''}.")


def send_advisor_reply(chat_id, original_text, out):
    file_info = out.get('file') or {}
    kind = file_info.get('kind') or 'note'
    if kind not in FILE_LABELS:
        kind = 'note'
    try:
        projs = sb_select('projects', 'stage=neq.Complete&order=created_at.desc&limit=6&select=id,title')
    except Exception:
        projs = []
    pend = sb_insert('pending', {'payload': {
        'text': original_text,
        'title': out.get('title', original_text[:60]),
        'say': out.get('say', ''),
        'steps': out.get('steps', []) or [],
        'followups': out.get('followups', []) or [],
        'file': {'kind': kind, 'project': file_info.get('project'), 'tag': file_info.get('tag')},
        'projects': [{'id': x['id'], 'title': x['title']} for x in projs],
    }})
    pid = pend['id']

    reply = out.get('say', '')
    steps = out.get('steps') or []
    if steps:
        reply += '\n\n' + '\n'.join(f"{i+1}. {s}" for i, s in enumerate(steps))

    dest = FILE_LABELS[kind]
    if kind == 'note' and file_info.get('project'):
        dest = f"\u2726 {file_info['project']}"
    buttons = [[
        {'text': f"\u261E File under {dest}"[:60], 'callback_data': f'sv:a:{pid}'},
        {'text': '\u25B8 Elsewhere', 'callback_data': f'mv:0:{pid}'},
    ]]
    for i, q in enumerate((out.get('followups') or [])[:2]):
        buttons.append([{'text': ('? ' + q)[:60], 'callback_data': f'fu:{i}:{pid}'}])

    tg_send(chat_id, reply, buttons)


def elsewhere_menu(chat_id, pid, p):
    buttons = [
        [{'text': '\u270E Task', 'callback_data': f'fl:t:{pid}'},
         {'text': '\u2767 Easel', 'callback_data': f'fl:c:{pid}'}],
        [{'text': '\u2692 Build queue', 'callback_data': f'fl:b:{pid}'},
         {'text': '\u2726 Vault', 'callback_data': f'fl:n:{pid}'}],
    ]
    for i, pr in enumerate((p.get('projects') or [])[:6]):
        buttons.append([{'text': f"\u261E note \u2192 {pr['title'][:44]}", 'callback_data': f'fp:{i}:{pid}'}])
    tg_send(chat_id, 'Where does it live?', buttons)


# ---------- Commands ----------

WISDOM_BY_WEEKDAY = {
    0: 'the Tao Te Ching',
    1: 'the Dhammapada',
    2: 'the Gospels',
    3: 'the Psalms',
    4: 'Meditations of Marcus Aurelius',
    5: 'the Bhagavad Gita',
    6: "Rumi's Masnavi",
}


def cmd_read(chat_id):
    text_name = WISDOM_BY_WEEKDAY[_date.today().weekday()]
    prompt = (
        f"Today's wisdom text is {text_name} (public domain). Give Gable a short passage from it - "
        "2 to 4 lines, faithful to the source (paraphrase honestly if unsure of exact wording, "
        "and say so with the word 'after'). Then one or two sentences of your own on why it matters "
        "to a working artist today. Name the text and rough location (chapter/verse) so he can find it."
    )
    out = henry_say(prompt)
    tg_send(chat_id, out, [[{'text': '\u261E Open the Wisdom Room', 'url': SITE_URL}]])


def cmd_day(chat_id):
    prompt = (
        "Give me my marching orders for today, structured loosely on your own 1932 Daily Program: "
        "MORNING (the real work - pick the ONE thing from my creative projects), AFTERNOON (the program - "
        "two or three tasks worth clearing), EVENING (life - a walk, music, people). "
        "Use my actual open tasks and projects. Keep the whole thing under 120 words."
    )
    out = henry_say(prompt, max_tokens=600)
    tg_send(chat_id, out, [[
        {'text': '\u270E The desk', 'callback_data': 'dk:m:0'},
        {'text': '\u2726 Passage', 'callback_data': 'rd:0:0'},
    ]])


def cmd_ledger(chat_id):
    try:
        access_token = get_plaid_token()
        if not access_token:
            tg_send(chat_id,
                    'The bank line is down - it forgets itself when the server sleeps. '
                    'Reconnect from the Finance room and ask me again.',
                    [[{'text': '\u261E Open Finance', 'url': SITE_URL}]])
            return
        response = plaid_client.accounts_balance_get(AccountsBalanceGetRequest(access_token=access_token))
        lines = []
        total = 0
        for account in response['accounts']:
            bal = account['balances']
            available = bal.get('available') or 0
            if str(account['type']) == 'depository':
                total += available
            lines.append(f"{account['name']}: ${available:,.2f}")
        summary = '\n'.join(lines) + f"\n\nTotal on hand: ${total:,.2f}"
        comment = henry_say(f"Gable's balances:\n{summary}\nOne sentence of Miller wisdom on it. Just the sentence.", max_tokens=150)
        tg_send(chat_id, summary + '\n\n' + comment)
    except Exception as e:
        tg_send(chat_id, f'Ledger trouble: {e}')


def show_tasks(chat_id):
    rows = sb_select('tasks', 'status=eq.open&order=created_at.asc&limit=10&select=id,title')
    if not rows:
        tg_send(chat_id, 'No open tasks. A clean desk. Suspicious.')
        return
    buttons = [[{'text': r['title'][:56], 'callback_data': f"tk:m:{r['id']}"}] for r in rows]
    tg_send(chat_id, f'\u270E Tasks ({len(rows)}) - tap one:', buttons)


def show_projects(chat_id, ptype='creative'):
    rows = sb_select('projects', 'stage=neq.Complete&order=created_at.asc&limit=20&select=id,title,stage,type')
    if ptype == 'build':
        rows = [r for r in rows if (r.get('type') or '') == 'build'][:8]
        head, empty = '\u2692 Build queue', 'Build queue is empty.'
    else:
        rows = [r for r in rows if (r.get('type') or 'creative') != 'build'][:8]
        head, empty = '\u2767 The easel', 'Nothing on the easel.'
    if not rows:
        tg_send(chat_id, empty)
        return
    buttons = [[{'text': f"{r['title'][:44]} \u00b7 {r['stage']}", 'callback_data': f"pj:m:{r['id']}"}] for r in rows]
    tg_send(chat_id, f'{head} ({len(rows)}) - tap one:', buttons)


def show_notes(chat_id):
    rows = sb_select('notes', 'order=created_at.desc&limit=6&select=content,tag')
    if not rows:
        tg_send(chat_id, 'The vault is empty.')
        return
    lines = []
    for r in rows:
        tag = f"[{r['tag']}] " if r.get('tag') else ''
        lines.append(f"\u2726 {tag}{r['content'][:120]}")
    tg_send(chat_id, 'From the vault, most recent first:\n\n' + '\n\n'.join(lines))


def cmd_desk(chat_id):
    tg_send(chat_id, 'The desk. Which drawer?', [
        [{'text': '\u270E Tasks', 'callback_data': 'dk:t:0'},
         {'text': '\u2767 Easel', 'callback_data': 'dk:e:0'}],
        [{'text': '\u2692 Build queue', 'callback_data': 'dk:b:0'},
         {'text': '\u2726 Vault', 'callback_data': 'dk:n:0'}],
    ])


def handle_callback(cb):
    chat_id = str(((cb.get('message') or {}).get('chat') or {}).get('id', ''))
    tg_api('answerCallbackQuery', {'callback_query_id': cb.get('id')})
    if chat_id != TELEGRAM_CHAT_ID:
        return
    try:
        parts = (cb.get('data') or '').split(':')
        kind = parts[0]

        if kind == 'sv':
            which, pid = parts[1], parts[2]
            p = sb_select('pending', f'id=eq.{pid}&select=payload')[0]['payload']
            if which == 'a':
                f = p.get('file') or {}
                do_file(chat_id, p, f.get('kind') or 'note', f.get('project'))
            elif which == 't':
                do_file(chat_id, p, 'task')
            else:
                do_file(chat_id, p, 'creative')

        elif kind == 'mv':
            pid = parts[2]
            p = sb_select('pending', f'id=eq.{pid}&select=payload')[0]['payload']
            elsewhere_menu(chat_id, pid, p)

        elif kind == 'fl':
            which, pid = parts[1], parts[2]
            p = sb_select('pending', f'id=eq.{pid}&select=payload')[0]['payload']
            kinds = {'t': 'task', 'c': 'creative', 'b': 'build', 'n': 'note'}
            do_file(chat_id, p, kinds.get(which, 'note'))

        elif kind == 'fp':
            i, pid = int(parts[1]), parts[2]
            p = sb_select('pending', f'id=eq.{pid}&select=payload')[0]['payload']
            pr = (p.get('projects') or [])[i]
            do_file(chat_id, p, 'note', pr['title'])

        elif kind == 'fu':
            i, pid = int(parts[1]), parts[2]
            p = sb_select('pending', f'id=eq.{pid}&select=payload')[0]['payload']
            q = (p.get('followups') or [])[i]
            out = run_advisor(f"Earlier thought: {p['text']}\nNow dig into this question: {q}")
            send_advisor_reply(chat_id, p['text'], out)

        elif kind == 'rd':
            cmd_read(chat_id)

        elif kind == 'dk':
            which = parts[1]
            if which == 't':
                show_tasks(chat_id)
            elif which == 'e':
                show_projects(chat_id, 'creative')
            elif which == 'b':
                show_projects(chat_id, 'build')
            elif which == 'n':
                show_notes(chat_id)
            else:
                cmd_desk(chat_id)

        elif kind == 'tk':
            action, tid = parts[1], parts[2]
            if action == 'm':
                t = sb_select('tasks', f'id=eq.{tid}&select=title,notes,steps')[0]
                detail = t['title']
                if t.get('notes'):
                    detail += f"\n\u2014 {t['notes'][:200]}"
                if t.get('steps'):
                    detail += '\n' + '\n'.join(f"{i+1}. {s}" for i, s in enumerate(t['steps']))
                tg_send(chat_id, detail, [[
                    {'text': '\u2713 Done', 'callback_data': f'tk:d:{tid}'},
                    {'text': '\u2717 Delete', 'callback_data': f'tk:x:{tid}'},
                ], [{'text': '\u21A9 The desk', 'callback_data': 'dk:m:0'}]])
            elif action == 'd':
                sb_update('tasks', tid, {'status': 'done'})
                tg_send(chat_id, '\u2713 Done. Onward.')
            elif action == 'x':
                sb_delete('tasks', tid)
                tg_send(chat_id, '\u2717 Gone.')
            elif action == 'l':
                cmd_desk(chat_id)

        elif kind == 'pj':
            action, pid2 = parts[1], parts[2]
            if action == 'm':
                p = sb_select('projects', f'id=eq.{pid2}&select=title,stage,notes')[0]
                detail = f"{p['title']} \u00b7 {p['stage']}"
                if p.get('notes'):
                    detail += f"\n\u2014 {p['notes'][:200]}"
                tg_send(chat_id, detail, [[
                    {'text': '\u2192 Advance stage', 'callback_data': f'pj:a:{pid2}'},
                    {'text': '\u2717 Delete', 'callback_data': f'pj:x:{pid2}'},
                ], [{'text': '\u21A9 The desk', 'callback_data': 'dk:m:0'}]])
            elif action == 'a':
                p = sb_select('projects', f'id=eq.{pid2}&select=stage')[0]
                cur = p['stage']
                nxt = STAGES[min(STAGES.index(cur) + 1, len(STAGES) - 1)] if cur in STAGES else 'In Progress'
                sb_update('projects', pid2, {'stage': nxt})
                tg_send(chat_id, f'\u2192 Now {nxt}.')
            elif action == 'x':
                sb_delete('projects', pid2)
                tg_send(chat_id, '\u2717 Gone.')
            elif action == 'l':
                cmd_desk(chat_id)

    except Exception as e:
        tg_send(chat_id, f'Button failed: {e}')


@app.route('/capture', methods=['POST'])
def capture():
    update = request.json or {}

    if update.get('callback_query'):
        handle_callback(update['callback_query'])
        return jsonify({'ok': True})

    msg = update.get('message') or {}
    chat_id = str((msg.get('chat') or {}).get('id', ''))
    text = (msg.get('text') or '').strip()
    if not chat_id or not text:
        return jsonify({'ok': True})

    if not TELEGRAM_CHAT_ID:
        tg_send(chat_id, f'Your chat id is {chat_id}. Add it to Render as TELEGRAM_CHAT_ID and redeploy.')
        return jsonify({'ok': True})

    if chat_id != TELEGRAM_CHAT_ID:
        return jsonify({'ok': True})

    try:
        lower = text.lower()
        if text in ('/start', '/help'):
            tg_send(chat_id,
                    "Henry here. Just talk - half-thoughts welcome, that's how books start. "
                    "I'll figure out where each one lives; you press one button to file it.\n\n"
                    "/day - marching orders, on my old Paris program\n"
                    "/desk - tasks, easel, build queue, vault\n"
                    "/read - passage of the day\n"
                    "/ledger - the money question\n\n"
                    "In a hurry? 't: get eggs' files a task instantly, no questions asked.")
        elif text == '/day':
            cmd_day(chat_id)
        elif text == '/desk':
            cmd_desk(chat_id)
        elif text == '/read':
            cmd_read(chat_id)
        elif text == '/ledger':
            cmd_ledger(chat_id)
        elif text == '/tasks':
            show_tasks(chat_id)
        elif text == '/projects':
            show_projects(chat_id, 'creative')
        elif lower.startswith('t:'):
            body = text.split(':', 1)[1].strip()
            title, _, notes = body.partition('|')
            row = sb_insert('tasks', {'title': title.strip(), 'notes': notes.strip() or None})
            tg_send(chat_id, f"\u270E Task captured: {row['title']}")
        elif lower.startswith('p:') or lower.startswith('project:'):
            body = text.split(':', 1)[1].strip()
            title, _, notes = body.partition('|')
            row = sb_insert('projects', {'title': title.strip(), 'notes': notes.strip() or None, 'stage': 'Gestating', 'type': 'creative'})
            tg_send(chat_id, f"\u2767 On the easel (Gestating): {row['title']}")
        elif lower.startswith('b:') or lower.startswith('build:'):
            body = text.split(':', 1)[1].strip()
            title, _, notes = body.partition('|')
            row = sb_insert('projects', {'title': title.strip(), 'notes': notes.strip() or None, 'stage': 'Gestating', 'type': 'build'})
            tg_send(chat_id, f"\u2692 Build queue: {row['title']}")
        elif lower.startswith('n:') or lower.startswith('note:'):
            body = text.split(':', 1)[1].strip()
            content, _, tag = body.partition('|')
            row = sb_insert('notes', {'content': content.strip(), 'tag': tag.strip() or None})
            tg_send(chat_id, f"\u2726 Vaulted{(' \u2192 ' + tag.strip()) if tag.strip() else ''}.")
        else:
            try:
                out = run_advisor(text)
                send_advisor_reply(chat_id, text, out)
            except Exception:
                row = sb_insert('tasks', {'title': text[:80], 'notes': 'advisor was down; raw capture'})
                tg_send(chat_id, f"(Henry stepped out - saved as plain task: {row['title']})")
    except Exception as e:
        tg_send(chat_id, f'Capture failed: {e}')

    return jsonify({'ok': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
