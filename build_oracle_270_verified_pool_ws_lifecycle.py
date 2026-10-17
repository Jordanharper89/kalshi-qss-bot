"""ORACLE-270 verified Solana pool-account WebSocket lifecycle; no orders/RPC polling."""
import argparse
import base64
import hashlib
import json
import os
import socket
import tempfile
import time
from collections import Counter
from pathlib import Path

import build_oracle_269_persistent_token_lifecycle as lifecycle

BASE = Path('runtime_state/oracle/oracle_live_execution')
REPORT = BASE / 'ORACLE270_WS_POOL_LIFECYCLE.json'
INPUTS = (BASE / 'ORACLE268_CANONICAL_RAW.json', BASE / 'ORACLE258_ROTATION_RAW.json')
B58 = set('123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz')


def valid_address(v):
    return isinstance(v, str) and 32 <= len(v) <= 44 and all(c in B58 for c in v)


def inventory(paths, allowed):
    """Use pool account addresses from canonical sampler, never token-mint subscriptions."""
    by_address = {}
    for p in paths:
        if not p.is_file():
            continue
        data = json.loads(p.read_text(encoding='utf-8'))
        if data.get('build') != 'ORACLE241' or any(data.get(k) is not False for k in ('signing', 'broadcast', 'execution_admission')):
            raise RuntimeError('UNTRUSTED_CANONICAL_SOURCE')
        for row in data.get('observations', []):
            if not isinstance(row, dict) or row.get('mint') not in allowed:
                continue
            mint = row['mint']
            if not valid_address(mint):
                continue
            for key, source in (('pump_pool', 'PUMPSWAP_WS'), ('meteora_pool', 'METEORA_WS')):
                address = row.get(key)
                if valid_address(address):
                    by_address.setdefault(address, set()).add((mint, source))
    return {k: sorted(v) for k, v in sorted(by_address.items())}


def decode_notification(packet, subscriptions, addresses):
    """Return only account notifications with a previously acknowledged subscription."""
    if not isinstance(packet, dict) or packet.get('method') != 'accountNotification':
        return []
    params = packet.get('params')
    if not isinstance(params, dict) or type(params.get('subscription')) is not int:
        return []
    address = subscriptions.get(params['subscription'])
    if address is None or address not in addresses:
        return []
    result = params.get('result')
    if not isinstance(result, dict):
        return []
    context, value = result.get('context'), result.get('value')
    if not isinstance(context, dict) or type(context.get('slot')) is not int or context['slot'] <= 0:
        return []
    if not isinstance(value, dict):
        return []
    encoded = value.get('data')
    if not isinstance(encoded, list) or len(encoded) != 2 or encoded[1] != 'base64' or not isinstance(encoded[0], str):
        return []
    try:
        raw = base64.b64decode(encoded[0], validate=True)
    except (ValueError, TypeError):
        return []
    if not raw or len(raw) > 300000:
        return []
    fp = hashlib.sha256(raw).hexdigest()
    return [dict(mint=mint, source=source, slot=context['slot'], pool_fingerprint=fp,
                 verified_ws_account_update=True) for mint, source in addresses[address]]


def test():
    mint = 'A'*32
    addr = 'B'*32
    with tempfile.TemporaryDirectory() as d:
        p = Path(d)/'sample.json'
        row = dict(mint=mint, pump_pool=addr, meteora_pool='C'*32)
        p.write_text(json.dumps(dict(build='ORACLE241', signing=False, broadcast=False, execution_admission=False,
                                     observations=[row])), encoding='utf-8')
        inv = inventory((p,), {mint})
        assert len(inv) == 2 and inv[addr] == [(mint, 'PUMPSWAP_WS')]
        raw = base64.b64encode(b'pool-data').decode()
        notification = dict(method='accountNotification', params=dict(subscription=44,
                            result=dict(context=dict(slot=12345), value=dict(data=[raw, 'base64']))))
        assert not decode_notification(notification, {}, inv)
        events = decode_notification(notification, {44:addr}, inv)
        assert len(events) == 1 and events[0]['pool_fingerprint'] == hashlib.sha256(b'pool-data').hexdigest()
        db = lifecycle.new_db()
        assert lifecycle.market_event(db, events[0]) == 'HOT_NEW_VERIFIED_STATE'
        assert lifecycle.market_event(db, events[0]) == 'NO_NEW_STATE'
        notification['params']['result']['context']['slot'] = 12344
        assert lifecycle.market_event(db, decode_notification(notification,{44:addr},inv)[0]) == 'NO_NEW_STATE'
        assert lifecycle.market_event(db, dict(events[0], verified_ws_account_update=False)) == 'REJECT_UNVERIFIED_EVENT'
    print('[ORACLE270_TEST_PASS] canonical_pool_addresses=TRUE subscription_provenance=TRUE restart_dedup=TRUE no_execution=TRUE')


def run(seconds, maximum):
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO' or os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('DISARMED_CHILD_ENV_REQUIRED')
    url = os.getenv('SOLANA_WS_URL', '')
    if not url.startswith('wss://'):
        raise RuntimeError('SOLANA_WS_URL_WSS_REQUIRED')
    try:
        import websocket
    except ImportError as exc:
        raise RuntimeError('websocket-client package required') from exc
    db = lifecycle.load(lifecycle.DB)
    inv = inventory(INPUTS, set(db['tokens']))
    if not inv:
        raise RuntimeError('NO_CANONICAL_POOL_ADDRESSES')
    selected = dict(list(inv.items())[:maximum])
    counters = Counter()
    by_request, subscribed = {}, {}
    BASE.mkdir(parents=True, exist_ok=True)
    ws = None
    deadline = time.monotonic() + seconds
    try:
        # WebSocket accountSubscribe consumes subscriptions; it does not poll getAccountInfo.
        ws = websocket.create_connection(url, timeout=6, enable_multithread=True)
        ws.settimeout(2)
        for n, address in enumerate(selected, 1):
            by_request[n] = address
            ws.send(json.dumps({'jsonrpc':'2.0','id':n,'method':'accountSubscribe',
                                'params':[address, {'encoding':'base64','commitment':'processed'}]}))
        while time.monotonic() < deadline:
            try:
                message = ws.recv()
            except (socket.timeout, websocket.WebSocketTimeoutException):
                continue
            except websocket.WebSocketConnectionClosedException:
                counters['WS_CLOSED'] += 1
                break
            try:
                packet = json.loads(message)
            except (ValueError, TypeError):
                counters['NON_JSON'] += 1
                continue
            if not isinstance(packet, dict):
                continue
            if type(packet.get('id')) is int and packet['id'] in by_request:
                req = packet['id']
                if type(packet.get('result')) is int:
                    subscribed[packet['result']] = by_request[req]
                    counters['SUBSCRIBED'] += 1
                else:
                    counters['SUBSCRIPTION_ERROR'] += 1
                del by_request[req]
                continue
            updates = decode_notification(packet, subscribed, selected)
            if updates:
                counters['ACCOUNT_NOTIFICATIONS'] += 1
                for update in updates:
                    counters[lifecycle.market_event(db, update)] += 1
            elif packet.get('method') == 'accountNotification':
                counters['REJECTED_NOTIFICATION'] += 1
    finally:
        if ws is not None:
            try: ws.close()
            except Exception: pass
        lifecycle.save(db, lifecycle.DB)
        report = dict(build='ORACLE270', ws_account_subscriptions_requested=len(selected),
                      ws_account_subscriptions_confirmed=len(subscribed),
                      pool_addresses_available=len(inv), counters=dict(counters),
                      tiers={tier:sum(t['tier']==tier for t in db['tokens'].values()) for tier in ('HOT','ACTIVE','COLD')},
                      note='Pool-account changes are not two-venue state freshness or positive economic evidence.',
                      full_reprice_connected=False, fee_adjusted_net_certified=False, atomic_simulation_certified=False,
                      execution_admission=False, signing=False, broadcast=False)
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
        print('[ORACLE270_RESULT]', json.dumps(report, sort_keys=True), flush=True)
        print('[REPORT]', REPORT, flush=True)

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--run', action='store_true')
    p.add_argument('--seconds', type=int, default=90)
    p.add_argument('--max-accounts', type=int, default=30)
    a = p.parse_args()
    if not a.test and not a.run: p.error('Specify --test or --run')
    if a.test:test()
    if a.run:run(max(10,min(a.seconds,180)),max(1,min(a.max_accounts,64)))
