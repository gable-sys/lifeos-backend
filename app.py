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
        return jsonify({'success': True})
    except plaid.ApiException as e:
        return jsonify({'error': json.loads(e.body)}), 400


@app.route('/balance', methods=['GET'])
def get_balance():
    try:
        access_token = access_tokens.get('default')
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
        access_token = access_tokens.get('default')
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




# ElevenLabs pre-made voice IDs (stable, verified)
# See: https://elevenlabs.io/docs/voices/pre-made-voices
SCHOLAR_VOICES = {
    'Ernest Hemingway':    'TxGEqnHWrfWFTfGW9XjX',  # Josh - deep American male
    'Mark Twain':          'VR6AewLTigWG4xSOukaG',   # Arnold - warm older male
    'Napoleon Bonaparte':  'pNInz6obpgDQGcFmaJgB',   # Adam - authoritative male
    'Marcus Aurelius':     'onwK4e9ZLuTAKqWW03F9',   # Daniel - calm British male
    'Simone de Beauvoir':  'XB0fDUnXU5powFXDhCwa',   # Charlotte - British female (closest to French accent)
    'Henry Miller':        'TxGEqnHWrfWFTfGW9XjX',   # Josh - gruff American
    'Edmond Dantes':       'ErXwobaYiN019PkySvjV',   # Antoni - warm dramatic male
    'Fyodor Dostoevsky':   'onwK4e9ZLuTAKqWW03F9',   # Daniel - intense measured
    'default':             'TxGEqnHWrfWFTfGW9XjX',   # Josh fallback
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
        
        # Use a single reliable voice ID - Rachel (verified working)
        voice_id = 'TxGEqnHWrfWFTfGW9XjX'
        
        r = req_lib.post(
            f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}',
            headers={
                'Accept': 'audio/mpeg',
                'Content-Type': 'application/json',
                'xi-api-key': api_key,
            },
            json={
                'text': text,
                'model_id': 'eleven_monolingual_v1',
                'voice_settings': {'stability': 0.5, 'similarity_boost': 0.75}
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


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
