import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.country_code import CountryCode
from plaid.model.products import Products

app = Flask(__name__)
CORS(app)

PLAID_CLIENT_ID = os.environ.get('PLAID_CLIENT_ID')
PLAID_SECRET = os.environ.get('PLAID_SECRET')
PLAID_ENV = os.environ.get('PLAID_ENV', 'sandbox')

# Only Sandbox and Production exist in plaid-python 39+
env_map = {
    'sandbox': plaid.Environment.Sandbox,
    'production': plaid.Environment.Production,
}

configuration = plaid.Configuration(
    host=env_map.get(PLAID_ENV, plaid.Environment.Sandbox),
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET,
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# In-memory token store — persists until Render restarts
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
        )
        response = client.link_token_create(req)
        return jsonify({'link_token': response['link_token']})
    except plaid.ApiException as e:
        body = json.loads(e.body)
        return jsonify({'error': body}), 400


@app.route('/exchange_token', methods=['POST'])
def exchange_token():
    try:
        public_token = request.json.get('public_token')
        req = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = client.item_public_token_exchange(req)
        access_tokens['default'] = response['access_token']
        return jsonify({'success': True})
    except plaid.ApiException as e:
        body = json.loads(e.body)
        return jsonify({'error': body}), 400


@app.route('/balance', methods=['GET'])
def get_balance():
    try:
        access_token = access_tokens.get('default')
        if not access_token:
            return jsonify({'error': 'No bank connected yet', 'connected': False}), 401

        req = AccountsBalanceGetRequest(access_token=access_token)
        response = client.accounts_balance_get(req)

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

        return jsonify({
            'accounts': accounts,
            'total_available': round(total, 2),
            'connected': True,
        })
    except plaid.ApiException as e:
        body = json.loads(e.body)
        return jsonify({'error': body}), 400


@app.route('/transactions', methods=['GET'])
def get_transactions():
    try:
        access_token = access_tokens.get('default')
        if not access_token:
            return jsonify({'error': 'No bank connected yet', 'connected': False}), 401

        req = TransactionsSyncRequest(access_token=access_token)
        response = client.transactions_sync(req)

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
        body = json.loads(e.body)
        return jsonify({'error': body}), 400


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
