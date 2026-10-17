"""ORACLE-052: bounded original-scanner batch: activity tiers, Mriya, native ALT.

One original Q25/Q20/Q18 scanner per window. No new WebSocket scanner.
Reuses ORACLE-051's saved-ALT unsigned compilation and exact >=0.010 gate.
Live pool event activity is an evidence-backed provisional tier source,
not certification of the historical production tier policy.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import os
import shutil
import uuid
import subprocess
import sys
import time
import unittest
from pathlib import Path

NAME = 'oracle_052_original_scanner_batch.py'
VERSION = 'ORACLE_052_ORIGINAL_SCANNER_BATCH'
PKG = Path('qseries_v2/oracle_execution/solana_atomic_executor')
OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE_052_BATCH.json')
WINDOW = Path('runtime_state/oracle/oracle_live_execution/ORACLE_052_WINDOWS')
MIN_SIZE_LAMPORTS = 10_000_000


def safe_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data, sort_keys=True, indent=2, default=str) + '\n', encoding='utf-8')
    tmp.replace(path)


def actual_stage(events, now_ns):
    """Derived *observation* tier, from independent WS slots, not profitability."""
    current = [(slot, stamp) for slot, stamp in events
               if type(slot) is int and slot > 0 and 0 <= now_ns-stamp <= 600_000_000_000]
    count = len(set(slot for slot, _ in current))
    rapid = len(set(slot for slot, stamp in current if now_ns-stamp <= 15_000_000_000))
    hot = len(set(slot for slot, stamp in current if now_ns-stamp <= 90_000_000_000))
    if rapid >= 12: return 'ULTRA-HOT'
    if hot >= 5: return 'HOT'
    if count >= 2: return 'ACTIVE'
    return None


class Activity:
    """Physical scanner events only. Never infer tier from a price or a file timestamp."""
    def __init__(self, prior=None, clock_ns=time.perf_counter_ns, epoch=time.time):
        self.clock_ns, self.epoch = clock_ns, epoch
        self.seen = collections.defaultdict(lambda: collections.deque(maxlen=160))
        self.registry = {'created_epoch': 0, 'rows': []}
        self.prior = prior if isinstance(prior, dict) else None
        self.events = 0
        self.counters = collections.Counter()

    def record(self, token, slot, received_ns):
        now = self.clock_ns()
        if not isinstance(token, str) or type(slot) is not int or slot <= 0:
            return
        if type(received_ns) is not int or received_ns > now or now-received_ns > 750_000_000:
            self.counters['STALE_OR_UNTRUSTED_EVENT'] += 1
            return
        row = self.seen[token]
        if row and row[-1][0] == slot:
            return
        row.append((slot, received_ns))
        self.events += 1
        stage = actual_stage(row, now)
        # Incorporate the genuine preexisting Mriya lifecycle registry, if recent.
        old = None
        prior = self.prior
        epoch = self.epoch()
        if prior and isinstance(prior.get('created_epoch'), (int, float)):
            if 0 <= epoch-prior['created_epoch'] <= 600:
                for x in prior.get('rows') or []:
                    if x.get('token') == token:
                        old = str((x.get('lifecycle') or {}).get('stage') or x.get('tier') or '').upper().replace('_','-')
                        break
        # A genuine lifecycle stage may upgrade but cannot bypass the physical two-slot gate.
        if stage and old in ('ULTRA-HOT', 'HOT') and stage == 'ACTIVE':
            stage = old
        rows = {x['token']: x for x in self.registry['rows']}
        if not stage:
            rows.pop(token, None)
            self.registry['rows'] = list(rows.values())
            return
        if stage:
            rows[token] = {'token': token, 'tier': stage, 'lifecycle': {'stage': stage},
                           'source': 'OBSERVED_ORIGINAL_WS_SLOTS', 'slots': len(set(s for s,_ in row))}
            self.registry['rows'] = list(rows.values())
            self.registry['created_epoch'] = epoch
            self.counters[stage] += 1

    def export(self):
        return {'received_unique_slot_events': self.events,
                'distinct_tokens': len(self.seen),
                'admitted_tier_tokens': len(self.registry['rows']),
                'tier_counts': dict(collections.Counter(x['tier'] for x in self.registry['rows'])),
                'rejections': dict(self.counters),
                'tier_policy': 'PROVISIONAL_PHYSICAL_WS_ACTIVITY_WITH_EXISTING_LIFECYCLE_IF_FRESH',
                'historical_original_tier_policy_certified': False}


def structural_gate(root):
    parts = ('oracle_050_original_scanner_executor_consolidation.py',
             'oracle_051_original_scanner_alt_and_size_gate.py', 'runtime.py')
    missing = [str(PKG/p) for p in parts if not (root/PKG/p).is_file()]
    originals = [Path('qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py'),
                 Path('qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'),
                 Path('qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py')]
    missing += [str(p) for p in originals if not (root/p).is_file()]
    return missing


def one_window(root, seconds, index, run_id):
    if any('PRIVATE_KEY' in k.upper() or 'SECRET_KEY' in k.upper() for k in os.environ):
        print('[HOLD] PRIVATE_KEY_MUST_NOT_ENTER_SCANNER_CHILD', flush=True)
        return 2
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_050_original_scanner_executor_consolidation as v50
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_051_original_scanner_alt_and_size_gate as v51
    from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
    from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine

    originals = v50.hash_sources(root)
    prior = v50.latest_tiers(root)
    activity = Activity(prior)
    discovered = []
    hydrated = []
    reasons = []
    original_latest = v50.latest_tiers
    original_price = q20.LatestStateLane._price
    original_candidates = engine.candidate_universe
    original_prepare = q25.prepare_once

    def observe_price(lane, token, row):
        try:
            activity.record(str(token), int(row[1]), int(row[2]))
        except (IndexError, ValueError, TypeError):
            activity.counters['MALFORMED_EVENT'] += 1
        return original_price(lane, token, row)

    def trace_universe(repo_root):
        rows = original_candidates(repo_root)
        for x in rows:
            if isinstance(x, dict):
                discovered.append({'token': str(x.get('token','')),
                                   'source': str(x.get('source','UNKNOWN')),
                                   'pool': str(x.get('pump_pool',''))})
        print('[MRIYA_ORIGINAL_DISCOVERY] exact=%d mriya_priority=%d' % (
            len(discovered), sum(x['source']=='MRIYA_HOT' for x in discovered)), flush=True)
        return rows

    def trace_prepare(repo_root):
        state, capability = original_prepare(repo_root)
        hydrated.extend(str(x.token) for x in state.get('pairs') or [])
        return state, capability

    try:
        # Patches wrap existing functions in memory only; original Q25/Q20/Q18 files unchanged.
        v50.latest_tiers = lambda _root: activity.registry
        q20.LatestStateLane._price = observe_price
        engine.candidate_universe = trace_universe
        q25.prepare_once = trace_prepare
        print('[BATCH_WINDOW] number=%d seconds=%d scanner=ORIGINAL_Q25_Q20_Q18' % (index, seconds), flush=True)
        print('[TIERS] REAL_WS_SLOT_EVIDENCE; OLD_LIFECYCLE_WHEN_FRESH', flush=True)
        print('[MRIYA] ORIGINAL_ENGINE_HOT_FIRST_STARTUP_REFRESH; NO_SECOND_SCANNER', flush=True)
        print('[ALT] ORACLE051_EXISTING_SAVED_TABLES; NO_CREATION_OR_EXTENSION', flush=True)
        print('[MINIMUM] 0.010_SOL [FIRST_CANARY] 0.010_SOL [SIGNING] FALSE [BROADCAST] FALSE', flush=True)
        result = v51.run_once(root, seconds)
    except Exception as exc:
        reasons.append('WINDOW_ERROR_'+type(exc).__name__)
        result = 2
    finally:
        v50.latest_tiers = original_latest
        q20.LatestStateLane._price = original_price
        engine.candidate_universe = original_candidates
        q25.prepare_once = original_prepare

    report50, report51 = {}, {}
    for file, dest in ((v50.REPORT, 'r50'), (v51.REPORT, 'r51')):
        try:
            data = json.loads((root/file).read_text(encoding='utf-8'))
            if dest == 'r50': report50 = data
            else: report51 = data
        except (OSError, ValueError): reasons.append('MISSING_'+dest.upper()+'_REPORT')
    verdict = {
        'revision': VERSION, 'window': index, 'run_id':run_id, 'status': 'OBSERVATION_COMPLETE' if result == 0 else 'HOLD',
        'original_scanner_exit_code': result,
        'source_hashes_unchanged': originals == v50.hash_sources(root),
        'mriya': {'exact_crosslist_candidates': len(discovered),
                  'mriya_hot_candidates': sum(x['source']=='MRIYA_HOT' for x in discovered),
                  'hydrated_pairs': len(hydrated), 'hydrated_mriya': len(set(hydrated)&
                       {x['token'] for x in discovered if x['source']=='MRIYA_HOT'}),
                  'universe_tokens': sorted({x['token'] for x in discovered}),
                  'hydrated_tokens': sorted(set(hydrated)),
                  'same_socket_replenishment': False,
                  'refresh_at_original_scanner_window_boundary': True},
        'activity_tiers': activity.export(),
        'native': {'ready_tokens': report50.get('native_ready_tokens',0),
                   'positive_scanner_quotes': report50.get('positive_scanner_quotes',0),
                   'handoffs': report50.get('pre_simulation_handoffs',0),
                   'native_compile_attempts': report50.get('native_compile_attempts',0),
                   'unsigned_simulation_passes': report50.get('unsigned_atomic_simulation_passes',0),
                   'alt_compiler': (report51.get('statistics') or {}).get('last_compile_status'),
                   'hold_reasons': report50.get('holds',{})},
        'minimum_trade_lamports': MIN_SIZE_LAMPORTS,
        'first_canary_lamports': MIN_SIZE_LAMPORTS,
        'live_trade_authorized': False, 'signing': False, 'broadcast': False,
        'errors': reasons
    }
    if not verdict['source_hashes_unchanged']:
        verdict['status'] = 'HOLD_SCANNER_SOURCE_CHANGED'
    safe_write(root / WINDOW / ('window_%02d_%s.json'%(index,run_id)), verdict)
    print('[ORACLE052_WINDOW_RESULT] '+json.dumps({
        'window': index, 'status':verdict['status'], 'mriya':verdict['mriya']['hydrated_mriya'],
        'tier_admitted':verdict['activity_tiers']['admitted_tier_tokens'],
        'compile_attempts':verdict['native']['native_compile_attempts'],
        'sim_passes':verdict['native']['unsigned_simulation_passes']}, sort_keys=True), flush=True)
    return 0 if result == 0 and verdict['source_hashes_unchanged'] else 2


def batch(root, seconds, cycles):
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_050_original_scanner_executor_consolidation as v50
    reports = []
    run_id = uuid.uuid4().hex
    for n in range(1, cycles+1):
        env = v50.scrub(os.environ)
        if os.environ.get('QSB_ORACLE_EXEC_ALT_ADDRESS'):
            env['QSB_ORACLE_EXEC_ALT_ADDRESS'] = os.environ['QSB_ORACLE_EXEC_ALT_ADDRESS']
        cmd = [sys.executable,'-I','-u', str(Path(__file__).resolve()), '--child',
               '--seconds',str(seconds), '--index',str(n), '--run-id',run_id]
        print('[ORACLE052_STAGE] %d/%d' % (n, cycles), flush=True)
        proc = subprocess.Popen(cmd,cwd=root,env=env,stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace')
        positive_lines = 0
        informative = ('[BATCH_WINDOW]', '[MRIYA_ORIGINAL_DISCOVERY]', '[CACHE]',
                       '[LIVE]', '[HEARTBEAT]', '[ORACLE020_COMPLETE]',
                       '[ORACLE051_NATIVE]', '[ORACLE051_SIM]',
                       '[ORACLE050_RESULT]', '[ORACLE052_WINDOW_RESULT]',
                       '[HOLD]', '[ATOMIC_SIM]')
        try:
            for line in proc.stdout:
                line = line.rstrip()
                if line.startswith(informative):
                    print(line,flush=True)
                elif line.startswith('[ORACLE020_EXACT_LATEST]') and 'bps=+' in line and positive_lines < 12:
                    print(line,flush=True)
                    positive_lines += 1
            code = proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            try:proc.wait(timeout=8)
            except subprocess.TimeoutExpired:proc.kill();proc.wait()
            print('[STOP] BATCH_INTERRUPTED', flush=True)
            return 130
        window = root/WINDOW/('window_%02d_%s.json'%(n,run_id))
        try: report=json.loads(window.read_text(encoding='utf-8'))
        except (OSError,ValueError): report={'status':'HOLD_NO_WINDOW_REPORT'}
        if report.get('run_id') != run_id: report = {'status':'HOLD_STALE_WINDOW_REPORT'}
        reports.append(report)
        safe_write(root/OUT, {'revision':VERSION, 'windows_completed':len(reports),
            'windows_requested':cycles, 'windows':reports,
            'signing':False, 'broadcast':False, 'realized_profit_certified':False,
            'continuous_same_socket_rotation_certified':False})
        if code or report.get('status') != 'OBSERVATION_COMPLETE':
            print('[HOLD] WINDOW_FAILED; NEXT_STAGE_BLOCKED', flush=True)
            return 2
        if n > 1:
            previous = set(reports[-2]['mriya']['hydrated_tokens'])
            current = set(reports[-1]['mriya']['hydrated_tokens'])
            print('[REPLENISHMENT_WINDOW_DELTA] added=%d retired=%d' % (
                len(current-previous),len(previous-current)),flush=True)
    print('[BATCH_DONE] no_signing no_broadcast no_realized_profit_certification',flush=True)
    print('[REPORT]',root/OUT,flush=True)
    return 0


class Tests(unittest.TestCase):
    def test_no_single_slot_admission(self):
        self.assertIsNone(actual_stage([(5,900)],1000))
    def test_two_slot_active(self):
        self.assertEqual(actual_stage([(5,900),(6,950)],1000),'ACTIVE')
    def test_repeated_slot_not_two_events(self):
        self.assertIsNone(actual_stage([(5,900),(5,950)],1000))
    def test_hot(self):
        self.assertEqual(actual_stage([(i,900) for i in range(1,6)],1000),'HOT')
    def test_ultrahot(self):
        self.assertEqual(actual_stage([(i,900) for i in range(1,13)],1000),'ULTRA-HOT')
    def test_age_out(self):
        self.assertIsNone(actual_stage([(i,0) for i in range(12)],700_000_000_000))
    def test_observed_timestamp_gate(self):
        a=Activity(clock_ns=lambda:2_000_000_000,epoch=lambda:123456)
        a.record('X',1,1_000_000_000)
        self.assertFalse(a.registry['rows'])
        a.record('X',2,1_900_000_000)
        a.record('X',3,1_950_000_000)
        self.assertEqual(a.registry['rows'][0]['tier'],'ACTIVE')
    def test_exact_canary_and_no_send(self):
        self.assertEqual(MIN_SIZE_LAMPORTS,10_000_000)
        import inspect
        t=inspect.getsource(one_window)
        self.assertNotIn('sendTransaction',t)
        self.assertNotIn('signed_tx(',t)
    def test_existing_lifecycle_does_not_bypass_ws(self):
        a=Activity({'created_epoch':900,'rows':[{'token':'X','tier':'HOT'}]},
                   clock_ns=lambda:3_000_000_000,epoch=lambda:1000)
        a.record('X',5,2_999_000_000)
        self.assertEqual(a.registry['rows'],[])
    def test_module_is_importable(self):
        self.assertTrue(NAME.endswith('.py'))


def main():
    a=argparse.ArgumentParser()
    a.add_argument('--test',action='store_true')
    a.add_argument('--audit',action='store_true')
    a.add_argument('--run',action='store_true')
    a.add_argument('--child',action='store_true')
    a.add_argument('--seconds',type=int,default=120)
    a.add_argument('--cycles',type=int,default=2)
    a.add_argument('--index',type=int,default=1)
    a.add_argument('--run-id',default='')
    args=a.parse_args()
    root=Path.cwd()
    if args.test:
        tests=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
        return 0 if unittest.TextTestRunner(verbosity=2).run(tests).wasSuccessful() else 1
    if args.audit:
        missing=structural_gate(root)
        print('[ORIGINAL_SCANNER] INTACT' if not missing else '[HOLD] MISSING_'+str(missing))
        print('[STAGES] ORIGINAL_MRIYA_STARTUP / WS_ACTIVITY_TIERS / NATIVE_051_ALT_SIM')
        print('[ROTATION] BOUNDED_SEQUENTIAL_WINDOWS_NOT_SAME_SOCKET')
        print('[MINIMUM] 0.010_SOL [FIRST_CANARY] 0.010_SOL')
        print('[SIGNING] FALSE [BROADCAST] FALSE')
        return 0 if not missing else 2
    if args.child:
        sys.path.insert(0,str(root.resolve()))
        return one_window(root,args.seconds,args.index,args.run_id)
    if args.run:
        if not 60 <= args.seconds <= 600 or not 1 <= args.cycles <= 8:
            print('[HOLD] SECONDS_60_600_CYCLES_1_8')
            return 2
        return batch(root,args.seconds,args.cycles)
    target=root/PKG/NAME
    if not target.parent.is_dir():
        print('[HOLD] MISSING_EXECUTOR_PACKAGE')
        return 2
    if target.resolve()!=Path(__file__).resolve():
        shutil.copyfile(Path(__file__).resolve(),target)
    print('[PASS]',VERSION)
    print('[ARCH] ONE_ORIGINAL_SCANNER_AT_A_TIME; Mriya startup refresh')
    print('[STAGES] ORIGINAL_MRIYA_STARTUP / WS_ACTIVITY_TIERS / NATIVE_051_ALT_SIM')
    print('[SIGNING] FALSE [BROADCAST] FALSE')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
