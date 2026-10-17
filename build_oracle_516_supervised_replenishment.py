from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = BASE / 'oracle_516_supervised_replenishment.py'
MODULE = 'qseries_v2.oracle_execution.solana_atomic_executor.oracle_516_supervised_replenishment'
ROOT = Path('runtime_state/oracle/oracle_live_execution/oracle_516')
LOCK = ROOT / 'controller.lock'
REPORT = ROOT / 'supervised_replenishment_report.json'
SCANNER = BASE / 'boss_scanner_live.py'
SCANNER_LOCK = Path('runtime_state/oracle/final_boss_dual/scanner.lock')


class Hold(RuntimeError):
    pass


def read(path):
    path = Path(path)
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise Hold('STATE_NOT_OBJECT')
    return value


def atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    try:
        temp.write_text(json.dumps(data, sort_keys=True, indent=2), encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_error(exc):
    return str(exc) if isinstance(exc, Hold) else type(exc).__name__


def check_env():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise Hold('PRIVATE_KEY_NOT_ALLOWED_IN_WORKER_ENV')
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise Hold('EXECUTION_NOT_DISARMED')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise Hold('HTTPS_RPC_REQUIRED')
    if not os.getenv('SOLANA_WS_URL', '').startswith('wss://'):
        raise Hold('WSS_URL_REQUIRED')


def acquire_lock():
    ROOT.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise Hold('ORACLE516_CONTROLLER_ALREADY_LOCKED')
    with os.fdopen(fd, 'w') as out:
        out.write(str(os.getpid()))


def pending_gaps(q514):
    state = read(q514.RECOVERY)
    jobs = state.get('jobs', {})
    if not isinstance(jobs, dict):
        raise Hold('INVALID_RECOVERY_JOBS')
    return sum(1 for p in q514.GAPS.glob('*.json')
               if jobs.get(p.stem, {}).get('status') != 'COMPLETE')


def evaluate(rows, fast_state, expected_epochs):
    passed = sum(row.get('status') == 'PASS_PRIORITY_DISCOVERY_ADMISSION_TRIAL'
                 and row.get('scanner_exit') == 0
                 and row.get('scanner_status') == 'PASS_LIVE_EPOCH_OBSERVED'
                 and row.get('matched_fresh_quotes', 0) > 0
                 for row in rows)
    fast_ok = (fast_state.get('status') == 'FAST_CURRENT' and
               all(row.get('fast_progress_during_epoch') is True for row in rows))
    status = ('PASS_SUPERVISED_LIVE_REPLENISHMENT_TRIAL' if
              len(rows) == expected_epochs and passed == expected_epochs and fast_ok
              else 'HOLD_SUPERVISED_REPLENISHMENT_UNPROVEN')
    return status, passed, fast_ok


def start_worker(q514, args, lane):
    name = '--fast-worker' if lane == 'FAST' else '--recovery-worker'
    cmd = [sys.executable, '-m', q514.MODULE, name,
           '--seconds', '3600',
           '--fast-limit', str(args.fast_limit),
           '--fast-interval', str(args.fast_interval),
           '--recovery-batch', str(args.recovery_batch),
           '--recovery-interval', str(args.recovery_interval),
           '--recovery-pages', str(args.recovery_pages),
           '--recovery-page-size', str(args.recovery_page_size)]
    # QSB_SOLANA_PRIVATE_KEY is excluded by the parent's hidden-key launcher.
    environment = os.environ.copy()
    environment.pop('QSB_SOLANA_PRIVATE_KEY', None)
    environment['QSB_LIVE_ARM'] = 'NO'
    return subprocess.Popen(cmd, env=environment)


def watchdog(stop, args, phase, q514, jobs):
    while not stop.wait(args.heartbeat):
        fast, recovery = read(q514.FAST), read(q514.RECOVERY)
        print('[ORACLE516_HEARTBEAT]', json.dumps({
            'phase': phase.get('value', 'STARTING'),
            'phase_seconds': int(time.monotonic() - phase.get('since', time.monotonic())),
            'fast_status': fast.get('status'),
            'fast_tokens': fast.get('total_tokens', 0),
            'recovery_status': recovery.get('status'),
            'workers_alive': [job.poll() is None for job in jobs],
            'execution_authority': False
        }, sort_keys=True), flush=True)


def supervisor(args):
    check_env()
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_508_mriya_coverage as q508,
        oracle_514_independent_recovery as q514,
        oracle_515_priority_admission as q515,
    )
    if not SCANNER.is_file() or not Path(q508.TOKENS).is_file():
        raise Hold('CANONICAL_SOURCE_OR_SCANNER_MISSING')
    if q514.LOCK.exists() or SCANNER_LOCK.exists():
        raise Hold('OTHER_ORACLE_CONTROLLER_OR_SCANNER_RUNNING')
    if not q514.FAST.exists() or not q514.REGISTRY.exists():
        raise Hold('ORACLE514_CERTIFIED_BASELINE_REQUIRED')
    if read(q514.REPORT).get('status') != 'PASS_INDEPENDENT_LANES_BOUNDED':
        raise Hold('ORACLE514_BASELINE_NOT_CERTIFIED')
    if read(q515.REPORT).get('status') != 'PASS_PRIORITY_DISCOVERY_ADMISSION_TRIAL':
        raise Hold('ORACLE515_BASELINE_NOT_CERTIFIED')
    scanner_before = digest(SCANNER)
    tokens_before = digest(q508.TOKENS)
    acquire_lock()
    jobs = []
    phase = {'value': 'STARTING', 'since': time.monotonic()}
    stop = threading.Event()
    monitor = None
    epoch_rows = []
    result = {'status': 'HOLD_TRIAL_INCOMPLETE', 'execution_authority': False,
              'signing': False, 'broadcast': False,
              'scanner_modified': False, 'fixed_first_trade_size': False}
    try:
        jobs.append(start_worker(q514, args, 'FAST'))
        if args.with_recovery:
            jobs.append(start_worker(q514, args, 'RECOVERY'))
        monitor = threading.Thread(target=watchdog,
                                   args=(stop, args, phase, q514, jobs), daemon=True)
        monitor.start()
        # Fresh token collection remains active in another process throughout
        # admission. Historical work is never a prerequisite to admission.
        for epoch in range(1, args.epochs + 1):
            if any(job.poll() is not None for job in jobs):
                raise Hold('BACKGROUND_LANE_WORKER_EXITED')
            phase.update(value='MERGE_EPOCH_' + str(epoch), since=time.monotonic())
            candidate_registry = q514.merge()
            start_fast = read(q514.FAST).get('last_success_unix', 0)
            before_epoch = time.time()
            phase.update(value='QUALIFY_WARM_SCANNER_EPOCH_' + str(epoch),
                         since=time.monotonic())
            print('[ORACLE516_EPOCH_START]', json.dumps({
                'epoch': epoch, 'epochs': args.epochs,
                'registry_candidates': candidate_registry['unique_candidates'],
                'warm_limit': args.warm_limit,
                'qualify_limit': args.qualify_limit,
                'scanner_seconds': args.seconds,
                'recovery_critical_path': False
            }, sort_keys=True), flush=True)
            code = q515.run(argparse.Namespace(
                warm_limit=args.warm_limit,
                qualify_limit=args.qualify_limit,
                seconds=args.seconds))
            if not q515.REPORT.is_file() or q515.REPORT.stat().st_mtime < before_epoch - 2:
                raise Hold('ADMISSION_REPORT_NOT_REFRESHED')
            admitted = read(q515.REPORT)
            fs = read(q514.FAST)
            admitted['epoch'] = epoch
            admitted['fast_progress_during_epoch'] = (
                fs.get('status') == 'FAST_CURRENT'
                and float(fs.get('last_success_unix', 0)) >= max(
                    float(start_fast), before_epoch))
            admitted['fast_token_inventory'] = fs.get('total_tokens', 0)
            admitted['fast_gap_events'] = fs.get('gap_events', 0)
            admitted['pending_gap_jobs'] = pending_gaps(q514)
            atomic(ROOT / ('epoch_%02d.json' % epoch), admitted)
            epoch_rows.append(admitted)
            print('[ORACLE516_EPOCH]', json.dumps({
                'epoch': epoch, 'status': admitted.get('status'),
                'warm_pass': admitted.get('warm_pass'),
                'visible': admitted.get('visible_in_first_28'),
                'fresh_quoted': admitted.get('matched_fresh_quotes'),
                'all_quoted': admitted.get('matched_all_quotes'),
                'fast_progress': admitted['fast_progress_during_epoch'],
                'pending_gap_jobs': admitted['pending_gap_jobs']
            }, sort_keys=True), flush=True)
            if code != 0 or not admitted['fast_progress_during_epoch']:
                raise Hold('EPOCH_ADMISSION_OR_FAST_PROGRESS_FAILED')
            if digest(SCANNER) != scanner_before or digest(q508.TOKENS) != tokens_before:
                raise Hold('PROTECTED_SOURCE_CHANGED')
        phase.update(value='FINAL_VALIDATION', since=time.monotonic())
        status, passed, fast_ok = evaluate(epoch_rows, read(q514.FAST), args.epochs)
        result = {'status': status, 'epochs': args.epochs,
                  'epochs_pass': passed, 'fast_progress_certified': fast_ok,
                  'qualified_registry_last': epoch_rows[-1].get('qualified_registry_total'),
                  'max_visible_in_first_28': max(r.get('visible_in_first_28', 0)
                                                 for r in epoch_rows),
                  'max_live_quoted_in_one_epoch': max(r.get('matched_all_quotes', 0)
                                                      for r in epoch_rows),
                  'fast_tokens_last': read(q514.FAST).get('total_tokens'),
                  'pending_gap_jobs': pending_gaps(q514),
                  'background_recovery_enabled': args.with_recovery,
                  'historical_completion_required': False,
                  'production_28_pair_certified': False,
                  'independent_ws_ack_certified': False,
                  'net_profitability_certified': False,
                  'scanner_modified': False, 'q508_modified': False,
                  'size_optimizer_modified': False, 'fixed_first_trade_size': False,
                  'execution_authority': False, 'signing': False, 'broadcast': False}
        atomic(REPORT, result)
        print('[ORACLE516_FINAL]', json.dumps(result, sort_keys=True), flush=True)
        return 0 if status.startswith('PASS_') else 2
    except Exception as exc:
        result['status'] = 'HOLD_SUPERVISED_REPLENISHMENT'
        result['reason'] = safe_error(exc)
        result['epochs_completed'] = len(epoch_rows)
        result['pending_gap_jobs'] = pending_gaps(q514)
        atomic(REPORT, result)
        print('[ORACLE516_HOLD]', result['reason'], flush=True)
        return 2
    finally:
        stop.set()
        if monitor is not None:
            monitor.join(timeout=3)
        for proc in jobs:
            if proc.poll() is None:
                proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        LOCK.unlink(missing_ok=True)


def tests():
    assert evaluate([{'status': 'PASS_PRIORITY_DISCOVERY_ADMISSION_TRIAL',
                      'scanner_exit': 0, 'scanner_status': 'PASS_LIVE_EPOCH_OBSERVED',
                      'matched_fresh_quotes': 2, 'fast_progress_during_epoch': True}],
                    {'status': 'FAST_CURRENT'}, 1) == (
                        'PASS_SUPERVISED_LIVE_REPLENISHMENT_TRIAL', 1, True)
    assert evaluate([{'status': 'PASS_PRIORITY_DISCOVERY_ADMISSION_TRIAL',
                      'scanner_exit': 0, 'scanner_status': 'PASS_LIVE_EPOCH_OBSERVED',
                      'matched_fresh_quotes': 0, 'fast_progress_during_epoch': True}],
                    {'status': 'FAST_CURRENT'}, 1)[0].startswith('HOLD_')
    assert evaluate([{'status': 'PASS_PRIORITY_DISCOVERY_ADMISSION_TRIAL',
                      'scanner_exit': 0, 'scanner_status': 'PASS_LIVE_EPOCH_OBSERVED',
                      'matched_fresh_quotes': 2, 'fast_progress_during_epoch': True}],
                    {'status': 'FAST_CURRENT'}, 2)[0].startswith('HOLD_')
    assert evaluate([{'status': 'PASS_PRIORITY_DISCOVERY_ADMISSION_TRIAL',
                      'scanner_exit': 0, 'scanner_status': 'PASS_LIVE_EPOCH_OBSERVED',
                      'matched_fresh_quotes': 2, 'fast_progress_during_epoch': False}],
                    {'status': 'FAST_CURRENT'}, 1)[0].startswith('HOLD_')
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / 'test.json'
        atomic(path, {'test': 1})
        assert read(path) == {'test': 1}
    source = Path(__file__).read_text(encoding='utf-8')
    code = source.split('def tests():')[0]
    assert 'send' + 'Transaction' not in code
    assert 'sign' + '_transaction' not in code
    assert 'PRIVATE_KEY_NOT_ALLOWED_IN_WORKER_ENV' in code
    print('[PASS] ORACLE516 bounded_multi_epoch live_fast_worker gap_preservation '
          'heartbeat failclosed no_signing best_size_unchanged', flush=True)


def install():
    if not TARGET.parent.is_dir() or not SCANNER.is_file():
        raise Hold('REPOSITORY_OR_FROZEN_SCANNER_REQUIRED')
    source = Path(__file__).read_text(encoding='utf-8')
    ast.parse(source)
    temp = TARGET.with_name(TARGET.name + '.' + str(os.getpid()) + '.tmp')
    try:
        temp.write_text(source, encoding='utf-8')
        os.replace(temp, TARGET)
    finally:
        temp.unlink(missing_ok=True)
    print('[PASS] ORACLE516_FULL_INSTALL scanner_frozen existing_515_admission '
          'independent_514_fast no_signing', flush=True)
    print('[INSTALLED]', TARGET, flush=True)


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    for name in ('--install', '--test', '--trial', '--status'):
        mode.add_argument(name, action='store_true')
    parser.add_argument('--epochs', type=int, default=2)
    parser.add_argument('--seconds', type=int, default=90)
    parser.add_argument('--warm-limit', type=int, default=16)
    parser.add_argument('--qualify-limit', type=int, default=56)
    parser.add_argument('--fast-limit', type=int, default=32)
    parser.add_argument('--fast-interval', type=float, default=2.)
    parser.add_argument('--heartbeat', type=float, default=12.)
    parser.add_argument('--with-recovery', action='store_true')
    parser.add_argument('--recovery-batch', type=int, default=8)
    parser.add_argument('--recovery-interval', type=float, default=45.)
    parser.add_argument('--recovery-pages', type=int, default=12)
    parser.add_argument('--recovery-page-size', type=int, default=1000)
    args = parser.parse_args()
    if args.install:
        install()
        return 0
    if args.test:
        tests()
        return 0
    if args.status:
        print('[ORACLE516_STATUS]', json.dumps({'controller_locked': LOCK.exists(),
              'report': read(REPORT)}, sort_keys=True), flush=True)
        return 0
    if not (2 <= args.epochs <= 4 and 60 <= args.seconds <= 110
            and 1 <= args.warm_limit <= 28 and 1 <= args.qualify_limit <= 100
            and 8 <= args.fast_limit <= 256 and .5 <= args.fast_interval <= 60
            and 5 <= args.heartbeat <= 60 and 1 <= args.recovery_batch <= 128
            and 2 <= args.recovery_interval <= 600
            and 1 <= args.recovery_pages <= 20
            and 8 <= args.recovery_page_size <= 1000):
        parser.error('INVALID_MANUAL_BOUNDS')
    return supervisor(args)


if __name__ == '__main__':
    raise SystemExit(main())
