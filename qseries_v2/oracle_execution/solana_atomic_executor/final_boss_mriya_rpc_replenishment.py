"""Final Boss Mriya wallet replenishment V5: version-1 compatible read-only RPC.

Mriya wallet activity alone is never a candidate execution authorization.
Never starts a WebSocket, touches a private key, changes scanner subscriptions,
modifies a wallet, or signs/broadcasts a transaction.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'runtime_state/oracle/final_boss_dual/mriya_live_sightings.json'
MRIYA = 'MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X'
WSOL = 'So11111111111111111111111111111111111111112'
BASE58 = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')
FRESH_SECONDS = 180
MAX_CALLS = 4
MAX_TRANSACTIONS = 3
MAX_SUPPORTED_VERSION = 1  # Confirmed by Helius: version-0 failed -32015; version-1 succeeds.

class RpcHold(RuntimeError):
    """Short sanitized code; do not print RPC error message or URL."""

class PublicRpc:
    def __init__(self, url):
        if not isinstance(url, str) or not url.startswith('https://'):
            raise RpcHold('HOLD_HTTPS_RPC_NOT_CONFIGURED')
        self._url = url
        self.calls = 0
        self.retry_after = 0
        self.method_counts = {}
        self.last_error_code = None

    def request(self, method, params):
        if method not in ('getSignaturesForAddress', 'getTransaction'):
            raise RpcHold('HOLD_RPC_METHOD_NOT_ALLOWED')
        if self.calls >= MAX_CALLS:
            raise RpcHold('HOLD_RPC_CYCLE_BUDGET_EXHAUSTED')
        body = json.dumps({'jsonrpc': '2.0', 'id': self.calls + 1,
                           'method': method, 'params': params}).encode('utf-8')
        req = urllib.request.Request(self._url, body,
                  {'Content-Type': 'application/json'}, method='POST')
        self.calls += 1
        self.method_counts[method] = self.method_counts.get(method, 0) + 1
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                raise RpcHold('HOLD_RPC_RESPONSE_TOO_LARGE')
            payload = json.loads(raw.decode('utf-8'))
            if not isinstance(payload, dict):
                raise RpcHold('HOLD_RPC_RESPONSE_NOT_OBJECT')
            err = payload.get('error')
            if err:
                code = err.get('code') if isinstance(err, dict) else None
                self.last_error_code = code if type(code) is int else None
                if code == -32015:
                    raise RpcHold('HOLD_RPC_TRANSACTION_VERSION_UNSUPPORTED')
                if code == 429 or code == -32429:
                    self.retry_after = 60
                    raise RpcHold('HOLD_RPC_RATE_LIMIT')
                raise RpcHold('HOLD_RPC_JSON_ERROR_'+str(code) if type(code) is int
                              else 'HOLD_RPC_JSON_ERROR_UNCLASSIFIED')
            if 'result' not in payload:
                raise RpcHold('HOLD_RPC_RESULT_MISSING')
            return payload['result']
        except urllib.error.HTTPError as ex:
            if ex.code == 429:
                value = ex.headers.get('Retry-After', '60') if ex.headers else '60'
                try:
                    self.retry_after = max(30, min(600, int(value)))
                except (ValueError, TypeError):
                    self.retry_after = 60
                raise RpcHold('HOLD_RPC_HTTP_429') from None
            raise RpcHold('HOLD_RPC_HTTP_'+str(ex.code)) from None
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, UnicodeError):
            raise RpcHold('HOLD_RPC_TRANSPORT_OR_FORMAT') from None

def valid_mint(value):
    return isinstance(value, str) and value != WSOL and BASE58.fullmatch(value) is not None

def transaction_mints(tx):
    """Read parsed SPL/Token-2022 balances and parsed instructions, not ALT guesses."""
    if not isinstance(tx, dict):
        return set()
    meta = tx.get('meta')
    if not isinstance(meta, dict) or meta.get('err') is not None:
        return set()
    result = set()
    for key in ('preTokenBalances', 'postTokenBalances'):
        balances = meta.get(key)
        if not isinstance(balances, list):
            continue
        for item in balances:
            if isinstance(item, dict) and valid_mint(item.get('mint')):
                result.add(item['mint'])
    message = ((tx.get('transaction') or {}).get('message') or {})
    instructions = message.get('instructions') or []
    inner = meta.get('innerInstructions') or []
    if isinstance(inner, list):
        for group in inner:
            if isinstance(group, dict) and isinstance(group.get('instructions'), list):
                instructions = list(instructions) + group['instructions']
    if isinstance(instructions, list):
        for ins in instructions:
            if not isinstance(ins, dict):
                continue
            parsed = ins.get('parsed')
            info = parsed.get('info') if isinstance(parsed, dict) else None
            program = ins.get('program')
            if program not in ('spl-token', 'spl-token-2022') or not isinstance(info, dict):
                continue
            mint = info.get('mint')
            if valid_mint(mint):
                result.add(mint)
    return result

def collect(rpc, now=None, limit_tx=MAX_TRANSACTIONS):
    now = time.time() if now is None else now
    if type(limit_tx) is not int or not 0 <= limit_tx <= MAX_TRANSACTIONS:
        raise RpcHold('HOLD_INVALID_TRANSACTION_BUDGET')
    sigs = rpc.request('getSignaturesForAddress',
        [MRIYA, {'limit': 24, 'commitment': 'confirmed'}])
    if not isinstance(sigs, list):
        raise RpcHold('HOLD_SIGNATURES_RESPONSE_INVALID')
    fresh = []
    seen = set()
    for entry in sigs:
        if not isinstance(entry, dict) or entry.get('err') is not None:
            continue
        sig = entry.get('signature')
        bt = entry.get('blockTime')
        if not isinstance(sig, str) or not 64 <= len(sig) <= 96 or sig in seen:
            continue
        if type(bt) is not int or not 0 <= now - bt <= FRESH_SECONDS:
            continue
        fresh.append(entry)
        seen.add(sig)
    observed = {}
    transactions = 0
    versions = {'legacy': 0, 'v0': 0, 'v1': 0, 'unsupported': 0, 'missing': 0}
    for entry in fresh[:limit_tx]:
        transaction = rpc.request('getTransaction',
            [entry['signature'], {'encoding': 'jsonParsed', 'commitment': 'confirmed',
                                  'maxSupportedTransactionVersion': MAX_SUPPORTED_VERSION}])
        transactions += 1
        if not isinstance(transaction, dict):
            versions['missing'] += 1
            continue
        version = transaction.get('version', 'legacy')
        if version == 'legacy': versions['legacy'] += 1
        elif type(version) is int and version == 0: versions['v0'] += 1
        elif type(version) is int and version == 1: versions['v1'] += 1
        else:
            versions['unsupported'] += 1
            continue
        bt = transaction.get('blockTime')
        slot = transaction.get('slot')
        if type(bt) is not int or not 0 <= now - bt <= FRESH_SECONDS:
            continue
        if type(slot) is not int or slot <= 0:
            continue
        for mint in transaction_mints(transaction):
            current = observed.get(mint)
            if current is None or current['block_time'] < bt:
                observed[mint] = {'token': mint, 'slot': slot, 'block_time': bt,
                    'tx_witness_sha256': hashlib.sha256(entry['signature'].encode('ascii')).hexdigest()[:20]}
    if getattr(rpc, 'calls', 0) > MAX_CALLS:
        raise RpcHold('HOLD_RPC_CALL_BUDGET_OVERRUN')
    return {
        'source': 'MRIYA_WALLET_CONFIRMED_TX', 'wallet': MRIYA,
        'build': 'FINAL_BOSS_MRIYA_RPC_V5_VERSION1',
        'updated_unix': now, 'rows': sorted(observed.values(), key=lambda x: x['token']),
        'fresh_signatures_observed': len(fresh),
        'signatures_returned': len(sigs),
        'transactions_inspected': transactions, 'transaction_versions': versions,
        'rpc_calls': rpc.calls, 'rpc_budget': MAX_CALLS,
        'rpc_methods': getattr(rpc, 'method_counts', {}),
        'rpc_max_supported_transaction_version': MAX_SUPPORTED_VERSION,
        'scanner_modified': False, 'additional_websockets': 0,
        'signing': False, 'broadcast': False, 'execution_authorized': False,
        'status': 'OBSERVED' if observed else 'NO_FRESH_WALLET_MINT_ACTIVITY',
        'note': 'Wallet activity only. Not proof of pool identity, security, profitability, or execution eligibility.'
    }

def save(payload, path=OUT):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', dir=path.parent, encoding='utf-8',
                                     delete=False, suffix='.tmp') as tmp:
        name = tmp.name
        json.dump(payload, tmp, sort_keys=True, indent=2)
    os.replace(name, path)

def tests():
    class Fake:
        def __init__(self, version=1, active=True):
            self.calls = 0
            self.method_counts = {}
            self.version = version
            self.active = active
            self.params = []
        def request(self, method, params):
            self.calls += 1
            self.method_counts[method] = self.method_counts.get(method, 0) + 1
            self.params.append((method, params))
            if method == 'getSignaturesForAddress':
                return [{'signature': 'A'*88, 'blockTime': 100 if self.active else -1000, 'err': None},
                        {'signature': 'B'*88, 'blockTime': -500, 'err': None}]
            return {'version': self.version, 'slot': 1234, 'blockTime': 100,
                'meta': {'err': None, 'postTokenBalances': [{'mint': 'C'*43}, {'mint': WSOL}]},
                'transaction': {'message': {'transactionConfig': {'computeUnitLimit': 30000},
                                                'instructions': []}}}
    v1 = Fake()
    r = collect(v1, now=110)
    assert r['transactions_inspected'] == 1 and r['transaction_versions']['v1'] == 1
    assert r['rows'][0]['token'] == 'C'*43 and r['rpc_calls'] == 2
    assert v1.params[1][1][1]['maxSupportedTransactionVersion'] == 1
    assert type(v1.params[1][1][1]['maxSupportedTransactionVersion']) is int
    assert r['signing'] is False and r['broadcast'] is False
    assert collect(Fake(version=0), now=110)['transaction_versions']['v0'] == 1
    assert collect(Fake(version='legacy'), now=110)['transaction_versions']['legacy'] == 1
    assert collect(Fake(version=2), now=110)['rows'] == []
    assert collect(Fake(active=False), now=110)['transactions_inspected'] == 0
    ins_tx = {'meta': {'err': None, 'innerInstructions': [{'instructions': [
                   {'program': 'spl-token-2022', 'parsed': {'info': {'mint': 'D'*43}}}]}]},
              'transaction': {'message': {'instructions': []}}}
    assert transaction_mints(ins_tx) == {'D'*43}
    assert transaction_mints({'meta': {'err': {'code': 7},
               'postTokenBalances': [{'mint': 'C'*43}]}}) == set()
    assert not valid_mint(WSOL) and not valid_mint('invalid-public-key')
    try: collect(Fake(), limit_tx=4)
    except RpcHold as err: assert str(err) == 'HOLD_INVALID_TRANSACTION_BUDGET'
    else: raise AssertionError('FAILED_RPC_BUDGET_TEST')
    import unittest.mock as mock
    payload_err = json.dumps({'jsonrpc': '2.0', 'error': {'code': -32015,
                             'message': 'Never display this RPC message'}}).encode()
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, n): return payload_err
    with mock.patch('urllib.request.urlopen', return_value=Response()):
        rpc = PublicRpc('https://example.invalid/rpc?api-key=never-output-this')
        try: rpc.request('getTransaction', ['A'*88, {'maxSupportedTransactionVersion': 1}])
        except RpcHold as err: assert str(err) == 'HOLD_RPC_TRANSACTION_VERSION_UNSUPPORTED'
        else: raise AssertionError('JSON_RPC_ERROR_HANDLING_FAILED')
    with tempfile.TemporaryDirectory() as directory:
        f = Path(directory)/'read_only.json'
        save(r, f)
        assert json.loads(f.read_text(encoding='utf-8'))['transaction_versions']['v1'] == 1
    print('[PASS] MRIYA_V5 version1/legacy/v0 parsing, Token2022 witnesses, freshness, max-four RPC, sanitized errors, zero wallet or scanner mutations')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--observe', action='store_true')
    parser.add_argument('--seconds', type=int, default=90)
    parser.add_argument('--interval', type=int, default=30)
    args = parser.parse_args()
    if args.test:
        tests()
        return 0
    if not (args.once or args.observe):
        parser.error('Use --test, --once, or --observe')
    if not 20 <= args.interval <= 300 or not 1 <= args.seconds <= 3600:
        parser.error('INVALID_OBSERVATION_SCHEDULE')
    url = os.environ.get('SOLANA_RPC_URL', '')
    if not url.startswith('https://'):
        print('[MRIYA_RPC_HOLD] HOLD_HTTPS_RPC_NOT_CONFIGURED', flush=True)
        return 2
    deadline = time.monotonic() + args.seconds
    while True:
        rpc = PublicRpc(url)
        try:
            report = collect(rpc)
            save(report)
            print('[MRIYA_RPC_FRESH]', json.dumps({
                k: report[k] for k in ('fresh_signatures_observed', 'transactions_inspected',
                    'transaction_versions', 'rpc_calls', 'rpc_budget', 'status')
            }, sort_keys=True), flush=True)
            print('[MRIYA_MINTS]', len(report['rows']), flush=True)
        except RpcHold as exc:
            # Do not renew stale sightings when RPC is unavailable or unsupported.
            report = {'source': 'MRIYA_WALLET_CONFIRMED_TX', 'wallet': MRIYA,
                      'build': 'FINAL_BOSS_MRIYA_RPC_V5_VERSION1',
                      'updated_unix': time.time(), 'rows': [], 'status': str(exc),
                      'rpc_calls': rpc.calls, 'rpc_budget': MAX_CALLS,
                      'rpc_error_code': rpc.last_error_code,
                      'execution_authorized': False, 'scanner_modified': False,
                      'signing': False, 'broadcast': False}
            save(report)
            print('[MRIYA_RPC_HOLD]', str(exc), flush=True)
        if args.once or time.monotonic() >= deadline:
            break
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(max(args.interval, rpc.retry_after), remaining))
    print('[REPORT]', OUT.relative_to(ROOT), flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
