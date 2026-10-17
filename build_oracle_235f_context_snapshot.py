"""ORACLE-235F: same-context RPC pool snapshot, read-only."""
import argparse
import base64
import hashlib
import json
import os
import sqlite3
import time
import urllib.request
from contextlib import closing
from pathlib import Path

ROOT = Path('runtime_state/oracle/oracle_live_execution')
REGISTRY = ROOT / 'ORACLE218_DISCOVERY.sqlite3'
REPORT = ROOT / 'ORACLE235F_CONTEXT_SNAPSHOT.json'
PUMP = 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
DLMM = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'


def evaluate(routes, accounts, slot):
    if type(slot) is not int or slot <= 0:
        raise ValueError('INVALID_CONTEXT_SLOT')
    results = []
    for mint, pump, dlmm in routes:
        reasons = []
        for addr, owner in ((pump, PUMP), (dlmm, DLMM)):
            a = accounts.get(addr)
            if a is None:
                reasons.append('MISSING_ACCOUNT')
            elif a.get('owner') != owner:
                reasons.append('OWNER_MISMATCH')
            elif not a.get('digest') or a.get('bytes', 0) == 0:
                reasons.append('EMPTY_ACCOUNT_STATE')
        results.append({'mint_prefix': mint[:12], 'slot': slot,
                        'pool_context_verified': not reasons,
                        'reason': reasons[0] if reasons else 'PASS_SAME_RPC_CONTEXT'})
    return results


def decode(addresses, response):
    if response.get('error'):
        raise ValueError('RPC_ERROR')
    body = response.get('result')
    if not isinstance(body, dict):
        raise ValueError('INVALID_RPC_RESULT')
    slot = (body.get('context') or {}).get('slot')
    values = body.get('value')
    if not isinstance(values, list) or len(values) != len(addresses):
        raise ValueError('ACCOUNT_COUNT_MISMATCH')
    accounts = {}
    for address, item in zip(addresses, values):
        if item is None:
            accounts[address] = None
            continue
        data = item.get('data')
        if not isinstance(data, list) or len(data) != 2 or data[1] != 'base64':
            raise ValueError('ACCOUNT_ENCODING_MISMATCH')
        raw = base64.b64decode(data[0], validate=True)
        accounts[address] = {'owner': item.get('owner'), 'bytes': len(raw),
                             'digest': hashlib.sha256(raw).hexdigest()}
    return slot, accounts


def rpc_snapshot(addresses, url):
    body = json.dumps({'jsonrpc': '2.0', 'id': 235, 'method': 'getMultipleAccounts',
                       'params': [addresses, {'encoding': 'base64',
                                              'commitment': 'confirmed'}]}).encode()
    request = urllib.request.Request(url, data=body,
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=25) as response:
        return decode(addresses, json.load(response))


def run():
    if os.environ.get('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise RuntimeError('HOLD_ARMED_ENVIRONMENT')
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('HOLD_PRIVATE_KEY_PRESENT')
    url = os.environ.get('SOLANA_RPC_URL', '')
    if not url.startswith('https://'):
        raise RuntimeError('HOLD_RPC_URL_MISSING')
    if not REGISTRY.is_file():
        raise RuntimeError('HOLD_REGISTRY_MISSING')
    with closing(sqlite3.connect(REGISTRY.resolve().as_uri() + '?mode=ro', uri=True)) as db:
        routes = db.execute('SELECT mint,pump_pool,meteora_pool FROM universal_routes').fetchall()
    addresses = sorted({a for _, p, d in routes for a in (p, d)})
    if not routes or len(addresses) > 100:
        raise RuntimeError('HOLD_ROUTE_COUNT_UNSUPPORTED')
    slot, accounts = rpc_snapshot(addresses, url)
    results = evaluate(routes, accounts, slot)
    passed = sum(row['pool_context_verified'] for row in results)
    report = {'build': 'ORACLE235F', 'rpc_context_slot': slot,
              'observed_at_epoch': time.time(), 'routes': len(routes),
              'unique_accounts': len(addresses), 'pool_context_pass': passed,
              'hydrated_bin_arrays_verified': False,
              'ws_to_quote_reconciled': False, 'mriya_certified': False,
              'profit_certified': False, 'signing': False, 'broadcast': False,
              'status': 'HOLD_BIN_ARRAY_HYDRATION_AND_WS_QUOTE_LINEAGE',
              'route_results': results}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('[ORACLE235F_RESULT]', json.dumps({k: v for k, v in report.items()
                                            if k != 'route_results'}, sort_keys=True))
    for row in results:
        if not row['pool_context_verified']:
            print('[ORACLE235F_HOLD]', row['mint_prefix'], row['reason'])
    print('[REPORT]', REPORT)


def test():
    routes = [('mint', 'pump', 'dlmm')]
    addresses = ['pump', 'dlmm']
    response = {'result': {'context': {'slot': 42}, 'value': [
        {'owner': PUMP, 'data': ['AQID', 'base64']},
        {'owner': DLMM, 'data': ['BAUG', 'base64']}]}}
    slot, items = decode(addresses, response)
    assert evaluate(routes, items, slot)[0]['pool_context_verified']
    items['dlmm']['owner'] = PUMP
    assert evaluate(routes, items, slot)[0]['reason'] == 'OWNER_MISMATCH'
    assert evaluate(routes, {}, slot)[0]['reason'] == 'MISSING_ACCOUNT'
    print('[ORACLE235F_TEST_PASS] shared_context=TRUE owner_guard=TRUE missing_guard=TRUE')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.test:
        test()
    if args.run:
        run()