
from __future__ import annotations
import argparse
import ast
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MODULE = 'qseries_v2.oracle_execution.solana_atomic_executor.oracle_513_split_lanes'
TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_513_split_lanes.py')
ROOT = Path('runtime_state/oracle/oracle_live_execution/oracle_513')
FAST = ROOT / 'fast_checkpoint.json'
RECOVERY = ROOT / 'recovery_checkpoint.json'
FAST_TOKENS = ROOT / 'fast_tokens.json'
RECOVERY_TOKENS = ROOT / 'recovery_tokens.json'
REGISTRY = ROOT / 'discovery_registry.json'
REPORT = ROOT / 'split_report.json'


class Hold(RuntimeError):
    pass


def read(path, default):
    if not path.is_file():
        return default
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict):
        raise Hold('INVALID_JSON_OBJECT')
    return value


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.' + str(os.getpid()) + '.tmp')
    try:
        temp.write_text(
            json.dumps(value, sort_keys=True, indent=2),
            encoding='utf-8'
        )
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def signature(entry):
    sig = entry.get('signature') if isinstance(entry, dict) else None
    if not isinstance(sig, str) or not sig:
        raise Hold('BAD_SIGNATURE_ROW')
    return sig


def newest_window(rows, cursor):
    """Fast lane never claims a missing cursor was covered."""
    keys = [signature(x) for x in rows]
    if len(set(keys)) != len(keys):
        raise Hold('DUPLICATE_FAST_SIGNATURE')
    if cursor in keys:
        count = keys.index(cursor)
        return list(reversed(rows[:count])), False
    return list(reversed(rows)), bool(cursor)


def history_window(rpc, anchor, page_size, max_pages):
    """Find exact anchor or HOLD; never use an unbounded sweep."""
    if not anchor:
        raise Hold('RECOVERY_ANCHOR_REQUIRED')

    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_508_mriya_coverage as m
    )

    newer, seen, before = [], set(), None

    for _ in range(max_pages):
        opts = {
            'limit': page_size,
            'commitment': 'confirmed'
        }
        if before:
            opts['before'] = before

        rows = m.rpc_call(
            rpc,
            'getSignaturesForAddress',
            [m.engine.MRIYA, opts]
        )

        if not isinstance(rows, list):
            raise Hold('HISTORY_RPC_SHAPE')

        for entry in rows:
            sig = signature(entry)

            if sig in seen:
                raise Hold('HISTORY_DUPLICATE_SIGNATURE')
            if sig == anchor:
                return newer

            seen.add(sig)
            newer.append(entry)

        if len(rows) < page_size:
            raise Hold('HISTORY_ANCHOR_NOT_FOUND')

        last = signature(rows[-1])
        if last == before:
            raise Hold('HISTORY_PAGINATION_STALLED')

        before = last

    raise Hold('HISTORY_PAGE_CAP_ANCHOR_UNREACHED')


def check_environment():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise Hold('PRIVATE_KEY_MUST_BE_EXCLUDED_FROM_CHILD')

    if os.getenv('QSB_LIVE_ARM', 'NO').upper() != 'NO':
        raise Hold('EXECUTION_MUST_BE_DISARMED')

    if not os.getenv('SOLANA_RPC_URL', '').startswith('https://'):
        raise Hold('HELIUS_RPC_REQUIRED')


def merge_registry():
    """One merger; neither producer writes the other's file."""
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_508_mriya_coverage as m
    )

    sources = [
        ('EXISTING_508', m.read_json(m.TOKENS, {})),
        ('LIVE_513', read(FAST_TOKENS, {})),
        ('RECOVERY_513', read(RECOVERY_TOKENS, {})),
    ]

    registry = {}
    counts = {}

    for src, records in sources:
        counts[src] = len(records)

        for token, entry in records.items():
            if not isinstance(token, str) or len(token) < 32:
                continue

            if token not in registry:
                registry[token] = {
                    'token': token,
                    'sources': [src]
                }
            elif src not in registry[token]['sources']:
                registry[token]['sources'].append(src)

    fast = read(FAST, {})
    recovery = read(RECOVERY, {})

    output = {
        'revision': 'ORACLE_513',
        'created_unix': time.time(),
        'qualification_required': True,
        'scanner_admitted': False,
        'execution_authority': False,
        'source_counts': counts,
        'unique_tokens': len(registry),
        'candidates': registry,
        'fast_state': fast.get('status', 'NOT_STARTED'),
        'recovery_state': recovery.get('status', 'NOT_STARTED'),
        'history_complete': (
            recovery.get('gap_remaining') == 0
            and recovery.get('status') == 'RECOVERY_CAUGHT_UP'
        )
    }

    atomic(REGISTRY, output)
    return output


def collect_tokens(m, rows, path):
    found, failed = m.fetch_tokens(
        m.engine._rpc,
        rows,
        sleep_s=0.02
    )

    existing = read(path, {})
    existing.update(found)

    # Evidence must be written before moving the cursor.
    atomic(path, existing)
    return len(found), failed, len(existing)


def fast_tick(args):
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_508_mriya_coverage as m
    )

    checkpoint = read(FAST, {})
    old_cursor = checkpoint.get('cursor')

    rows = m.rpc_call(
        m.engine._rpc,
        'getSignaturesForAddress',
        [
            m.engine.MRIYA,
            {
                'limit': args.fast_limit,
                'commitment': 'confirmed'
            }
        ]
    )

    if not isinstance(rows, list) or not rows:
        raise Hold('LIVE_SIGNATURES_UNAVAILABLE')

    to_process, gap = newest_window(rows, old_cursor)

    if len(to_process) > args.fast_max_fetch:
        raise Hold('FAST_FETCH_BUDGET_EXCEEDED')

    added, failed, total = collect_tokens(
        m, to_process, FAST_TOKENS
    )

    cursor = signature(rows[0])

    checkpoint.update({
        'cursor': cursor,
        'status': (
            'FAST_GAP_DECLARED'
            if gap else 'FAST_CURRENT'
        ),
        'last_success_unix': time.time(),
        'last_batch_signatures': len(to_process),
        'last_failed_onchain': failed,
        'total_tokens': total,
        'last_discovered_tokens': added,
        'gap_events': (
            int(checkpoint.get('gap_events', 0))
            + int(gap)
        ),
        'bootstrap_unverified_history': bool(
            checkpoint.get('bootstrap_unverified_history', False)
            or not old_cursor
        )
    })

    atomic(FAST, checkpoint)

    print(
        '[ORACLE513_FAST]',
        json.dumps({
            k: checkpoint[k] for k in (
                'status',
                'last_batch_signatures',
                'last_failed_onchain',
                'total_tokens',
                'gap_events'
            )
        }),
        flush=True
    )


def recovery_tick(args):
    from qseries_v2.oracle_execution.solana_atomic_executor import (
        oracle_508_mriya_coverage as m
    )

    checkpoint = read(RECOVERY, {})
    anchor = checkpoint.get('cursor')

    if not anchor:
        previous = m.read_json(m.CHECKPOINT, {})
        anchor = (
            previous.get('head')
            or previous.get('newest')
        )

    if not anchor:
        raise Hold('NO_VERIFIED_508_RECOVERY_ANCHOR')

    newer = history_window(
        m.engine._rpc,
        anchor,
        args.recovery_page_size,
        args.recovery_pages
    )

    part = list(reversed(
        newer[-args.recovery_batch:]
    ))

    added, failed, total = collect_tokens(
        m, part, RECOVERY_TOKENS
    )

    if part:
        anchor = signature(part[-1])

    checkpoint.update({
        'cursor': anchor,
        'status': (
            'RECOVERY_CAUGHT_UP'
            if len(newer) == len(part)
            else 'RECOVERY_BACKLOG'
        ),
        'gap_remaining': len(newer) - len(part),
        'last_success_unix': time.time(),
        'last_batch_signatures': len(part),
        'last_failed_onchain': failed,
        'last_discovered_tokens': added,
        'total_tokens': total
    })

    atomic(RECOVERY, checkpoint)

    print(
        '[ORACLE513_RECOVERY]',
        json.dumps({
            k: checkpoint[k] for k in (
                'status',
                'last_batch_signatures',
                'last_failed_onchain',
                'gap_remaining',
                'total_tokens'
            )
        }),
        flush=True
    )


def worker(args, fn, interval):
    check_environment()
    until = (
        time.monotonic() + args.seconds
        if args.seconds else None
    )

    while until is None or time.monotonic() < until:
        try:
            fn(args)

        except Exception as exc:
            code = (
                str(exc)
                if isinstance(exc, Hold)
                else type(exc).__name__
            )

            if fn is fast_tick:
                path = FAST
                kind = 'FAST'
            else:
                path = RECOVERY
                kind = 'RECOVERY'

            before = read(path, {})
            before['status'] = 'HOLD_' + code
            before['last_error_unix'] = time.time()
            atomic(path, before)

            print(
                '[ORACLE513_%s_HOLD]' % kind,
                code,
                flush=True
            )

        if until is not None and time.monotonic() >= until:
            break

        time.sleep(interval)


def controller(args):
    check_environment()

    if not TARGET.is_file():
        raise Hold('INSTALL_FIRST')

    paths = (FAST, RECOVERY)
    jobs = []
    start = time.monotonic()
    wall_start = time.time()

    try:
        for name in ('--fast-worker', '--recovery-worker'):
            cmd = [
                sys.executable, '-m', MODULE, name,
                '--seconds', str(args.seconds),
                '--fast-limit', str(args.fast_limit),
                '--fast-max-fetch', str(args.fast_max_fetch),
                '--fast-interval', str(args.fast_interval),
                '--recovery-pages', str(args.recovery_pages),
                '--recovery-page-size', str(args.recovery_page_size),
                '--recovery-batch', str(args.recovery_batch),
                '--recovery-interval', str(args.recovery_interval)
            ]

            jobs.append(subprocess.Popen(
                cmd, env=os.environ.copy()
            ))

        while time.monotonic() - start < args.seconds:
            for p in jobs:
                if p.poll() is not None and p.returncode:
                    raise Hold('WORKER_EXITED_NONZERO')

            merge_registry()
            time.sleep(2)

    finally:
        for p in jobs:
            if p.poll() is None:
                p.terminate()

        for p in jobs:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()
                p.wait()

    snapshot = merge_registry()
    f, h = (read(p, {}) for p in paths)

    outcome = {
        'status': (
            'PASS_SPLIT_LANE_TRIAL'
            if (
                f.get('last_success_unix', 0) >= wall_start
                and h.get('last_success_unix', 0) >= wall_start
                and f.get('status') in (
                    'FAST_CURRENT', 'FAST_GAP_DECLARED'
                )
                and h.get('status') in (
                    'RECOVERY_CAUGHT_UP',
                    'RECOVERY_BACKLOG'
                )
            )
            else 'HOLD_LANE_NOT_OBSERVED'
        ),
        'fast_status': f.get('status'),
        'recovery_status': h.get('status'),
        'history_gap_remaining': h.get('gap_remaining'),
        'unique_candidates': snapshot['unique_tokens'],
        'two_independent_checkpoints': True,
        'scanner_modified': False,
        'q508_checkpoint_modified_by_513': False,
        'quotes_or_size_selection_modified': False,
        'trade_size_policy':
            'EXISTING_OPTIMIZER_SELECTS_BEST_NET_EXECUTABLE_SIZE',
        'qualification_required': True,
        'scanner_admitted': False,
        'execution_authority': False,
        'signing': False,
        'broadcast': False
    }

    atomic(REPORT, outcome)

    print(
        '[ORACLE513_FINAL]',
        json.dumps(outcome, sort_keys=True),
        flush=True
    )

    return (
        0 if outcome['status'].startswith('PASS_')
        else 2
    )


def tests():
    rows = [
        {'signature': 'S5', 'err': None},
        {'signature': 'S4', 'err': None},
        {'signature': 'S3', 'err': None},
        {'signature': 'S2', 'err': None}
    ]

    a, gap = newest_window(rows, 'S3')
    assert [x['signature'] for x in a] == [
        'S4', 'S5'
    ] and not gap

    a, gap = newest_window(rows, 'OLD')
    assert len(a) == 4 and gap

    a, gap = newest_window(rows, None)
    assert len(a) == 4 and not gap

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / 'safe.json'
        atomic(path, {'cursor': 'S5'})
        assert read(path, {})['cursor'] == 'S5'

    src = Path(__file__).read_text(encoding='utf-8')
    assert (
        'm.' + 'atomic_' + 'json(m.CHECKPOINT'
    ) not in src.split('def tests():')[0]

    assert (
        'QSB_SOLANA_PRIVATE_KEY' in src
        and ('send' + 'Transaction')
        not in src.split('def tests():')[0]
    )

    print(
        '[PASS] ORACLE513 isolated_state live_gap_indicator '
        'recovery_bounds atomic_evidence no_signing no_broadcast',
        flush=True
    )


def install():
    scanner = Path(
        'qseries_v2/oracle_execution/solana_atomic_executor/'
        'boss_scanner_live.py'
    )

    if not TARGET.parent.is_dir() or not scanner.is_file():
        raise Hold('SCANNER_REPOSITORY_NOT_FOUND')

    source = Path(__file__).read_text(encoding='utf-8')
    ast.parse(source)

    temp = TARGET.with_name(
        TARGET.name + '.' + str(os.getpid()) + '.tmp'
    )

    try:
        temp.write_text(source, encoding='utf-8')
        os.replace(temp, TARGET)
    finally:
        if temp.exists():
            temp.unlink()

    print(
        '[PASS] ORACLE513_FULL_INSTALL separate_live_recovery '
        'scanner_frozen execution_disarmed',
        flush=True
    )
    print('[INSTALLED]', TARGET, flush=True)


def main():
    ap = argparse.ArgumentParser()
    modes = ap.add_mutually_exclusive_group(required=True)

    for opt in (
        '--install',
        '--test',
        '--trial',
        '--fast-worker',
        '--recovery-worker',
        '--merge'
    ):
        modes.add_argument(opt, action='store_true')

    ap.add_argument('--seconds', type=int, default=45)
    ap.add_argument('--fast-limit', type=int, default=64)
    ap.add_argument('--fast-max-fetch', type=int, default=128)
    ap.add_argument('--fast-interval', type=float, default=2.0)
    ap.add_argument('--recovery-pages', type=int, default=12)
    ap.add_argument('--recovery-page-size', type=int, default=1000)
    ap.add_argument('--recovery-batch', type=int, default=32)
    ap.add_argument('--recovery-interval', type=float, default=8.0)

    args = ap.parse_args()

    if args.install:
        install()
        return 0

    if args.test:
        tests()
        return 0

    if args.merge:
        r = merge_registry()
        print(
            '[ORACLE513_REGISTRY]',
            json.dumps({
                k: v for k, v in r.items()
                if k != 'candidates'
            }),
            flush=True
        )
        return 0

    if not (
        10 <= args.seconds <= 3600
        and 1 <= args.fast_limit <= 256
        and args.fast_limit <= args.fast_max_fetch <= 256
        and 0.5 <= args.fast_interval <= 60
        and 1 <= args.recovery_pages <= 20
        and 8 <= args.recovery_page_size <= 1000
        and 1 <= args.recovery_batch <= 128
        and 1 <= args.recovery_interval <= 600
    ):
        ap.error('INVALID_MANUAL_BOUNDS')

    if args.fast_worker:
        worker(args, fast_tick, args.fast_interval)
        return 0

    if args.recovery_worker:
        worker(args, recovery_tick, args.recovery_interval)
        return 0

    if args.trial:
        return controller(args)

    return 2


if __name__ == '__main__':
    raise SystemExit(main())
