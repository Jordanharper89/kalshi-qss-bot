from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import sys
import time
import urllib.error
from pathlib import Path

BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = BASE / 'oracle_517_bounded_28_slot_admission.py'
ROOT = Path('runtime_state/oracle/oracle_live_execution/oracle_517')
REPORT = ROOT / 'capacity_trial.json'
SCANNER = BASE / 'boss_scanner_live.py'
STAGE = Path('runtime_state/oracle/final_boss_dual/staged_discovery.json')
SCANNER_LOCK = Path('runtime_state/oracle/final_boss_dual/scanner.lock')


class Hold(RuntimeError):
    pass


def read(path):
    path = Path(path)
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise Hold('STATE_NOT_OBJECT')
    return data


def atomic(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    try:
        temp.write_text(json.dumps(value, sort_keys=True, indent=2), encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compact_current_batch(original_merger, old, added, cap=28):
    """Reject un-rewarmed historical stage rows; keep verified current warm rows."""
    if not isinstance(old, list) or not isinstance(added, list):
        raise Hold('INVALID_ADMISSION_ROWS')
    if not (1 <= cap <= 28):
        raise Hold('INVALID_SLOT_CAP')
    unique = {}
    for row in added:
        if not isinstance(row, dict):
            raise Hold('INVALID_WARM_ROW')
        token, pool = row.get('token'), row.get('pump_pool')
        if not isinstance(token, str) or not (32 <= len(token) <= 44):
            raise Hold('INVALID_WARM_TOKEN')
        if not isinstance(pool, str) or not pool:
            raise Hold('INVALID_WARM_POOL')
        previous = unique.get(token)
        if previous is not None and previous['pump_pool'] != pool:
            raise Hold('CONFLICTING_PUMP_POOL')
        unique[token] = row
    if not unique:
        raise Hold('HOLD_NO_WARM_ROWS_FOR_STAGE')
    if len(unique) > cap:
        raise Hold('HOLD_CAP_EXCEEDED_BEFORE_STAGE')
    # Reuse ORACLE-511's proven merger, with no stale staged row carried in.
    merged = original_merger([], list(unique.values()))
    if not isinstance(merged, list):
        raise Hold('INVALID_511_MERGE_RESULT')
    seen = set()
    for row in merged:
        if not isinstance(row, dict):
            raise Hold('INVALID_511_MERGED_ROW')
        token = row.get('token')
        if token in seen or token not in unique:
            raise Hold('UNWARMED_OR_DUPLICATED_STAGE_ROW')
        if row.get('pump_pool') != unique[token]['pump_pool']:
            raise Hold('POOL_IDENTITY_CHANGED_IN_STAGE')
        seen.add(token)
    if seen != set(unique) or len(merged) > cap:
        raise Hold('MERGER_DROPPED_OR_EXCEEDED_WARM_ROWS')
    return merged


def http_429(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return int(exc.code) == 429
    # 509/510 wrap RPC limits as a typed Hold with this explicit code.
    return 'HTTP_429' in str(exc) if isinstance(exc, RuntimeError) else False


def pacing_wrapper(original_warm, min_spacing, max_retries, retry_backoff, telemetry):
    next_start = [0.0]

    def wrapped(row):
        for attempt in range(max_retries + 1):
            delay = next_start[0] - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            next_start[0] = time.monotonic() + min_spacing
            try:
                return original_warm(row)
            except Exception as exc:
                if not http_429(exc):
                    raise
                telemetry['http_429_seen'] += 1
                if attempt == max_retries:
                    telemetry['http_429_exhausted'] += 1
                    raise Hold('WARM_HTTP_429_RETRY_EXHAUSTED') from None
                telemetry['http_429_retries'] += 1
                # Sleep in this bounded warm path only; independent fast worker continues.
                wait = min(30.0, retry_backoff * (2 ** attempt))
                time.sleep(wait)
    return wrapped


def summarise(report, epochs, telemetry, cap):
    if not epochs:
        raise Hold('NO_SUPERVISED_EPOCH_REPORTS')
    rows = []
    for e in epochs:
        visible = int(e.get('visible_in_first_28') or 0)
        warm = int(e.get('warm_pass') or 0)
        staged = int(e.get('staged_rows') or 0)
        quoted = int(e.get('matched_all_quotes') or 0)
        fresh = int(e.get('matched_fresh_quotes') or 0)
        if not (0 <= quoted <= visible <= staged <= cap and 0 <= staged <= warm):
            raise Hold('OCCUPANCY_OR_QUOTE_DENOMINATOR_INVALID')
        rows.append({
            'epoch': e.get('epoch'), 'warm_pass': warm, 'stage_occupied': staged,
            'visible_current_batch': visible, 'observed_distinct_quotes': quoted,
            'observed_fresh_quotes': fresh,
            'observed_quote_coverage_percent': round(100 * quoted / visible, 2) if visible else 0,
            'warm_holds': e.get('warm_holds', []),
            'scanner_status': e.get('scanner_status'),
        })
    confirmed = (
        report.get('status') == 'PASS_SUPERVISED_LIVE_REPLENISHMENT_TRIAL'
        and len(rows) == int(report.get('epochs_pass', -1))
        and all(r['stage_occupied'] <= cap and r['observed_fresh_quotes'] > 0 for r in rows)
    )
    return {
        'status': 'PASS_BOUNDED_28_SLOT_COMPACTION_TRIAL' if confirmed else 'HOLD_28_SLOT_COMPACTION_UNPROVEN',
        'epochs': rows, 'slot_cap': cap,
        'max_observed_distinct_quotes': max(r['observed_distinct_quotes'] for r in rows),
        'max_staged': max(r['stage_occupied'] for r in rows),
        'observed_quote_coverage_is_not_subscription_ack': True,
        'rpc_warm_telemetry': telemetry,
        'production_28_pair_certified': False,
        'independent_ws_ack_certified': False,
        'historical_completion_required': False,
        'size_optimizer_modified': False,
        'fixed_first_trade_size': False,
        'execution_authority': False, 'signing': False, 'broadcast': False,
        'scanner_modified': False, 'q508_modified': False,
    }


def check_environment():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise Hold('PRIVATE_KEY_NOT_ALLOWED_IN_TRIAL_ENV')
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise Hold('EXECUTION_MUST_BE_DISARMED')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise Hold('RPC_URL_REQUIRED')
    if not os.getenv('SOLANA_WS_URL', '').startswith('wss://'):
        raise Hold('WS_URL_REQUIRED')


def run(args):
    check_environment()
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_508_mriya_coverage as q508,
        oracle_510_warm_pair_preflight as q510,
        oracle_511_dynamic_admission as q511,
        oracle_514_independent_recovery as q514,
        oracle_515_priority_admission as q515,
        oracle_516_supervised_replenishment as q516,
    )
    if q516.LOCK.exists() or q514.LOCK.exists() or SCANNER_LOCK.exists():
        raise Hold('OTHER_CONTROLLER_OR_SCANNER_ACTIVE')
    if read(q516.REPORT).get('status') != 'PASS_SUPERVISED_LIVE_REPLENISHMENT_TRIAL':
        raise Hold('ORACLE516_BASELINE_REQUIRED')
    if not SCANNER.is_file() or not Path(q508.TOKENS).is_file():
        raise Hold('PROTECTED_FILES_MISSING')
    original_511_merger = q511.merger
    original_510_warm = q510.warm_one
    before = (digest(SCANNER), digest(q508.TOKENS))
    telemetry = {'http_429_seen': 0, 'http_429_retries': 0, 'http_429_exhausted': 0}
    # Scoped substitutions. No code or scanner file is changed, and both callables
    # are restored even on trial failure.
    try:
        q511.merger = lambda old, added: compact_current_batch(
            original_511_merger, old, added, args.slot_cap)
        q510.warm_one = pacing_wrapper(
            original_510_warm, args.warm_spacing,
            args.warm_429_retries, args.warm_429_backoff, telemetry)
        code = q516.supervisor(args)
    finally:
        q511.merger = original_511_merger
        q510.warm_one = original_510_warm
    if (digest(SCANNER), digest(q508.TOKENS)) != before:
        raise Hold('PROTECTED_FILE_DIGEST_CHANGED')
    report = read(q516.REPORT)
    epochs = [read(q516.ROOT / ('epoch_%02d.json' % i))
              for i in range(1, args.epochs + 1)]
    outcome = summarise(report, epochs, telemetry, args.slot_cap)
    if code:
        outcome['status'] = 'HOLD_SUPERVISOR_EXIT_NONZERO'
    atomic(REPORT, outcome)
    print('[ORACLE517_FINAL]', json.dumps(outcome, sort_keys=True), flush=True)
    return 0 if outcome['status'].startswith('PASS_') else 2


def tests():
    def fixture_merger(old, added):
        return old + added
    t = 'T' * 32
    p = 'P' * 32
    old = [{'token': 'O' * 32, 'pump_pool': 'X' * 32}]
    added = [{'token': t, 'pump_pool': p}]
    assert compact_current_batch(fixture_merger, old, added) == added
    assert len(compact_current_batch(fixture_merger, old, added * 2)) == 1
    try:
        compact_current_batch(fixture_merger, old, [
            added[0], {'token': t, 'pump_pool': 'Z' * 32}])
        raise AssertionError('IDENTITY_CONFLICT_ALLOWED')
    except Hold as exc:
        assert str(exc) == 'CONFLICTING_PUMP_POOL'
    assert http_429(urllib.error.HTTPError('https://redacted.invalid',429,'',{},None))
    calls, telemetry = [0], {'http_429_seen': 0, 'http_429_retries': 0,
                             'http_429_exhausted': 0}
    def once(row):
        calls[0] += 1
        if calls[0] == 1:
            raise urllib.error.HTTPError('https://redacted.invalid',429,'',{},None)
        return {'directions': ['PUMP_TO_METEORA', 'METEORA_TO_PUMP']}
    assert pacing_wrapper(once, 0, 1, 0, telemetry)({})['directions']
    assert telemetry['http_429_retries'] == 1 and telemetry['http_429_seen'] == 1
    fixture = {'status':'PASS_SUPERVISED_LIVE_REPLENISHMENT_TRIAL', 'epochs_pass': 1}
    row = {'epoch':1,'visible_in_first_28':21,'staged_rows':21,'warm_pass':21,
           'matched_all_quotes':5,'matched_fresh_quotes':4}
    assert summarise(fixture,[row],telemetry,28)['status'].startswith('PASS_')
    bad = dict(row, staged_rows=35)
    try:
        summarise(fixture,[bad],telemetry,28)
        raise AssertionError('OVER_CAP_ALLOWED')
    except Hold as exc:
        assert str(exc) == 'OCCUPANCY_OR_QUOTE_DENOMINATOR_INVALID'
    src = Path(__file__).read_text(encoding='utf-8')
    protected = src.split('def tests():')[0]
    assert 'send' + 'Transaction' not in protected
    assert 'sign' + '_transaction' not in protected
    assert 'QSB_SOLANA_PRIVATE_KEY' in protected
    print('[PASS] ORACLE517 frozen_scanner 28_slot_current_warm_only '
          '429_retry_bounded independent_fast_worker no_signing no_broadcast', flush=True)


def install():
    if not TARGET.parent.is_dir() or not SCANNER.is_file():
        raise Hold('FROZEN_SCANNER_REPOSITORY_MISSING')
    data = Path(__file__).read_text(encoding='utf-8')
    ast.parse(data)
    temp = TARGET.with_name(TARGET.name + '.' + str(os.getpid()) + '.tmp')
    try:
        temp.write_text(data, encoding='utf-8')
        os.replace(temp, TARGET)
    finally:
        temp.unlink(missing_ok=True)
    print('[PASS] ORACLE517_FULL_INSTALL staged_selection_compaction '
          '429_warm_pacing scanner_frozen execution_disabled', flush=True)
    print('[INSTALLED]', TARGET, flush=True)


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    for name in ('--install', '--test', '--trial', '--status'):
        mode.add_argument(name, action='store_true')
    ap.add_argument('--epochs', type=int, default=2)
    ap.add_argument('--seconds', type=int, default=90)
    ap.add_argument('--slot-cap', type=int, default=28)
    ap.add_argument('--warm-limit', type=int, default=28)
    ap.add_argument('--qualify-limit', type=int, default=56)
    ap.add_argument('--fast-limit', type=int, default=32)
    ap.add_argument('--fast-interval', type=float, default=6.0)
    ap.add_argument('--heartbeat', type=float, default=12.0)
    ap.add_argument('--warm-spacing', type=float, default=0.8)
    ap.add_argument('--warm-429-retries', type=int, default=1)
    ap.add_argument('--warm-429-backoff', type=float, default=6.0)
    ap.add_argument('--with-recovery', action='store_true')
    ap.add_argument('--recovery-batch', type=int, default=8)
    ap.add_argument('--recovery-interval', type=float, default=45.0)
    ap.add_argument('--recovery-pages', type=int, default=12)
    ap.add_argument('--recovery-page-size', type=int, default=1000)
    args = ap.parse_args()
    if args.install:
        install()
        return 0
    if args.test:
        tests()
        return 0
    if args.status:
        print('[ORACLE517_STATUS]', json.dumps(read(REPORT), sort_keys=True), flush=True)
        return 0
    if not (1 <= args.epochs <= 4 and 60 <= args.seconds <= 110 and
            1 <= args.slot_cap <= 28 and 1 <= args.warm_limit <= args.slot_cap and
            1 <= args.qualify_limit <= 100 and 1 <= args.fast_limit <= 256 and
            1 <= args.fast_interval <= 60 and 4 <= args.heartbeat <= 30 and
            0 <= args.warm_spacing <= 10 and 0 <= args.warm_429_retries <= 3 and
            0 <= args.warm_429_backoff <= 30):
        ap.error('INVALID_MANUAL_BOUNDS')
    try:
        return run(args)
    except Exception as exc:
        reason = str(exc) if isinstance(exc, Hold) else type(exc).__name__
        outcome = {'status':'HOLD_28_SLOT_TRIAL', 'reason':reason,
                   'execution_authority':False, 'signing':False, 'broadcast':False}
        atomic(REPORT, outcome)
        print('[ORACLE517_HOLD]', reason, flush=True)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
