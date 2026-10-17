from __future__ import annotations

import argparse
import asyncio
import ast
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

MODULE = 'oracle_518_ws_account_lineage_probe'
BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = BASE / (MODULE + '.py')
STAGE = Path('runtime_state/oracle/final_boss_dual/staged_discovery.json')
ROOT = Path('runtime_state/oracle/oracle_live_execution/oracle_518')
REPORT = ROOT / 'ws_lineage_report.json'
SCANNER = BASE / 'boss_scanner_live.py'
ALPHABET = re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')


class Hold(RuntimeError):
    pass


def read(path):
    path = Path(path)
    if not path.is_file():
        raise Hold('REQUIRED_SOURCE_MISSING_' + path.name)
    result = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(result, dict):
        raise Hold('SOURCE_NOT_OBJECT')
    return result


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    try:
        temp.write_text(json.dumps(value, sort_keys=True, indent=2), encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def selected_stage(max_pairs, max_stage_age):
    state = read(STAGE)
    created = state.get('generated_at')
    if not isinstance(created, (int, float)):
        raise Hold('STAGE_TIMESTAMP_MISSING')
    age = time.time() - created
    if not (0 <= age <= max_stage_age):
        raise Hold('STAGE_NOT_CURRENT_RECHECK_ADMISSION')
    rows = state.get('rows')
    if not isinstance(rows, list) or not rows or len(rows) > 28:
        raise Hold('STAGE_NOT_BOUNDED_TO_28')
    answer, seen = [], set()
    for row in rows[:max_pairs]:
        if not isinstance(row, dict):
            raise Hold('BAD_STAGE_ROW')
        token, pool = row.get('token'), row.get('pump_pool')
        if not (isinstance(token, str) and ALPHABET.fullmatch(token)):
            raise Hold('BAD_STAGE_TOKEN')
        if not (isinstance(pool, str) and ALPHABET.fullmatch(pool)):
            raise Hold('BAD_STAGE_PUMP_POOL')
        if token in seen:
            raise Hold('DUPLICATE_STAGE_TOKEN')
        seen.add(token)
        answer.append({'token': token, 'pump_pool': pool})
    return answer, int(age), fingerprint(STAGE)


def parse_message(raw, outstanding, sub_to_token, observed):
    data = json.loads(raw)
    if not isinstance(data, dict):
        return
    rid = data.get('id')
    if rid is not None and str(rid) in outstanding:
        name = outstanding.pop(str(rid))
        if isinstance(data.get('result'), int):
            sub_to_token[data['result']] = name
            observed['ack'][name] = True
        else:
            observed['reject'][name] = str(
                (data.get('error') or {}).get('code', 'INVALID_RESULT')
            )[:20]
        return
    method = data.get('method')
    params = data.get('params') or {}
    if method == 'accountNotification' and isinstance(params, dict):
        name = sub_to_token.get(params.get('subscription'))
        if name and name != '__slot__':
            observed['updates'][name] = observed['updates'].get(name, 0) + 1
    elif method == 'slotNotification' and isinstance(params, dict):
        if sub_to_token.get(params.get('subscription')) == '__slot__':
            observed['slot_events'] += 1


async def perform_probe(ws_url, rows, seconds, ack_seconds):
    try:
        import websockets
    except ImportError:
        raise Hold('DEPENDENCY_WEBSOCKETS_MISSING') from None
    outstanding = {}
    sub_to_token = {}
    observed = {'ack': {}, 'reject': {}, 'updates': {}, 'slot_events': 0}
    pool_by_token = {r['token']: r['pump_pool'] for r in rows}
    # One independent diagnostic connection. Never share or alter scanner subscriptions.
    async with websockets.connect(
        ws_url, open_timeout=12, ping_interval=20, max_size=2000000
    ) as socket:
        next_id = 1
        for token, pool in pool_by_token.items():
            outstanding[str(next_id)] = token
            await socket.send(json.dumps({
                'jsonrpc': '2.0', 'id': next_id, 'method': 'accountSubscribe',
                'params': [pool, {'encoding': 'base64', 'commitment': 'processed'}]
            }))
            next_id += 1
        outstanding[str(next_id)] = '__slot__'
        await socket.send(json.dumps({
            'jsonrpc': '2.0', 'id': next_id, 'method': 'slotSubscribe', 'params': []
        }))
        start = time.monotonic()
        deadline = start + ack_seconds + seconds
        ack_deadline = start + ack_seconds
        while time.monotonic() < deadline:
            now = time.monotonic()
            if outstanding and now < ack_deadline:
                remaining = min(1.0, deadline - now)
            else:
                remaining = min(2.0, deadline - now)
            try:
                raw = await asyncio.wait_for(socket.recv(), timeout=max(0.01, remaining))
            except asyncio.TimeoutError:
                continue
            parse_message(raw, outstanding, sub_to_token, observed)
            # Observation period begins only after the full ACK window elapsed.
        return observed, outstanding


def build_report(rows, age, stage_hash, observed, outstanding, seconds, scanner_hash):
    slot_ack = observed['ack'].get('__slot__', False)
    pool_acks = sum(bool(observed['ack'].get(x['token'])) for x in rows)
    updated = sum(observed['updates'].get(x['token'], 0) > 0 for x in rows)
    rejected = len([t for t in observed['reject'] if t != '__slot__'])
    pending = len([v for v in outstanding.values() if v != '__slot__'])
    # Pump pool state can remain unchanged while its vaults trade. Do not label
    # zero pump-pool notifications as zero market activity or a scanner fault.
    if pool_acks == len(rows) and slot_ack and observed['slot_events'] > 0:
        status = 'PASS_INDEPENDENT_WS_ACK_AND_SLOT_FEED'
    elif rejected:
        status = 'HOLD_WS_SUBSCRIPTION_REJECTED'
    else:
        status = 'HOLD_INDEPENDENT_WS_ACK_OR_SLOT_FEED_UNPROVEN'
    return {
        'revision': 'ORACLE_518', 'status': status,
        'source': 'CURRENT_STAGED_PUMP_POOL_ACCOUNTS_ONLY',
        'not_scanner_ws_ack': True,
        'not_meteora_or_vault_subscription_coverage': True,
        'not_live_quote_coverage': True,
        'stage_age_seconds_at_start': age,
        'stage_sha256': stage_hash,
        'scanner_sha256': scanner_hash,
        'requested_pump_pool_accounts': len(rows),
        'account_subscription_acks': pool_acks,
        'account_subscription_rejections': rejected,
        'account_subscription_unanswered': pending,
        'account_tokens_with_notifications': updated,
        'slot_subscription_ack': slot_ack,
        'slot_notifications': observed['slot_events'],
        'observation_seconds_after_ack_window': seconds,
        'pairs': [
            {'token': r['token'], 'pump_pool': r['pump_pool'],
             'ack': bool(observed['ack'].get(r['token'])),
             'reject_code': observed['reject'].get(r['token']),
             'notifications': observed['updates'].get(r['token'], 0)}
            for r in rows
        ],
        'historical_recovery_modified': False,
        'scanner_modified': False,
        'execution_authority': False,
        'signing': False,
        'broadcast': False,
        'fixed_first_trade_size': False,
        'production_28_pair_certified': False,
    }


def run(args):
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise Hold('PRIVATE_KEY_MUST_NOT_BE_IN_CHILD')
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise Hold('EXECUTION_MUST_BE_DISARMED')
    url = os.getenv('SOLANA_WS_URL', '')
    if not url.startswith('wss://'):
        raise Hold('WSS_URL_REQUIRED')
    if not SCANNER.is_file():
        raise Hold('FROZEN_SCANNER_NOT_FOUND')
    rows, age, stage_hash = selected_stage(args.max_pairs, args.max_stage_age)
    scanner_hash = fingerprint(SCANNER)
    print('[ORACLE518_SOURCE]', json.dumps({
        'staged_pump_pools': len(rows), 'stage_age_seconds': age,
        'account_type': 'PUMP_POOL_ONLY', 'scanner_modified': False
    }), flush=True)
    try:
        observed, outstanding = asyncio.run(perform_probe(
            url, rows, args.seconds, args.ack_seconds))
    except Hold:
        raise
    except Exception as exc:
        # Exception messages can contain URLs with private Helius keys. Never print them.
        raise Hold('WS_TRANSPORT_' + type(exc).__name__) from None
    if fingerprint(SCANNER) != scanner_hash or fingerprint(STAGE) != stage_hash:
        raise Hold('PROTECTED_SCANNER_OR_STAGE_CHANGED_DURING_PROBE')
    report = build_report(rows, age, stage_hash, observed, outstanding,
                          args.seconds, scanner_hash)
    atomic(REPORT, report)
    summary = {k: v for k, v in report.items() if k != 'pairs'}
    print('[ORACLE518_FINAL]', json.dumps(summary, sort_keys=True), flush=True)
    return 0 if report['status'].startswith('PASS_') else 2


def tests():
    t1, t2, p1 = 'T' * 32, 'U' * 32, 'P' * 32
    rows = [{'token': t1, 'pump_pool': p1}, {'token': t2, 'pump_pool': 'Q'*32}]
    pending = {'1': t1, '2': t2, '3': '__slot__'}
    links = {}
    seen = {'ack': {}, 'reject': {}, 'updates': {}, 'slot_events': 0}
    parse_message(json.dumps({'id': 1, 'result': 91}), pending, links, seen)
    parse_message(json.dumps({'id': 2, 'result': 92}), pending, links, seen)
    parse_message(json.dumps({'id': 3, 'result': 93}), pending, links, seen)
    parse_message(json.dumps({'method': 'slotNotification', 'params': {'subscription': 93}}),
                  pending, links, seen)
    parse_message(json.dumps({'method': 'accountNotification', 'params': {'subscription': 91}}),
                  pending, links, seen)
    r = build_report(rows, 4, 's', seen, pending, 10, 'c')
    assert r['status'] == 'PASS_INDEPENDENT_WS_ACK_AND_SLOT_FEED'
    assert r['account_subscription_acks'] == 2 and r['account_tokens_with_notifications'] == 1
    assert r['slot_notifications'] == 1 and not r['not_scanner_ws_ack'] is False
    parse_message(json.dumps({'method': 'accountNotification', 'params': {'subscription': 200}}),
                  pending, links, seen)
    assert seen['updates'][t1] == 1
    with __import__('tempfile').TemporaryDirectory() as d:
        path = Path(d)/'test.json'
        atomic(path, {'revision': 'OK'})
        assert read(path)['revision'] == 'OK'
    print('[PASS] ORACLE518 ack_correlation slot_feed notification_accounting '
          'no_fake_scanner_ack frozen_scanner no_signing', flush=True)


def install():
    if not BASE.is_dir() or not SCANNER.is_file():
        raise Hold('REPOSITORY_AND_FROZEN_SCANNER_REQUIRED')
    source = Path(__file__).read_text(encoding='utf-8')
    ast.parse(source)
    target_tmp = TARGET.with_name(TARGET.name + '.' + str(os.getpid()) + '.tmp')
    try:
        target_tmp.write_text(source, encoding='utf-8')
        os.replace(target_tmp, TARGET)
    finally:
        target_tmp.unlink(missing_ok=True)
    print('[PASS] ORACLE518_FULL_INSTALL read_only_ws_probe scanner_frozen', flush=True)
    print('[INSTALLED]', TARGET, flush=True)


def main():
    ap = argparse.ArgumentParser()
    modes = ap.add_mutually_exclusive_group(required=True)
    modes.add_argument('--install', action='store_true')
    modes.add_argument('--test', action='store_true')
    modes.add_argument('--probe', action='store_true')
    modes.add_argument('--status', action='store_true')
    ap.add_argument('--seconds', type=int, default=45)
    ap.add_argument('--ack-seconds', type=int, default=15)
    ap.add_argument('--max-pairs', type=int, default=28)
    ap.add_argument('--max-stage-age', type=int, default=7200)
    args = ap.parse_args()
    if args.install:
        install(); return 0
    if args.test:
        tests(); return 0
    if args.status:
        data = read(REPORT)
        print('[ORACLE518_STATUS]', json.dumps({
            k: v for k,v in data.items() if k != 'pairs'
        }, sort_keys=True), flush=True)
        return 0
    if not (10 <= args.seconds <= 180 and 3 <= args.ack_seconds <= 40
            and 1 <= args.max_pairs <= 28 and 60 <= args.max_stage_age <= 86400):
        ap.error('INVALID_MANUAL_BOUNDS')
    try:
        return run(args)
    except Hold as exc:
        print('[ORACLE518_HOLD]', str(exc), flush=True)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
