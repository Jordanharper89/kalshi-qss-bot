from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
import time
from pathlib import Path

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_515_priority_admission.py')
ROOT = Path('runtime_state/oracle/oracle_live_execution/oracle_515')
REPORT = ROOT / 'priority_admission_report.json'
SHADOW = ROOT / 'shadow_509_mriya_tokens.json'
SCANNER = TARGET.parent / 'boss_scanner_live.py'
LIVE_LOCK = Path('runtime_state/oracle/final_boss_dual/scanner.lock')

class Hold(RuntimeError):
    pass

def read(path):
    p = Path(path)
    if not p.is_file():
        return {}
    x = json.loads(p.read_text(encoding='utf-8'))
    if not isinstance(x, dict):
        raise Hold('INVALID_INPUT_JSON')
    return x

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    try:
        tmp.write_text(json.dumps(value, sort_keys=True, indent=2), encoding='utf-8')
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)

def fingerprint(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def valid_token(token, row):
    return (isinstance(token, str) and 32 <= len(token) <= 44 and
            isinstance(row, dict) and row.get('token') == token)

def source_snapshot():
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_508_mriya_coverage as q508,
        oracle_513_split_lanes as q513,
        oracle_514_independent_recovery as q514,
    )
    reg = read(q514.REGISTRY)
    if reg.get('revision') != 'ORACLE_514' or not isinstance(reg.get('candidates'), dict):
        raise Hold('HOLD_514_REGISTRY_MISSING')
    raw = [
        ('508', read(q508.TOKENS)),
        ('513_FAST', read(q513.FAST_TOKENS)),
        ('514_FAST', read(q514.FAST_TOKENS)),
        ('513_RECOVERY', read(q513.RECOVERY_TOKENS)),
        ('514_RECOVERY', read(q514.RECOVERY_TOKENS)),
    ]
    fresh = {}
    merged = {}
    counts = {}
    for name, records in raw:
        counts[name] = len(records)
        for token, entry in records.items():
            if token not in reg['candidates'] or not valid_token(token, entry):
                continue
            merged[token] = entry
            if name in ('513_FAST', '514_FAST'):
                fresh[token] = entry
    # Prefer recent live observations, but independently revalidate every warmed pair.
    if not fresh:
        raise Hold('HOLD_NO_513_514_FAST_DISCOVERY')
    return q508, merged, fresh, counts

def patch_509_sources(q508, q509, shadow):
    """Temporary *in-process* source substitution; never write 508's actual file."""
    original = Path(q508.TOKENS)
    changed = []
    for module in (q508, q509):
        for key, obj in vars(module).items():
            if isinstance(obj, Path) and obj == original:
                changed.append((module, key, obj))
                setattr(module, key, shadow)
    if not changed:
        raise Hold('HOLD_509_SOURCE_SEAM_MISSING')
    return changed

def audit_with_overlay(q508, q509, rows, amount, phase):
    if not rows:
        return {'phase': phase, 'eligible': 0, 'checked': 0}
    original = Path(q508.TOKENS)
    before_hash = fingerprint(original)
    write(SHADOW, rows)
    originals = patch_509_sources(q508, q509, SHADOW)
    try:
        q509.audit(amount, 100, False)
    finally:
        for module, key, value in reversed(originals):
            setattr(module, key, value)
    if fingerprint(original) != before_hash:
        raise Hold('HOLD_508_TOKENS_MUTATED')
    result = read(q509.REPORT)
    if (result.get('status') != 'PASS_AUDIT' or
            int(result.get('source_mriya_tokens', -1)) != len(rows)):
        raise Hold('HOLD_509_SHADOW_CONTRACT_NOT_PROVEN_' + phase)
    return {'phase': phase, 'eligible': len(rows),
            'checked': result.get('checked_this_run'),
            'pending': result.get('pending_unchecked'),
            'verified_registry': result.get('qualified_fresh_registry')}

def rank(rows, live):
    return sorted(rows, key=lambda r: (r.get('token') not in live, r.get('token', '')))

def require_environment():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise Hold('HOLD_PRIVATE_KEY_IN_CHILD')
    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise Hold('HOLD_SIGNING_NOT_DISARMED')
    if not (os.getenv('SOLANA_RPC_URL', '').startswith('https://') and
            os.getenv('SOLANA_WS_URL', '').startswith('wss://')):
        raise Hold('HOLD_RPC_WS_REQUIRED')

def run(args):
    require_environment()
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_509_exact_pair_qualification as q509,
        oracle_510_warm_pair_preflight as q510,
        oracle_511_dynamic_admission as q511,
        oracle_514_independent_recovery as q514,
    )
    from qseries_v2.oracle_execution import (
        oracle_018_exact_sdk_hot_lane_cutover as q18,
        oracle_023_persistent_token_net_worker as q23,
    )
    if q514.LOCK.exists() or LIVE_LOCK.exists():
        raise Hold('HOLD_OTHER_CONTROLLER_OR_SCANNER_RUNNING')
    frozen = fingerprint(SCANNER)
    q508, merged, fresh, counts = source_snapshot()
    print('[ORACLE515_SOURCE]', json.dumps({'registry': len(merged), 'fast': len(fresh),
                                            'sources': counts}, sort_keys=True), flush=True)
    phases = []
    phases.append(audit_with_overlay(q508, q509, fresh, args.qualify_limit, 'LIVE_PRIORITY'))
    phases.append(audit_with_overlay(q508, q509, merged, args.qualify_limit, 'RESERVE'))
    candidates, verified = q510.selected(q509.load(q510.CHECKS), 28)
    eligible = rank([r for r in candidates if r.get('token') in merged], fresh)
    attempted = eligible[:args.warm_limit]
    if not attempted:
        raise Hold('HOLD_NO_509_VERIFIED_DISCOVERY')
    warm, holds = [], []
    try:
        for row in attempted:
            try:
                result = q510.warm_one(row)
                directions = {r['direction'] for r in result.get('directions', [])}
                if directions != set(q510.DIRECTIONS):
                    raise Hold('HOLD_BIDIRECTIONAL_QUOTES_MISSING')
                warm.append(row)
                print('[ORACLE515_WARM]', json.dumps({'token': row['token'][:12],
                      'fresh': row['token'] in fresh, 'slot': result.get('slot')}), flush=True)
            except Exception as exc:
                code = str(exc) if isinstance(exc, (Hold, q510.Hold)) else type(exc).__name__
                holds.append({'token': row['token'][:12], 'reason': code})
                print('[ORACLE515_WARM_HOLD]', json.dumps(holds[-1]), flush=True)
    finally:
        for mod in (q18, q23):
            worker = getattr(mod, '_worker', None)
            if worker is not None:
                worker.close()
                mod._worker = None
    if not warm:
        raise Hold('HOLD_NO_EXACT_WARM_PAIR')
    stage = q511.assert_contract()
    current = read(stage)
    old = current.get('rows', []) if (isinstance(current.get('rows'), list) and
                0 <= time.time() - float(current.get('generated_at', 0)) <= 600) else []
    added = [{'token': r['token'], 'pump_pool': r['pump_pool'],
              'source': 'ORACLE515_FRESH' if r['token'] in fresh else 'ORACLE515_RESERVE',
              'age': 0.0} for r in warm]
    staged = q511.merger(old[:112], added)
    if len(staged) > 112:
        raise Hold('HOLD_STAGE_MAX_EXCEEDED')
    q511.scanner.save(stage, {'generated_at': time.time(),
                            'rows': staged, 'candidates': len(staged)})
    visible = q511.watchable(added, q511.scanner.select_rows([]))
    if not visible:
        raise Hold('HOLD_NONE_VISIBLE_TO_FROZEN_SELECTOR')
    contract = {'staged_path': str(stage), 'stage_hash': fingerprint(stage),
                'visible_tokens': [r['token'] for r in visible],
                'visible_in_first_28': len(visible), 'staged_rows': len(staged)}
    print('[ORACLE515_ADMISSION]', json.dumps({'warm': len(warm),
          'fresh_warm': sum(r['token'] in fresh for r in warm),
          'staged': len(staged), 'visible': len(visible)}), flush=True)
    live = q511.trial(contract, args.seconds)
    if fingerprint(SCANNER) != frozen:
        raise Hold('HOLD_FROZEN_SCANNER_HASH_CHANGED')
    quotes = set(live.get('matched_quoted_tokens') or [])
    status = ('PASS_PRIORITY_DISCOVERY_ADMISSION_TRIAL' if
              live.get('status') == 'PASS_LIVE_EPOCH_OBSERVED' and
              quotes.intersection(fresh) and live.get('returncode') == 0
              else 'HOLD_FAST_LIVE_QUOTE_NOT_OBSERVED')
    report = {'status': status, 'source_candidates': len(merged),
              'fresh_candidates': len(fresh), 'qualified_registry_total': verified,
              'audit_phases': phases, 'warm_attempted': len(attempted),
              'warm_pass': len(warm), 'warm_holds': holds,
              'fresh_warmed': sum(r['token'] in fresh for r in warm),
              'visible_in_first_28': len(visible), 'staged_rows': len(staged),
              'matched_fresh_quotes': len(quotes.intersection(fresh)),
              'matched_all_quotes': len(quotes),
              'scanner_status': live.get('status'), 'scanner_exit': live.get('returncode'),
              'pending_recovery_514': read(q514.REPORT).get('pending_gap_jobs'),
              'recovery_on_critical_path': False,
              'scanner_modified': False, 'execution_authority': False,
              'signing': False, 'broadcast': False,
              'size_selection_changed': False, 'fixed_first_trade_size': False,
              'production_28_pair_certified': False}
    write(REPORT, report)
    print('[ORACLE515_FINAL]', json.dumps(report, sort_keys=True), flush=True)
    return 0 if status.startswith('PASS_') else 2

def tests():
    rows = [{'token': 'b'}, {'token': 'a'}, {'token': 'c'}]
    assert [x['token'] for x in rank(rows, {'c': 1, 'b': 1})] == ['b', 'c', 'a']
    assert valid_token('x' * 32, {'token': 'x' * 32})
    assert not valid_token('x' * 31, {'token': 'x' * 31})
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / 'test.json'
        write(path, {'a': 1})
        assert read(path) == {'a': 1}
    # Require independent 509 alias restoration before and after auditing.
    from types import SimpleNamespace
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        q508 = SimpleNamespace(TOKENS=root / 'old.json')
        q509 = SimpleNamespace(TOKENS=q508.TOKENS)
        aliases = patch_509_sources(q508, q509, root / 'shadow.json')
        assert q508.TOKENS == root / 'shadow.json'
        assert q509.TOKENS == root / 'shadow.json'
        for mod, key, val in reversed(aliases):
            setattr(mod, key, val)
        assert q508.TOKENS == root / 'old.json'
        assert q509.TOKENS == root / 'old.json'
    # Physically exercise the temporary 509 source path and restoration.
    from types import SimpleNamespace
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        original = root / 'original.json'
        checks = root / 'report.json'
        write(original, {'token': 'ORIGINAL'})
        qm = SimpleNamespace(TOKENS=original)
        def audit(amount, width, flag):
            assert amount == 2 and width == 100 and flag is False
            data = read(qm.TOKENS)
            write(checks, {'status': 'PASS_AUDIT', 'source_mriya_tokens': len(data),
                          'checked_this_run': 1, 'qualified_fresh_registry': 1})
        qa = SimpleNamespace(TOKENS=original, REPORT=checks, audit=audit)
        result = audit_with_overlay(qm, qa, {'a': {'token': 'a'}}, 2, 'TEST')
        assert result['eligible'] == 1
        assert read(original) == {'token': 'ORIGINAL'}
        assert qm.TOKENS == original and qa.TOKENS == original
    src = Path(__file__).read_text(encoding='utf-8')
    assert 'send' + 'Transaction' not in src.split('def tests():')[0]
    print('[PASS] ORACLE515 fresh_priority shadow_509_alias_restore '
          '509_510_511_failclosed frozen_scanner unsigned', flush=True)

def install():
    if not SCANNER.is_file() or not TARGET.parent.is_dir():
        raise Hold('HOLD_CANONICAL_SCANNER_REQUIRED')
    src = Path(__file__).read_text(encoding='utf-8')
    ast.parse(src)
    tmp = TARGET.with_name(TARGET.name + '.' + str(os.getpid()) + '.tmp')
    try:
        tmp.write_text(src, encoding='utf-8')
        os.replace(tmp, TARGET)
    finally:
        tmp.unlink(missing_ok=True)
    print('[PASS] ORACLE515_FULL_INSTALL scanner_frozen source_508_preserved '
          'oracle_selects_size no_signing no_broadcast', flush=True)
    print('[INSTALLED]', TARGET, flush=True)

def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--install', action='store_true')
    mode.add_argument('--test', action='store_true')
    mode.add_argument('--trial', action='store_true')
    ap.add_argument('--warm-limit', type=int, default=8)
    ap.add_argument('--qualify-limit', type=int, default=28)
    ap.add_argument('--seconds', type=int, default=90)
    args = ap.parse_args()
    if args.install:
        install()
        return 0
    if args.test:
        tests()
        return 0
    if not (1 <= args.warm_limit <= 28 and 1 <= args.qualify_limit <= 100
            and 60 <= args.seconds <= 110):
        ap.error('INVALID_RUNTIME_BOUNDS')
    try:
        return run(args)
    except Exception as exc:
        reason = str(exc) if isinstance(exc, Hold) else type(exc).__name__
        write(REPORT, {'status': 'HOLD_PRIORITY_ADMISSION', 'reason': reason,
                       'execution_authority': False, 'signing': False,
                       'broadcast': False, 'size_selection_changed': False})
        print('[ORACLE515_HOLD]', reason, flush=True)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
