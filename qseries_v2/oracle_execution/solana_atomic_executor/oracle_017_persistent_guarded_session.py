
from pathlib import Path
import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
import time
import unittest
import uuid

PACKAGE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = 'oracle_017_persistent_guarded_session.py'
REPORT = Path(
    'runtime_state/oracle/oracle_live_execution/ORACLE_017_SESSION.json'
)
PARENT_REPORT = Path(
    'runtime_state/oracle/oracle_live_execution/ORACLE_ATOMIC_CLOSEOUT.json'
)
VERSION = 'ORACLE_017B_DIRECT_SCANNER_GUARDED_SESSION'

SAFE = {
    'SYSTEMROOT','WINDIR','SYSTEMDRIVE','PATH','PATHEXT',
    'TEMP','TMP','COMSPEC','QSB_SOLANA_WALLET',
    'SOLANA_RPC_URL','QSB_SOLANA_RPC_URL','SOLANA_WS_URL'
}


def clean_env(env):
    return {
        k:v for k,v in env.items()
        if k.upper() in SAFE
    }


def classify_error(value):
    x = str(value or '').lower()
    for fragment,label in (
        ('429','RATE_LIMIT'),
        ('rate limit','RATE_LIMIT'),
        ('401','AUTH'),
        ('403','AUTH'),
        ('timeout','TIMEOUT'),
        ('timed out','TIMEOUT'),
        ('name resolution','DNS'),
        ('gaierror','DNS'),
        ('ssl','TLS'),
        ('handshake','HANDSHAKE'),
        ('connection closed','CLOSED'),
        ('refused','REFUSED')
    ):
        if fragment in x:
            return label
    return 'UNCLASSIFIED' if x else 'NONE'


def assess(report):
    scanner = report.get('scanner') or {}
    subscribed = sum(report.get('shard_sizes') or [])
    evaluations = report.get('evaluations') or {}

    if (
        int(report.get('rpc_requests') or 0) > 80
        or int(report.get('simulations') or 0) > 1
    ):
        return 'HOLD_BUDGET_BREACH'

    if int(scanner.get('acks') or 0) == 0:
        return 'HOLD_SCANNER_NOT_CONNECTED'

    if (
        subscribed == 0
        or int(scanner.get('acks') or 0) < subscribed
    ):
        return 'HOLD_INCOMPLETE_SUBSCRIPTIONS'

    if int(scanner.get('notifications') or 0) == 0:
        return 'HOLD_NO_MARKET_NOTIFICATIONS'

    if (
        int(report.get('ready') or 0) < 4
        or int(report.get('priced_events') or 0) == 0
    ):
        return 'HOLD_PAIR_COVERAGE_OR_PRICING'

    for direction in (
        'PUMP_TO_METEORA',
        'METEORA_TO_PUMP'
    ):
        if int(evaluations.get(direction) or 0) == 0:
            return 'HOLD_DIRECTION_NOT_PRICED'

    return 'SCANNER_ACTIVE_EXECUTION_UNCERTIFIED'


def save(root,data):
    path = root / REPORT
    path.parent.mkdir(parents=True,exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(
        json.dumps(data,sort_keys=True,indent=2)+'\n',
        encoding='utf-8'
    )
    temp.replace(path)


def child(root,seconds,run_id):
    result = {
        'version':VERSION,
        'run_id':run_id,
        'status':'HOLD',
        'signing':False,
        'broadcast':False,
        'canary_sent':False,
        'net_profit_certified':False,
        'scanner_unchanged':True
    }

    if any(
        'PRIVATE_KEY' in k.upper()
        or 'SECRET_KEY' in k.upper()
        for k in os.environ
    ):
        result['hold'] = 'SECRET_IN_CHILD'
        save(root,result)
        return 2

    try:
        sys.path.insert(0,str(root))

        from qseries_v2.oracle_execution import (
            oracle_019_venue_native_reserve_feed_cutover as q19
        )
        from qseries_v2.oracle_execution.solana_atomic_executor import (
            oracle_015_rpc_efficient_bootstrap as v15
        )
        from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core

        if (
            v15.MAX_RPC,
            v15.MAX_SIM,
            v15.CANARY
        ) != (80,1,10_000_000):
            raise RuntimeError('GUARD_CONTRACT_DRIFT')

        original_worker = q19.persistent._worker
        original_rpc = core.rpc

        seen = {
            'worker':None,
            'shards':[],
            'rpc':0
        }

        stop_pulse = threading.Event()
        started = time.monotonic()

        async def observed_worker(
            i,addresses,queue,counters,stop
        ):
            seen['worker'] = counters
            seen['shards'].append(len(addresses))
            return await original_worker(
                i,addresses,queue,counters,stop
            )

        def counted_rpc(method,params):
            seen['rpc'] += 1
            return original_rpc(method,params)

        def heartbeat():
            while not stop_pulse.wait(10):
                c = seen['worker'] or {}
                print(
                    '[ORACLE017_PULSE] '
                    'elapsed=%d rpc=%d acks=%d '
                    'notifications=%d reconnects=%d'
                    % (
                        time.monotonic()-started,
                        seen['rpc'],
                        c.get('acks',0),
                        c.get('notifications',0),
                        c.get('reconnects',0)
                    ),
                    flush=True
                )

        q19.persistent._worker = observed_worker
        core.rpc = counted_rpc

        pulse = threading.Thread(
            target=heartbeat,
            daemon=True
        )
        pulse.start()

        try:
            code = v15.child(
                root,seconds,run_id
            )
        finally:
            stop_pulse.set()
            pulse.join(timeout=1)
            core.rpc = original_rpc
            q19.persistent._worker = original_worker

        p = json.loads(
            (root/PARENT_REPORT).read_text(
                encoding='utf-8'
            )
        )

        if (
            p.get('run_id') != run_id
            or p.get('two_venue_bootstrap') != v15.VERSION
        ):
            raise RuntimeError(
                'STALE_OR_WRONG_CHILD_REPORT'
            )

        c = seen['worker'] or {}

        result.update(
            ready=p.get('ready',0),
            priced_events=p.get('priced_events',0),
            evaluations=p.get('evaluations',{}),
            best_quotes=p.get('best_quotes',{}),
            rpc_requests=p.get('rpc_budget_used',0),
            rpc_by_method=p.get('rpc_counts_measured',{}),
            simulations=p.get('rpc_simulations_measured',0),
            holds=p.get('holds',[]),
            shard_sizes=seen['shards'],
            scanner={
                k:int(c.get(k,0) or 0)
                for k in (
                    'acks',
                    'connections',
                    'notifications',
                    'reconnects',
                    'rate_limit_disconnects',
                    'event_errors',
                    'queue_drops'
                )
            },
            ws_error_category=classify_error(
                c.get('last_ws_error')
            ),
            elapsed_seconds=round(
                time.monotonic()-started,2
            )
        )

        result['status'] = assess(result)
        save(root,result)
        return code

    except Exception as exc:
        result['hold'] = (
            'RUN_'+type(exc).__name__
        )
        save(root,result)
        return 2


def parent(root,seconds):
    run_id = str(uuid.uuid4())

    command = [
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
            command,
            cwd=root,
            env=clean_env(os.environ),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        def read_filtered():
            for line in proc.stdout:
                if line.startswith('[ORACLE017_PULSE]'):
                    print(line.rstrip(),flush=True)

        reader = threading.Thread(
            target=read_filtered,
            daemon=True
        )
        reader.start()

        code = proc.wait(
            timeout=seconds+120
        )
        reader.join(timeout=3)

        data = json.loads(
            (root/REPORT).read_text(
                encoding='utf-8'
            )
        )

        if data.get('run_id') != run_id:
            raise RuntimeError('STALE_RUN_REPORT')

        for key in (
            'status',
            'hold',
            'scanner',
            'shard_sizes',
            'ws_error_category',
            'ready',
            'priced_events',
            'evaluations',
            'best_quotes',
            'rpc_requests',
            'rpc_by_method',
            'simulations',
            'holds'
        ):
            if key in data:
                print(
                    '['+key.upper()+']',
                    json.dumps(data[key])
                )

        print(
            '[SCANNER] ORIGINAL '
            '[RPC_MAX] 80 '
            '[SIM_MAX] 1 '
            '[SIGNING] FALSE '
            '[BROADCAST] FALSE '
            '[CANARY] UNSENT'
        )

        print('[REPORT]',root/REPORT)
        return code

    except KeyboardInterrupt:
        print('[HOLD] USER_STOPPED')
        return 130

    except Exception as exc:
        print(
            '[HOLD] SESSION_'
            +type(exc).__name__
        )
        return 2

    finally:
        if proc is not None and proc.poll() is None:
            proc.kill()
            proc.wait(timeout=5)


class Tests(unittest.TestCase):

    def test_secret_scrub(self):
        self.assertEqual(
            clean_env({
                'PATH':'a',
                'QSB_SOLANA_PRIVATE_KEY':'x'
            }),
            {'PATH':'a'}
        )

    def test_rpc_ws_retained(self):
        self.assertEqual(
            clean_env({
                'SOLANA_RPC_URL':'a',
                'SOLANA_WS_URL':'b'
            }),
            {
                'SOLANA_RPC_URL':'a',
                'SOLANA_WS_URL':'b'
            }
        )

    def test_no_preflight(self):
        import inspect
        self.assertNotIn(
            'ws_preflight',
            inspect.getsource(child)
        )

    def test_connection_hold(self):
        self.assertEqual(
            assess({
                'scanner':{'acks':0}
            }),
            'HOLD_SCANNER_NOT_CONNECTED'
        )

    def test_incomplete_subscriptions(self):
        self.assertEqual(
            assess({
                'scanner':{'acks':1},
                'shard_sizes':[2]
            }),
            'HOLD_INCOMPLETE_SUBSCRIPTIONS'
        )

    def test_two_directions(self):
        record = {
            'scanner':{
                'acks':3,
                'notifications':10
            },
            'shard_sizes':[3],
            'ready':4,
            'priced_events':9,
            'evaluations':{
                'PUMP_TO_METEORA':4,
                'METEORA_TO_PUMP':4
            }
        }

        self.assertEqual(
            assess(record),
            'SCANNER_ACTIVE_EXECUTION_UNCERTIFIED'
        )

        self.assertEqual(
            assess(dict(
                record,
                evaluations={
                    'PUMP_TO_METEORA':4
                }
            )),
            'HOLD_DIRECTION_NOT_PRICED'
        )

    def test_guard(self):
        self.assertEqual(
            assess({
                'rpc_requests':81
            }),
            'HOLD_BUDGET_BREACH'
        )

    def test_classification_no_url(self):
        self.assertEqual(
            classify_error(
                'connection timeout api-key=secret'
            ),
            'TIMEOUT'
        )

    def test_canary_and_identity(self):
        self.assertEqual(
            VERSION,
            'ORACLE_017B_DIRECT_SCANNER_GUARDED_SESSION'
        )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--test',action='store_true')
    parser.add_argument('--run',action='store_true')
    parser.add_argument('--child',action='store_true')
    parser.add_argument('--seconds',type=int,default=60)
    parser.add_argument('--run-id',default='')

    args = parser.parse_args()
    root = Path.cwd()

    if args.test:
        tests = unittest.TextTestRunner(
            verbosity=2
        ).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(
                Tests
            )
        )
        return 0 if tests.wasSuccessful() else 1

    if args.child:
        return child(
            root,args.seconds,args.run_id
        )

    if args.run:
        if not 45 <= args.seconds <= 120:
            print(
                '[HOLD] SESSION_BOUNDS_45_TO_120_SECONDS'
            )
            return 2

        return parent(
            root,args.seconds
        )

    dest = root/PACKAGE/TARGET

    if not dest.parent.is_dir():
        print('[FAIL] EXECUTOR_DIRECTORY_MISSING')
        return 2

    if dest.resolve() != Path(__file__).resolve():
        shutil.copyfile(
            Path(__file__).resolve(),
            dest
        )

    print('[PASS]',VERSION,dest)
    print(
        '[MODE] NO_EXTRA_PREFLIGHT; '
        'ORIGINAL_SCANNER; ONE_GUARDED_STARTUP'
    )
    print(
        '[RPC_MAX] 80 '
        '[SIM_MAX] 1 '
        '[SIGNING] FALSE '
        '[BROADCAST] FALSE'
    )

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
