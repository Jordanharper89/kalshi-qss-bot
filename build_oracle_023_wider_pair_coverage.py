
from pathlib import Path
import argparse
import inspect
import json
import os
import shutil
import subprocess
import sys
import threading
import unittest
import uuid

BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
NAME = 'oracle_023_wider_pair_coverage.py'
REPORT = Path('runtime_state/oracle/oracle_live_execution/ORACLE_023_PAIR_COVERAGE.json')
V22_REPORT = Path('runtime_state/oracle/oracle_live_execution/ORACLE_022_PRICING.json')
V21_REPORT = Path('runtime_state/oracle/oracle_live_execution/ORACLE_021_POOL_BOOTSTRAP.json')
ATOMIC_REPORT = Path('runtime_state/oracle/oracle_live_execution/ORACLE_ATOMIC_CLOSEOUT.json')

VERSION = 'ORACLE_023_EIGHT_PAIR_WS_COVERAGE'
PAIR_CAP = 8
RPC_CAP = 80
SIM_CAP = 1
CANARY = 10_000_000

P2M = 'PUMP_TO_METEORA'
M2P = 'METEORA_TO_PUMP'

SAFE = {
    'SYSTEMROOT', 'WINDIR', 'SYSTEMDRIVE', 'PATH',
    'PATHEXT', 'TEMP', 'TMP', 'COMSPEC',
    'SOLANA_RPC_URL', 'QSB_SOLANA_RPC_URL',
    'SOLANA_WS_URL', 'QSB_SOLANA_WALLET'
}


def scrub(env):
    return {
        k: v for k, v in env.items()
        if k.upper() in SAFE
    }


class PairLedger:
    def __init__(self):
        self.lock = threading.Lock()
        self.selected = []
        self.quotes = {}
        self.calls = 0

    def select(self, pairs):
        rows = []

        for p in pairs:
            rows.append({
                'token': str(p.token),
                'pump_pool': str(p.pump_pool),
                'meteora_pool': str(p.meteora_pool),
                'watched_accounts': len(p.watched_accounts())
            })

        if len(rows) > PAIR_CAP:
            raise RuntimeError('PAIR_CAP_BREACH')

        if len({r['token'] for r in rows}) != len(rows):
            raise RuntimeError('DUPLICATE_PAIR_TOKEN')

        with self.lock:
            self.selected = rows

    def record(self, token, rows):
        with self.lock:
            self.calls += 1

            for row in rows:
                direction = row.get('direction')

                if direction not in (P2M, M2P):
                    continue

                if str(row.get('token')) != str(token):
                    raise RuntimeError('QUOTE_TOKEN_MISMATCH')

                net = int(row['local_net'])
                key = (str(token), direction)

                old = self.quotes.get(key)

                if old is None:
                    old = {
                        'count': 0,
                        'positive_count': 0,
                        'best_lamports': None
                    }
                    self.quotes[key] = old

                old['count'] += 1
                old['positive_count'] += int(net > 0)

                if (
                    old['best_lamports'] is None
                    or net > old['best_lamports']
                ):
                    old['best_lamports'] = net

    def snapshot(self):
        with self.lock:
            rows = [
                {
                    'token': token,
                    'direction': direction,
                    **values
                }
                for (token, direction), values
                in sorted(self.quotes.items())
            ]

            return {
                'prepared_pair_count': len(self.selected),
                'prepared_pairs': list(self.selected),
                'quoted_snapshot_calls': self.calls,
                'pair_direction_quotes': rows,
                'positive_local_quote_count': sum(
                    x['positive_count'] for x in rows
                )
            }


def checked_report(root, path, run_id):
    p = root / path

    if not p.is_file():
        raise RuntimeError('MISSING_RUN_REPORT')

    result = json.loads(
        p.read_text(encoding='utf-8')
    )

    if result.get('run_id') != run_id:
        raise RuntimeError('STALE_RUN_REPORT')

    return result


def save(root, data):
    dest = root / REPORT
    dest.parent.mkdir(parents=True, exist_ok=True)

    tmp = dest.with_suffix('.tmp')
    tmp.write_text(
        json.dumps(data, indent=2, sort_keys=True) + '\n',
        encoding='utf-8'
    )
    tmp.replace(dest)


def assess(d):
    if (
        int(d.get('rpc_requests') or 0) > RPC_CAP
        or int(d.get('simulations') or 0) > SIM_CAP
    ):
        return 'HOLD_RPC_OR_SIM_LIMIT_EXCEEDED'

    if not d.get('prepared_pair_count'):
        return 'HOLD_NO_PREPARED_PAIRS'

    if int(d.get('ready') or 0) < 4:
        return 'HOLD_INSUFFICIENT_READY_PAIRS'

    if int(d.get('priced_events') or 0) <= 0:
        return 'HOLD_NO_PRICED_EVENTS'

    if (
        d.get('scanner_status')
        != 'SCANNER_ACTIVE_EXECUTION_UNCERTIFIED'
    ):
        return 'HOLD_SCANNER_INTEGRITY'

    count = d.get('successful_directions') or {}

    if not all(
        int(count.get(k) or 0) > 0
        for k in (P2M, M2P)
    ):
        return 'HOLD_DIRECTIONAL_PRICING'

    if int(d.get('ready') or 0) <= 4:
        return 'BASELINE_COVERAGE_ACTIVE_NO_EXPANSION'

    return 'EXPANDED_COVERAGE_ACTIVE_PROFIT_UNCERTIFIED'


def child(root, seconds, run_id):
    result = {
        'version': VERSION,
        'run_id': run_id,
        'status': 'HOLD',
        'scanner_code_unchanged': True,
        'signing': False,
        'broadcast': False,
        'canary_sent': False,
        'profit_certified': False,
        'pair_cap': PAIR_CAP,
        'rpc_cap': RPC_CAP,
        'sim_cap': SIM_CAP
    }

    if any(
        'PRIVATE_KEY' in k.upper()
        or 'SECRET_KEY' in k.upper()
        for k in os.environ
    ):
        result['hold'] = 'SECRET_IN_CHILD'
        save(root, result)
        return 2

    sys.path.insert(0, str(root))

    ledger = PairLedger()

    try:
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
        from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_022_direction_isolated_pricing as v22
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_015_rpc_efficient_bootstrap as v15
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_atomic_closeout as atomic

        if q19.persistent.m.pd is not pd:
            raise RuntimeError('SCANNER_PAIR_STATE_MODULE_DRIFT')

        if not v22.VERSION.startswith('ORACLE_022_'):
            raise RuntimeError('V22_REQUIRED')

        if not atomic.VERSION.startswith(
            'ORACLE_ATOMIC_CLOSEOUT_V20_'
        ):
            raise RuntimeError('V20_REQUIRED')

        if (
            v15.MAX_RPC,
            v15.MAX_SIM,
            v15.CANARY
        ) != (RPC_CAP, SIM_CAP, CANARY):
            raise RuntimeError('RPC_GUARD_DRIFT')

        old_max = pd.MAX_PAIRS
        original_prepare = pd.prepare_pairs
        original_split = v22.split_exact

        def limited_prepare(path):
            pairs, landing = original_prepare(path)
            ledger.select(pairs)
            return pairs, landing

        def tracked_split(q18, snap, size, diag):
            rows = original_split(
                q18, snap, size, diag
            )
            ledger.record(snap['token'], rows)
            return rows

        pd.MAX_PAIRS = PAIR_CAP
        pd.prepare_pairs = limited_prepare
        v22.split_exact = tracked_split

        try:
            status = v22.child(
                root, seconds, run_id
            )
        finally:
            pd.MAX_PAIRS = old_max
            pd.prepare_pairs = original_prepare
            v22.split_exact = original_split

        v22_data = checked_report(
            root, V22_REPORT, run_id
        )
        v21_data = checked_report(
            root, V21_REPORT, run_id
        )
        atomic_data = checked_report(
            root, ATOMIC_REPORT, run_id
        )

        result.update(ledger.snapshot())

        result.update(
            ready=v22_data.get('ready', 0),
            priced_events=v22_data.get('priced_events', 0),
            successful_directions=(
                v22_data.get('successful_directions') or {}
            ),
            pricing_rejections=(
                v22_data.get('rejections_by_stage') or {}
            ),
            best_quotes=v22_data.get('best_quotes') or {},
            scanner_status=v22_data.get('scanner_status'),
            scanner=v21_data.get('scanner') or {},
            identity_validation=(
                v21_data.get('identity_validation') or {}
            ),
            rpc_requests=v21_data.get('rpc_requests', 0),
            rpc_by_method=(
                v21_data.get('rpc_by_method') or {}
            ),
            simulations=v21_data.get('simulations', 0),
            atomic_status=atomic_data.get('status'),
            local_rejections=(
                atomic_data.get('local_check_reject') or {}
            ),
            local_check_pass=(
                atomic_data.get('local_check_pass', 0)
            ),
            atomic_attempts=(
                atomic_data.get('attempts') or []
            ),
            holds=atomic_data.get('holds') or []
        )

        result['status'] = assess(result)

        if status != 0:
            result['status'] = 'HOLD_NESTED_RUNTIME_EXIT'

        save(root, result)
        return status

    except Exception as exc:
        result.update(ledger.snapshot())
        result['hold'] = 'V23_' + type(exc).__name__
        save(root, result)
        return 2


def parent(root, seconds):
    run_id = str(uuid.uuid4())

    cmd = [
        sys.executable,
        '-I',
        str(Path(__file__).resolve()),
        '--child',
        '--seconds',
        str(seconds),
        '--run-id',
        run_id
    ]

    proc = None

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=root,
            env=scrub(os.environ),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        def relay():
            for line in proc.stdout:
                if line.startswith('[ORACLE017_PULSE]'):
                    print(line.rstrip(), flush=True)

        thread = threading.Thread(
            target=relay,
            daemon=True
        )
        thread.start()

        code = proc.wait(timeout=seconds + 180)
        thread.join(timeout=2)

        d = checked_report(root, REPORT, run_id)

        for key in (
            'status',
            'hold',
            'prepared_pair_count',
            'ready',
            'scanner',
            'rpc_requests',
            'rpc_by_method',
            'priced_events',
            'successful_directions',
            'positive_local_quote_count',
            'pair_direction_quotes',
            'pricing_rejections',
            'best_quotes',
            'local_check_pass',
            'local_rejections',
            'simulations',
            'atomic_attempts',
            'holds'
        ):
            if key in d:
                print(
                    '[' + key.upper() + ']',
                    json.dumps(d[key], sort_keys=True),
                    flush=True
                )

        print(
            '[SCANNER] FROZEN '
            '[PAIR_CAP] 8 '
            '[RPC_CAP] 80 '
            '[SIM_CAP] 1',
            flush=True
        )

        print(
            '[SIGNING] FALSE '
            '[BROADCAST] FALSE '
            '[CANARY] UNSENT',
            flush=True
        )
        print('[REPORT]', root / REPORT, flush=True)
        return code

    except Exception as exc:
        print(
            '[HOLD] V23_PARENT_' + type(exc).__name__,
            flush=True
        )
        return 2

    finally:
        if proc and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)


class Tests(unittest.TestCase):

    def test_env_scrub(self):
        self.assertEqual(
            scrub({
                'PATH': 'ok',
                'QSB_SOLANA_PRIVATE_KEY': 'secret'
            }),
            {'PATH': 'ok'}
        )

    def test_budget(self):
        self.assertEqual(
            (PAIR_CAP, RPC_CAP, SIM_CAP, CANARY),
            (8, 80, 1, 10_000_000)
        )

    def test_tracking(self):
        l = PairLedger()

        class P:
            token = 't'
            pump_pool = 'p'
            meteora_pool = 'm'

            def watched_accounts(self):
                return ['a', 'b']

        l.select([P()])

        l.record('t', [
            {'token': 't', 'direction': P2M, 'local_net': -100},
            {'token': 't', 'direction': M2P, 'local_net': 500}
        ])

        l.record('t', [
            {'token': 't', 'direction': P2M, 'local_net': 100}
        ])

        d = l.snapshot()

        self.assertEqual(
            d['positive_local_quote_count'], 2
        )
        self.assertEqual(
            d['prepared_pair_count'], 1
        )
        self.assertEqual(
            next(
                x for x in d['pair_direction_quotes']
                if x['direction'] == P2M
            )['best_lamports'],
            100
        )

    def test_quote_token_guard(self):
        with self.assertRaisesRegex(
            RuntimeError,
            'QUOTE_TOKEN_MISMATCH'
        ):
            PairLedger().record('t', [
                {
                    'token': 'x',
                    'direction': P2M,
                    'local_net': 2
                }
            ])

    def test_duplicate_rejected(self):
        l = PairLedger()

        class P:
            token = 't'
            pump_pool = 'p'
            meteora_pool = 'm'

            def watched_accounts(self):
                return []

        with self.assertRaisesRegex(
            RuntimeError,
            'DUPLICATE'
        ):
            l.select([P(), P()])

    def test_assess(self):
        d = {
            'prepared_pair_count': 8,
            'ready': 8,
            'priced_events': 5,
            'scanner_status': 'SCANNER_ACTIVE_EXECUTION_UNCERTIFIED',
            'successful_directions': {
                P2M: 3,
                M2P: 3
            },
            'rpc_requests': 70,
            'simulations': 0
        }

        self.assertEqual(
            assess(d),
            'EXPANDED_COVERAGE_ACTIVE_PROFIT_UNCERTIFIED'
        )
        self.assertEqual(
            assess(dict(d, rpc_requests=81)),
            'HOLD_RPC_OR_SIM_LIMIT_EXCEEDED'
        )
        self.assertEqual(
            assess(dict(d, successful_directions={P2M: 3})),
            'HOLD_DIRECTIONAL_PRICING'
        )

    def test_test_does_not_call_helius(self):
        self.assertNotIn(
            'sendTransaction',
            inspect.getsource(child)
        )

    def test_installed_dependencies(self):
        from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19
        from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_022_direction_isolated_pricing as v22

        self.assertIs(
            q19.persistent.m.pd,
            pd
        )
        self.assertTrue(
            v22.VERSION.startswith('ORACLE_022_')
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--test', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--child', action='store_true')
    ap.add_argument('--seconds', type=int, default=60)
    ap.add_argument('--run-id', default='')

    a = ap.parse_args()
    root = Path.cwd()

    if a.test:
        t = unittest.TextTestRunner(
            verbosity=2
        ).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(
                Tests
            )
        )
        return 0 if t.wasSuccessful() else 1

    if a.child:
        return child(root, a.seconds, a.run_id)

    if a.run:
        if not 45 <= a.seconds <= 90:
            print('[HOLD] SESSION_BOUNDS_45_TO_90_SECONDS')
            return 2
        return parent(root, a.seconds)

    dest = root / BASE / NAME

    if not dest.parent.is_dir():
        print('[HOLD] CANONICAL_EXECUTOR_PACKAGE_MISSING')
        return 2

    if dest.resolve() != Path(__file__).resolve():
        shutil.copyfile(
            Path(__file__),
            dest
        )

    print('[PASS]', VERSION, dest)
    print(
        '[MODE] UP_TO_8_PAIRS; EXACT_QUOTES; '
        'ONE_STARTUP; FROZEN_SCANNER'
    )
    print(
        '[GUARDS] RPC_80; SIM_1; '
        'SIGNING_FALSE; BROADCAST_FALSE'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
