import os
import json
from flask import Flask, request, jsonify
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

app = Flask(__name__)
CORS(app)

PLAID_CLIENT_ID = os.environ.get('PLAID_CLIENT_ID')
PLAID_SECRET = os.environ.get('PLAID_SECRET')
PLAID_ENV = os.environ.get('PLAID_ENV', 'sandbox')

# Where Plaid sends the user back AFTER they finish the hosted login.
REDIRECT_URI = 'https://stupendous-concha-2d70be.netlify.app/'

env_map = {
    'sandbox': plaid.Environment.Sandbox,
    'production': plaid.Environment.Production,
}

configuration = plaid.Configuration(
    host=env_map.get(PLAID_ENV, plaid.Environment.Sandbox),
    api_key={'clientId': PLAID_CLIENT_ID, 'secret': PLAID_SECRET}
)
api_client = plaid.ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)

# Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

# In-memory token store -- persists until Render restarts
access_tokens = {}


@app.route('/')
def health():
    return jsonify({'status': 'Life OS backend running', 'env': PLAID_ENV})


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
        return jsonify({
            'link_token': r['link_token'],
            'hosted_link_url': r.get('hosted_link_url'),
        })
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
            results = session.get('results') or {}
            for item in (results.get('item_add_results') or []):
                if item.get('public_token'):
                    public_token = item['public_token']

        if not public_token:
            return jsonify({'success': False, 'pending': True})

        ex = plaid_client.item_public_token_exchange(
            ItemPublicTokenExchangeRequest(public_token=public_token)
        )
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
            current = bal.get('current') or 0
            acct_type = str(account['type'])
            accounts.append({
                'name': account['name'],
                'type': acct_type,
                'subtype': str(account.get('subtype', '')),
                'available': available,
                'current': current,
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
                'name': t['name'],
                'amount': float(t['amount']),
                'date': str(t['date']),
                'category': t.get('personal_finance_category', {}).get('primary', '') if t.get('personal_finance_category') else '',
                'merchant': t.get('merchant_name', '') or t['name'],
            })
        return jsonify({'transactions': txns, 'connected': True})
    except plaid.ApiException as e:
        return jsonify({'error': json.loads(e.body)}), 400


@app.route('/advisor', methods=['POST'])
def advisor():
    try:
        data = request.json or {}
        persona = data.get('system', '')
        messages = data.get('messages', [])
        r = anthropic_client.messages.create(
            model='claude-sonnet-4-5-20251013',
            max_tokens=1000,
            system=persona,
            messages=messages,
        )
        return jsonify({'content': [{'type': 'text', 'text': r.content[0].text}]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
