from __future__ import annotations
import argparse, ast, hashlib, json, os, threading, time
from pathlib import Path

BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = BASE / 'oracle_521_runtime_progress.py'
SCANNER = BASE / 'boss_scanner_live.py'
STAGE = Path('runtime_state/oracle/final_boss_dual/staged_discovery.json')
R520 = Path('runtime_state/oracle/oracle_live_execution/oracle_520/quote_boundary_audit.json')
REPORT = Path('runtime_state/oracle/oracle_live_execution/oracle_521/quote_coverage.json')
SCANNER_LOCK = Path('runtime_state/oracle/final_boss_dual/scanner.lock')

class Hold(RuntimeError):
    pass

def read(path):
    p = Path(path)
    if not p.is_file():
        raise Hold('MISSING_' + p.name)
    result = json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(result, dict):
        raise Hold('INVALID_' + p.name)
    return result

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    try:
        tmp.write_text(json.dumps(value, sort_keys=True, indent=2),
                       encoding='utf-8')
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)

def guard():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise Hold('PRIVATE_KEY_PRESENT_IN_TRIAL_CHILD')
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise Hold('EXECUTION_ARMED')
    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise Hold('RPC_REQUIRED')
    if not os.getenv('SOLANA_WS_URL', '').startswith('wss://'):
        raise Hold('WS_REQUIRED')
    if SCANNER_LOCK.exists():
        raise Hold('SCANNER_ALREADY_RUNNING')
    report = read(R520)
    if report.get('status') != 'PASS_STATIC_QUOTE_BOUNDARY_TRACED':
        raise Hold('ORACLE520_PASS_REQUIRED')
    if report.get('input_sha256', {}).get(SCANNER.as_posix()) != digest(SCANNER):
        raise Hold('FROZEN_SCANNER_HASH_MISMATCH')

def witness_wrapper(real_trial, evidence, phase):
    def wrapped(contract, seconds):
        phase.update(name='SCANNER_OBSERVATION',
                     since=time.monotonic(), seconds=seconds)
        print('[ORACLE521_SCANNER_START]', json.dumps({
            'visible_pairs': len(contract.get('visible_tokens', [])),
            'seconds': seconds}), flush=True)
        result = real_trial(contract, seconds)
        evidence['contract'] = dict(contract)
        evidence['trial'] = dict(result)
        return result
    return wrapped

def monitor(stop, phase, interval):
    while not stop.wait(interval):
        elapsed = int(time.monotonic() - phase['since'])
        value = {
            'phase': phase['name'],
            'elapsed_seconds': elapsed,
            'execution_authority': False
        }
        if phase['name'] == 'SCANNER_OBSERVATION':
            value['observation_window_seconds'] = phase['seconds']
            value['window_elapsed_percent'] = min(
                95, 100 * elapsed // max(1, phase['seconds']))
        print('[ORACLE521_HEARTBEAT]',
              json.dumps(value, sort_keys=True), flush=True)

def report_result(evidence, admitted, code, telemetry):
    contract = evidence.get('contract', {})
    trial = evidence.get('trial', {})
    tokens = contract.get('visible_tokens', [])
    if not tokens or len(set(tokens)) != len(tokens):
        raise Hold('NO_FRESH_VERIFIED_VISIBLE_PAIRS')
    observed = trial.get('matched_quoted_tokens') or []
    if not isinstance(observed, (set, list, tuple)):
        raise Hold('INVALID_QUOTE_EVIDENCE')
    matched = set(observed)
    if not matched.issubset(set(tokens)):
        raise Hold('QUOTE_OUTSIDE_VISIBLE_STAGE')
    if (int(admitted.get('visible_in_first_28', -1)) != len(tokens)
            or int(admitted.get('matched_all_quotes', -1)) != len(matched)):
        raise Hold('515_521_EVIDENCE_MISMATCH')
    ok = (
        code == 0
        and admitted.get('status') == 'PASS_PRIORITY_DISCOVERY_ADMISSION_TRIAL'
        and trial.get('status') == 'PASS_LIVE_EPOCH_OBSERVED'
        and trial.get('returncode') == 0
    )
    rows = [
        {'token': t,
         'result': 'MATCHED_QUOTE_OBSERVED' if t in matched
                   else 'NO_MATCHED_QUOTE_IN_WINDOW'}
        for t in tokens
    ]
    return {
        'status': 'PASS_LIVE_QUOTE_COVERAGE_MEASURED'
                  if ok else 'HOLD_LIVE_ADMISSION',
        'admission_status': admitted.get('status'),
        'scanner_status': trial.get('status'),
        'scanner_exit': trial.get('returncode'),
        'visible_pairs': len(tokens),
        'matched_quoted_pairs': len(matched),
        'not_observed_pairs': len(tokens) - len(matched),
        'quote_coverage_percent': round(100 * len(matched) / len(tokens), 2),
        'stage_rows': admitted.get('staged_rows'),
        'warm_pass': admitted.get('warm_pass'),
        'warm_holds': admitted.get('warm_holds'),
        'http_warm_telemetry': telemetry,
        'pair_results': rows,
        'absence_of_quote_does_not_prove_subscription_failure': True,
        'scanner_ws_ack_certified': False,
        'production_28_pair_certified': False,
        'net_profitability_certified': False,
        'scanner_modified': False,
        'execution_authority': False,
        'signing': False,
        'broadcast': False
    }

def run(args):
    guard()
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_508_mriya_coverage as q508,
        oracle_510_warm_pair_preflight as q510,
        oracle_511_dynamic_admission as q511,
        oracle_514_independent_recovery as q514,
        oracle_515_priority_admission as q515,
        oracle_516_supervised_replenishment as q516,
        oracle_517_bounded_28_slot_admission as q517
    )
    if q514.LOCK.exists() or q516.LOCK.exists() or q515.LIVE_LOCK.exists():
        raise Hold('ANOTHER_CONTROLLER_RUNNING')

    frozen = digest(SCANNER)
    historical = digest(q508.TOKENS)
    original_merger = q511.merger
    original_warm = q510.warm_one
    original_trial = q511.trial

    telemetry = {
        'http_429_seen': 0,
        'http_429_retries': 0,
        'http_429_exhausted': 0
    }
    evidence = {}
    phase = {
        'name': 'QUALIFY_AND_REWARM',
        'since': time.monotonic(),
        'seconds': args.seconds
    }
    stop = threading.Event()
    watcher = threading.Thread(
        target=monitor,
        args=(stop, phase, args.heartbeat),
        daemon=True
    )
    print('[ORACLE521_START] fresh_verified_admission via_existing_515_517 frozen_scanner',
          flush=True)
    watcher.start()

    try:
        q511.merger = lambda old, added: q517.compact_current_batch(
            original_merger, old, added, args.slot_cap)
        q510.warm_one = q517.pacing_wrapper(
            original_warm, args.warm_spacing, 1, 6, telemetry)
        q511.trial = witness_wrapper(original_trial, evidence, phase)

        code = q515.run(argparse.Namespace(
            warm_limit=args.warm_limit,
            qualify_limit=args.qualify_limit,
            seconds=args.seconds))
    finally:
        q511.merger = original_merger
        q510.warm_one = original_warm
        q511.trial = original_trial
        stop.set()
        watcher.join(timeout=3)

    if digest(SCANNER) != frozen or digest(q508.TOKENS) != historical:
        raise Hold('PROTECTED_SOURCE_CHANGED')

    admitted = read(q515.REPORT)
    if not evidence:
        raise Hold('ADMISSION_STOPPED_BEFORE_LIVE_SCANNER_' +
                   str(admitted.get('reason', 'NO_TRIAL')))

    result = report_result(evidence, admitted, code, telemetry)
    save(REPORT, result)

    for row in result['pair_results']:
        print('[ORACLE521_PAIR]',
              row['token'][:12], row['result'], flush=True)

    print('[ORACLE521_FINAL]', json.dumps({
        k: v for k, v in result.items() if k != 'pair_results'
    }, sort_keys=True), flush=True)

    return 0 if result['status'].startswith('PASS_') else 2

def tests():
    phase = {'name': 'READY', 'since': time.monotonic()}
    evidence = {}
    fake = witness_wrapper(
        lambda c, s: {
            'status': 'PASS_LIVE_EPOCH_OBSERVED',
            'returncode': 0,
            'matched_quoted_tokens': ['A' * 32]
        }, evidence, phase)
    fake({'visible_tokens': ['A' * 32, 'B' * 32]}, 60)
    admission = {
        'status': 'PASS_PRIORITY_DISCOVERY_ADMISSION_TRIAL',
        'visible_in_first_28': 2,
        'matched_all_quotes': 1
    }
    result = report_result(evidence, admission, 0, {})
    assert result['matched_quoted_pairs'] == 1
    assert result['quote_coverage_percent'] == 50
    assert result['status'] == 'PASS_LIVE_QUOTE_COVERAGE_MEASURED'
    try:
        report_result(
            {'contract': {'visible_tokens': []}, 'trial': {}},
            admission, 0, {})
        raise AssertionError('EMPTY_PAIR_BYPASS')
    except Hold:
        pass
    assert phase['name'] == 'SCANNER_OBSERVATION'
    print('[PASS] ORACLE521 refreshed_515_517_selection capture_exact_511_result safe_hold',
          flush=True)

def install():
    if not SCANNER.is_file():
        raise Hold('FROZEN_SCANNER_MISSING')
    src = Path(__file__).read_text(encoding='utf-8')
    ast.parse(src)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    before = digest(SCANNER)
    temp = TARGET.with_name(
        TARGET.name + '.' + str(os.getpid()) + '.tmp')
    try:
        temp.write_text(src, encoding='utf-8')
        os.replace(temp, TARGET)
    finally:
        temp.unlink(missing_ok=True)
    if digest(SCANNER) != before:
        raise Hold('SCANNER_MODIFIED')
    print('[PASS] ORACLE521_FULL_REPLACEMENT fresh_verified_admission frozen_scanner',
          flush=True)

def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    for item in ('install', 'test', 'trial', 'status'):
        mode.add_argument('--' + item, action='store_true')
    ap.add_argument('--seconds', type=int, default=90)
    ap.add_argument('--warm-limit', type=int, default=28)
    ap.add_argument('--qualify-limit', type=int, default=56)
    ap.add_argument('--slot-cap', type=int, default=28)
    ap.add_argument('--warm-spacing', type=float, default=0.8)
    ap.add_argument('--heartbeat', type=int, default=12)
    args = ap.parse_args()
    try:
        if args.install:
            install()
            return 0
        if args.test:
            tests()
            return 0
        if args.status:
            result = read(REPORT)
            print('[ORACLE521_STATUS]', json.dumps({
                k: v for k, v in result.items()
                if k != 'pair_results'
            }, sort_keys=True))
            return 0
        if not (
            60 <= args.seconds <= 110
            and 1 <= args.warm_limit <= 28
            and 1 <= args.qualify_limit <= 100
            and 1 <= args.slot_cap <= 28
            and 0.0 <= args.warm_spacing <= 5.0
            and 5 <= args.heartbeat <= 30
        ):
            raise Hold('INVALID_RUNTIME_ARGUMENTS')
        return run(args)
    except Exception as exc:
        print('[ORACLE521_HOLD]',
              str(exc) if isinstance(exc, Hold)
              else type(exc).__name__, flush=True)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())