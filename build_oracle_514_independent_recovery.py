from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.error
from pathlib import Path

MODULE = 'qseries_v2.oracle_execution.solana_atomic_executor.oracle_514_independent_recovery'
TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_514_independent_recovery.py')
ROOT = Path('runtime_state/oracle/oracle_live_execution/oracle_514')
OLD = Path('runtime_state/oracle/oracle_live_execution/oracle_513')
FAST = ROOT / 'fast_checkpoint.json'
RECOVERY = ROOT / 'recovery_checkpoint.json'
FAST_TOKENS = ROOT / 'fast_tokens.json'
RECOVERY_TOKENS = ROOT / 'recovery_tokens.json'
GAPS = ROOT / 'gaps'
REGISTRY = ROOT / 'discovery_registry.json'
REPORT = ROOT / 'runtime_report.json'
LOCK = ROOT / 'controller.lock'


class Hold(RuntimeError):
    pass


def read(path, fallback=None):
    if not path.exists():
        return {} if fallback is None else fallback
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise Hold('INVALID_STATE_OBJECT')
    return value


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    try:
        tmp.write_text(json.dumps(value, sort_keys=True, indent=2), encoding='utf-8')
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def sig(row):
    value = row.get('signature') if isinstance(row, dict) else None
    if not isinstance(value, str) or not value:
        raise Hold('INVALID_SIGNATURE')
    return value


def window(rows, prior):
    keys = [sig(x) for x in rows]
    if len(keys) != len(set(keys)):
        raise Hold('DUPLICATED_LIVE_SIGNATURE')
    if prior in keys:
        return list(reversed(rows[:keys.index(prior)])), None
    if prior:
        return list(reversed(rows)), (keys[-1], prior)
    return list(reversed(rows)), None


def walk_between(fetch, upper, lower, page_size, pages):
    """Fetch newer-to-older between two known signatures, excluding both."""
    if not upper or not lower or upper == lower:
        raise Hold('INVALID_BRIDGE_ANCHORS')
    seen, collected, before = set(), [], upper
    for _ in range(pages):
        rows = fetch(before, page_size)
        if not isinstance(rows, list):
            raise Hold('INVALID_HISTORY_RESPONSE')
        for row in rows:
            s = sig(row)
            if s in seen or s == before:
                raise Hold('DUPLICATED_HISTORY_SIGNATURE')
            if s == lower:
                return collected
            seen.add(s)
            collected.append(row)
        if len(rows) < page_size:
            raise Hold('HISTORY_ANCHOR_NOT_FOUND')
        new_before = sig(rows[-1])
        if new_before == before:
            raise Hold('HISTORY_CURSOR_STALLED')
        before = new_before
    raise Hold('HISTORY_LOOKBACK_LIMIT')


def create_gap(upper, lower, source):
    if not upper or not lower or upper == lower:
        return None
    key = hashlib.sha256((upper + '|' + lower).encode()).hexdigest()[:24]
    path = GAPS / (key + '.json')
    if not path.exists():
        atomic(path, {'id': key, 'newer': upper, 'older': lower,
                      'source': source, 'created_at': time.time()})
    return key


def seed_from_513():
    if FAST.exists() or RECOVERY.exists():
        if not FAST.exists() or not RECOVERY.exists():
            raise Hold('PARTIAL_514_SEED_STATE')
        return
    old_f = read(OLD / 'fast_checkpoint.json')
    old_r = read(OLD / 'recovery_checkpoint.json')
    upper, lower = old_f.get('cursor'), old_r.get('cursor')
    if not isinstance(upper, str) or not isinstance(lower, str):
        raise Hold('VERIFIED_513_CURSORS_REQUIRED')
    if old_f.get('status') != 'FAST_CURRENT':
        raise Hold('513_FAST_CURSOR_NOT_CURRENT')
    create_gap(upper, lower, '513_BOOTSTRAP_RECONCILIATION')
    atomic(FAST, {'cursor': upper, 'status': 'SEEDED_513',
                  'bootstrap_unverified_history': True, 'gap_events': 0})
    atomic(RECOVERY, {'status': 'SEEDED_513', 'total_processed': 0})


def rpc_parts():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_508_mriya_coverage as m
    )
    return m


def collect(m, entries, destination):
    found, failed_onchain = m.fetch_tokens(m.engine._rpc, entries, sleep_s=.02)
    existing = read(destination)
    existing.update(found)
    # Any failed RPC throws before the evidence/cursor commit.
    atomic(destination, existing)
    return len(found), failed_onchain, len(existing)


def fast_tick(args):
    m = rpc_parts()
    state = read(FAST)
    old_cursor = state.get('cursor')
    rows = m.rpc_call(m.engine._rpc, 'getSignaturesForAddress',
                      [m.engine.MRIYA, {'limit': args.fast_limit, 'commitment': 'confirmed'}])
    if not isinstance(rows, list) or not rows:
        raise Hold('FAST_SIGNATURE_PAGE_MISSING')
    part, missing = window(rows, old_cursor)
    # The gap manifest must be durable BEFORE allowing the fast cursor to move.
    gap_id = create_gap(*missing, 'FAST_WINDOW_MISS') if missing else None
    n, failed, total = collect(m, part, FAST_TOKENS)
    state.update({'cursor': sig(rows[0]), 'status': 'FAST_CURRENT',
                  'last_success_unix': time.time(),
                  'last_batch_signatures': len(part), 'last_failed_onchain': failed,
                  'last_discovered_tokens': n, 'total_tokens': total,
                  'gap_events': int(state.get('gap_events', 0)) + int(bool(missing))})
    atomic(FAST, state)
    print('[ORACLE514_FAST]', json.dumps({'status': state['status'],
          'signatures': len(part), 'tokens': total, 'new_gap': gap_id,
          'gap_events': state['gap_events']}), flush=True)


def recovery_tick(args):
    m = rpc_parts()
    state = read(RECOVERY)
    files = sorted(GAPS.glob('*.json'), key=lambda p: p.stat().st_mtime)
    pending = [(p, read(p)) for p in files
               if state.get('jobs', {}).get(p.stem, {}).get('status') != 'COMPLETE']
    if not pending:
        state.update({'status': 'BRIDGES_RECONCILED', 'last_success_unix': time.time(),
                      'last_batch_signatures': 0})
        atomic(RECOVERY, state)
        print('[ORACLE514_RECOVERY]', json.dumps({'status': state['status'],
              'pending_jobs': 0, 'deep_508_history_certified': False}), flush=True)
        return
    path, job = pending[0]
    jobs = state.setdefault('jobs', {})
    progress = jobs.get(job['id'], {})
    anchor = progress.get('cursor', job['older'])
    # Fixed upper boundary, moving verified lower boundary. This is oldest-first.
    def fetch(before, limit):
        return m.rpc_call(m.engine._rpc, 'getSignaturesForAddress',
                          [m.engine.MRIYA, {'before': before, 'limit': limit,
                                            'commitment': 'confirmed'}])
    outstanding = walk_between(fetch, job['newer'], anchor,
                               args.recovery_page_size, args.recovery_pages)
    part = list(reversed(outstanding[-args.recovery_batch:]))
    n, failed, total = collect(m, part, RECOVERY_TOKENS)
    if part:
        progress['cursor'] = sig(part[-1])
    progress.update({'status': 'COMPLETE' if len(outstanding) == len(part) else 'BACKLOG',
                     'remaining_at_scan': len(outstanding) - len(part),
                     'last_success_unix': time.time(), 'processed_total':
                     int(progress.get('processed_total', 0)) + len(part)})
    jobs[job['id']] = progress
    state.update({'status': 'RECOVERY_' + progress['status'],
                  'last_success_unix': time.time(),
                  'last_batch_signatures': len(part), 'last_failed_onchain': failed,
                  'total_tokens': total, 'last_discovered_tokens': n,
                  'total_processed': int(state.get('total_processed', 0)) + len(part)})
    atomic(RECOVERY, state)
    print('[ORACLE514_RECOVERY]', json.dumps({'status': state['status'],
          'job': job['id'], 'source': job['source'], 'batch': len(part),
          'remaining_at_scan': progress['remaining_at_scan'],
          'tokens': total, 'failed_onchain': failed}), flush=True)


def env_check():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise Hold('PRIVATE_KEY_NOT_ALLOWED_IN_CHILD')
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise Hold('EXECUTION_MUST_BE_DISARMED')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise Hold('HTTPS_RPC_REQUIRED')


def error_code(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return 'HTTP_' + str(exc.code)
    if isinstance(exc, Hold):
        return str(exc)
    if isinstance(exc, RuntimeError) and str(exc).replace('_', '').isupper() and len(str(exc)) < 90:
        return str(exc)
    return type(exc).__name__


def worker(args, lane):
    env_check()
    func = fast_tick if lane == 'FAST' else recovery_tick
    path = FAST if lane == 'FAST' else RECOVERY
    interval = args.fast_interval if lane == 'FAST' else args.recovery_interval
    deadline = time.monotonic() + args.seconds
    streak = 0
    while time.monotonic() < deadline:
        try:
            func(args)
            streak = 0
        except Exception as exc:
            streak += 1
            state = read(path)
            code = error_code(exc)
            state['status'] = 'HOLD_' + code
            state['last_error_code'] = code
            state['last_error_unix'] = time.time()
            atomic(path, state)
            print('[ORACLE514_' + lane + '_HOLD]', code, flush=True)
        if time.monotonic() >= deadline:
            break
        pause = min(90., interval * (2 ** min(streak, 5)))
        time.sleep(min(pause, max(0., deadline - time.monotonic())))


def merge():
    m = rpc_parts()
    sources = {
        '508': m.read_json(m.TOKENS, {}),
        '513_FAST': read(OLD / 'fast_tokens.json'),
        '513_RECOVERY': read(OLD / 'recovery_tokens.json'),
        '514_FAST': read(FAST_TOKENS),
        '514_RECOVERY': read(RECOVERY_TOKENS),
    }
    combined = {}
    for source, entries in sources.items():
        for token in entries:
            if isinstance(token, str) and len(token) >= 32:
                combined.setdefault(token, {'token': token, 'sources': []})['sources'].append(source)
    outcome = {'revision': 'ORACLE_514', 'unique_candidates': len(combined),
               'source_counts': {k: len(v) for k, v in sources.items()},
               'candidates': combined, 'qualification_required': True,
               'scanner_admitted': False, 'execution_authority': False,
               'history_complete': False, 'created_unix': time.time()}
    atomic(REGISTRY, outcome)
    return outcome


def controller(args):
    env_check()
    ROOT.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(fd, 'w') as f:
            f.write(str(os.getpid()))
    except FileExistsError:
        raise Hold('514_CONTROLLER_LOCK_PRESENT')
    jobs = []
    started = time.time()
    deadline = time.monotonic() + args.seconds + 45
    try:
        seed_from_513()
        for lane in ('--fast-worker', '--recovery-worker'):
            cmd = [sys.executable, '-m', MODULE, lane,
                   '--seconds', str(args.seconds), '--fast-limit', str(args.fast_limit),
                   '--fast-interval', str(args.fast_interval),
                   '--recovery-batch', str(args.recovery_batch),
                   '--recovery-interval', str(args.recovery_interval),
                   '--recovery-pages', str(args.recovery_pages),
                   '--recovery-page-size', str(args.recovery_page_size)]
            jobs.append(subprocess.Popen(cmd, env=os.environ.copy()))
        while any(j.poll() is None for j in jobs):
            if time.monotonic() > deadline:
                raise Hold('WORKER_DEADLINE_OVERRUN')
            if any(j.poll() not in (None, 0) for j in jobs):
                raise Hold('WORKER_NONZERO_EXIT')
            merge()
            time.sleep(2)
        codes = [j.wait() for j in jobs]
        result = merge()
        fs, rs = read(FAST), read(RECOVERY)
        pending = sum(1 for p in GAPS.glob('*.json')
                      if rs.get('jobs', {}).get(p.stem, {}).get('status') != 'COMPLETE')
        status = ('PASS_INDEPENDENT_LANES_BOUNDED' if
                  codes == [0, 0] and
                  fs.get('last_success_unix', 0) >= started and
                  rs.get('last_success_unix', 0) >= started and
                  fs.get('status') == 'FAST_CURRENT' and
                  rs.get('status') in ('RECOVERY_BACKLOG', 'RECOVERY_COMPLETE',
                                      'BRIDGES_RECONCILED')
                  else 'HOLD_LANE_INCOMPLETE')
        report = {'status': status, 'fast_status': fs.get('status'),
                  'recovery_status': rs.get('status'), 'pending_gap_jobs': pending,
                  'initial_513_bridge_verified': any(
                      v.get('status') == 'COMPLETE' and
                      read(GAPS / (k + '.json')).get('source') == '513_BOOTSTRAP_RECONCILIATION'
                      for k, v in rs.get('jobs', {}).items()),
                  'history_508_complete': False, 'new_registry_candidates': result['unique_candidates'],
                  'scanner_modified': False, 'qualification_required': True,
                  'scanner_admitted': False, 'signing': False, 'broadcast': False,
                  'execution_authority': False, 'fixed_first_trade_size': False,
                  'size_optimizer_modified': False}
        atomic(REPORT, report)
        print('[ORACLE514_FINAL]', json.dumps(report, sort_keys=True), flush=True)
        return 0 if status.startswith('PASS_') else 2
    finally:
        for job in jobs:
            if job.poll() is None:
                job.terminate()
            try:
                job.wait(timeout=10)
            except subprocess.TimeoutExpired:
                job.kill()
                job.wait()
        LOCK.unlink(missing_ok=True)


def tests():
    rows = [{'signature': 's' + str(i)} for i in range(9, 0, -1)]
    def fetch(before, limit):
        position = next(i for i, x in enumerate(rows) if x['signature'] == before)
        return rows[position + 1:position + 1 + limit]
    assert [sig(x) for x in walk_between(fetch, 's9', 's1', 3, 3)] == [
        's8', 's7', 's6', 's5', 's4', 's3', 's2']
    assert [sig(x) for x in reversed(walk_between(fetch, 's9', 's1', 3, 3)[-2:])] == ['s2', 's3']
    assert [sig(x) for x in walk_between(fetch, 's9', 's3', 3, 3)] == [
        's8', 's7', 's6', 's5', 's4']
    out, gap = window(rows[:3], 's2')
    assert gap == ('s7', 's2') and [sig(x) for x in out] == ['s7', 's8', 's9']
    out, gap = window(rows[:5], 's7')
    assert gap is None and [sig(x) for x in out] == ['s8', 's9']
    try:
        walk_between(fetch, 's9', 'notfound', 3, 1)
    except Hold as exc:
        assert str(exc) == 'HISTORY_LOOKBACK_LIMIT'
    else:
        raise AssertionError('UNREACHABLE_ANCHOR_NOT_HELD')
    assert error_code(urllib.error.HTTPError('https://redacted', 429, 'rate limit', {}, None)) == 'HTTP_429'
    source = Path(__file__).read_text(encoding='utf-8')
    live_code = source.split('def tests():')[0]
    assert ('send' + 'Transaction') not in live_code
    assert ('sign' + '_transaction') not in live_code
    print('[PASS] ORACLE514 independent_513_seed durable_gap_before_cursor '
          'oldest_first_bridge HTTP_429 backoff failclosed no_signing', flush=True)


def install():
    scanner = TARGET.parent / 'boss_scanner_live.py'
    if not scanner.exists() or not TARGET.parent.is_dir():
        raise Hold('REPOSITORY_OR_FROZEN_SCANNER_REQUIRED')
    src = Path(__file__).read_text(encoding='utf-8')
    ast.parse(src)
    tmp = TARGET.with_name(TARGET.name + '.' + str(os.getpid()) + '.tmp')
    try:
        tmp.write_text(src, encoding='utf-8')
        os.replace(tmp, TARGET)
    finally:
        tmp.unlink(missing_ok=True)
    print('[PASS] ORACLE514_FULL_INSTALL frozen_scanner isolated_fast_recovery no_signing', flush=True)
    print('[INSTALLED]', TARGET, flush=True)


def main():
    p = argparse.ArgumentParser()
    modes = p.add_mutually_exclusive_group(required=True)
    for mode in ('--install', '--test', '--trial', '--fast-worker', '--recovery-worker', '--merge'):
        modes.add_argument(mode, action='store_true')
    p.add_argument('--seconds', type=int, default=120)
    p.add_argument('--fast-limit', type=int, default=32)
    p.add_argument('--fast-interval', type=float, default=2)
    p.add_argument('--recovery-batch', type=int, default=32)
    p.add_argument('--recovery-interval', type=float, default=12)
    p.add_argument('--recovery-pages', type=int, default=12)
    p.add_argument('--recovery-page-size', type=int, default=1000)
    args = p.parse_args()
    if args.install:
        install()
        return 0
    if args.test:
        tests()
        return 0
    if args.merge:
        print('[ORACLE514_REGISTRY]', merge()['unique_candidates'])
        return 0
    if not (15 <= args.seconds <= 3600 and 8 <= args.fast_limit <= 256 and
            .5 <= args.fast_interval <= 60 and 1 <= args.recovery_batch <= 128 and
            2 <= args.recovery_interval <= 600 and 1 <= args.recovery_pages <= 20 and
            8 <= args.recovery_page_size <= 1000):
        p.error('INVALID_RUNTIME_BOUNDS')
    if args.fast_worker:
        worker(args, 'FAST')
        return 0
    if args.recovery_worker:
        worker(args, 'RECOVERY')
        return 0
    return controller(args)


if __name__ == '__main__':
    raise SystemExit(main())
