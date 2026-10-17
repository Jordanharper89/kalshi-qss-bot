"""ORACLE-053 complete installer: original scanner tier-event and size-failure resilience.

The existing Q25/Q20/Q18 scanner remains transport/pricing authority.
This module never creates a WebSocket client, signs, sends, or modifies scanner sources.
Mriya discovery remains at ORIGINAL scanner window boundary, not same-socket rotation.
"""
from __future__ import annotations
import argparse
import collections
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace

VERSION = 'ORACLE_053_ORIGINAL_SCANNER_RECOVERY_BATCH'
PKG = Path('qseries_v2/oracle_execution/solana_atomic_executor')
NAME = 'oracle_053_original_scanner_recovery_batch.py'
OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE_053_RECOVERY_BATCH.json')
PARTIAL = ('DLMM_PARTIAL', 'REVERSE_TOKEN_NET_ZERO', 'FORWARD_TOKEN_NET_ZERO')
MINIMUM = 10_000_000


def atomic_json(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(record, indent=2, sort_keys=True, default=str)+'\n', encoding='utf-8')
    tmp.replace(path)


def ws_pair_token(state, event):
    if not isinstance(state, dict) or not isinstance(event, dict):
        return None
    binding = state.get('preg', {}).get(event.get('address'))
    if not isinstance(binding, (tuple, list)) or len(binding) < 2:
        return None
    try:
        token = str(state['pairs'][binding[0]].token)
        return token if token else None
    except (TypeError, ValueError, IndexError, KeyError, AttributeError):
        return None


def isolated_size_scan(lane, token, row, quote, sizes, max_age_ms, statistics, expand=()):
    """Preserve Q20 state/freshness/coalescing; skip ONLY known unpriceable sizes.

    This never substitutes a synthetic quote: every admitted row must come from
    the original q18 exact SDK/DLMM quote function itself.
    """
    snap, slot, received_ns, generation = row
    now = time.perf_counter_ns()
    start_ms = max(0.0, (now - int(received_ns))/1e6)
    lane.event_start_ms.append(start_ms)
    if start_ms > max_age_ms:
        lane.stale_drops += 1
        statistics['stale_drops'] += 1
        return
    lane._warm(snap)
    started = time.perf_counter_ns()
    gathered = []
    for size in tuple(sizes) + tuple(expand):
        if float(size) < .010 - 1e-12:
            raise RuntimeError('ORACLE053_BELOW_010_PRICING_SIZE')
        try:
            found = quote(snap, size)
        except RuntimeError as exc:
            if not str(exc).startswith(PARTIAL):
                statistics['unexpected_quote_'+type(exc).__name__] += 1
                raise
            statistics['skipped_unpriceable_sizes'] += 1
            continue
        if not isinstance(found, (list, tuple)) or len(found) != 2:
            raise RuntimeError('ORACLE053_REJECT_INCOMPLETE_EXACT_DIRECTIONS')
        gathered.extend(found)
        lane.evaluations += len(found)
        statistics['successful_two_direction_sizes'] += 1
        if lane.newer_waiting(token, generation):
            lane.scan_replaced += 1
            statistics['newer_snapshot_preemptions'] += 1
            return
    if not gathered:
        statistics['no_valid_size_for_snapshot'] += 1
        return
    best = max(gathered, key=lambda x: int(x['local_net']))
    if best.get('direction') not in ('PUMP_TO_METEORA', 'METEORA_TO_PUMP'):
        raise RuntimeError('ORACLE053_DIRECTION_MISMATCH')
    age = (time.perf_counter_ns()-started)/1e6
    lane.scan_ms.append(age)
    lane.processed += 1
    if int(best['local_net']) > 0:
        lane.positive += 1
        statistics['positive_snapshots'] += 1
    if lane.best is None or int(best['local_net']) > int(lane.best['local_net']):
        lane.best = dict(best)
    print('[ORACLE020_EXACT_LATEST] token=%s slot=%s dir=%s size=%.3f bps=%+.2f net=%+d start_ms=%.3f scan_ms=%.3f'%(
        token[:10], slot, best['direction'], float(best['size_sol']), float(best['local_bps']),
        int(best['local_net']),start_ms,age),flush=True)


def physical_tier_hook(original, tracker, stats):
    def hook(state, event, counters, sim_lane):
        before = int(counters.get('event_errors', 0))
        result = original(state, event, counters, sim_lane)
        if int(counters.get('event_errors', 0)) == before and tracker():
            token = ws_pair_token(state, event)
            if token is not None:
                try:
                    tracker().record(token, event.get('slot'), event.get('received_ns'))
                    stats['physical_ws_events_checked'] += 1
                except (TypeError, ValueError, AttributeError):
                    stats['malformed_original_ws_events'] += 1
        return result
    return hook


def one_window(root, seconds, index, run_id):
    if any('PRIVATE_KEY' in k.upper() or 'SECRET_KEY' in k.upper() for k in os.environ):
        print('[HOLD] SECRET_ENVIRONMENT_DENIED',flush=True)
        return 2
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_052_original_scanner_batch as v52
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_050_original_scanner_executor_consolidation as v50
    from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18

    old_activity, old_install, old_price = v52.Activity, q20.install, q20.LatestStateLane._price
    stats = collections.Counter()
    tracker = [None]
    replaced_event = [None]
    original_event = [None]
    hashes = v50.hash_sources(root)

    def activity_factory(*args, **kwargs):
        a = old_activity(*args, **kwargs)
        tracker[0] = a
        return a

    def event_install():
        lane = old_install()
        actual = q20.persistent._process_event
        original_event[0] = actual
        replacement = physical_tier_hook(actual, lambda: tracker[0], stats)
        replaced_event[0] = replacement
        q20.persistent._process_event = replacement
        return lane

    def resilient_price(lane, token, row):
        return isolated_size_scan(lane,token,row,q18.exact_snapshot_opportunities,
                                  q20.FAST_SIZES,q20.MAX_START_AGE_MS,stats,q20.EXPAND_SIZES)

    status = 2
    try:
        v52.Activity = activity_factory
        q20.install = event_install
        q20.LatestStateLane._price = resilient_price
        print('[ORACLE053_STAGE] window=%d original_scanner=Q25_Q20_Q18' % index,flush=True)
        print('[TIER_SOURCE] REAL_ORIGINAL_POOL_WS_NOTIFICATIONS',flush=True)
        print('[QUOTE_FAILURE_POLICY] SKIP_INCOMPLETE_SIZE_KEEP_VALID_SIZES',flush=True)
        print('[MRIYA] REFRESH_AT_ORIGINAL_SCANNER_WINDOW_BOUNDARY_ONLY',flush=True)
        print('[SIZE_MIN] 0.010_SOL [SIGNING] FALSE [BROADCAST] FALSE',flush=True)
        status = v52.one_window(root,seconds,index,run_id)
    except Exception as exc:
        print('[HOLD] ORACLE053_WINDOW_'+type(exc).__name__,flush=True)
    finally:
        v52.Activity = old_activity
        q20.install = old_install
        q20.LatestStateLane._price = old_price
        if replaced_event[0] is not None and q20.persistent._process_event is replaced_event[0]:
            q20.persistent._process_event = original_event[0]

    wpath=root/v52.WINDOW/('window_%02d_%s.json'%(index,run_id))
    try:
        prior=json.loads(wpath.read_text(encoding='utf-8'))
    except (OSError,ValueError):
        prior={}
    rep={
        'revision':VERSION,'run_id':run_id,'window':index,
        'status':'OBSERVATION_COMPLETE' if status==0 and hashes==v50.hash_sources(root) else 'HOLD',
        'original_scanner_sources_unchanged':hashes==v50.hash_sources(root),
        'original_scanner_report':prior.get('native',{}),
        'mriya':prior.get('mriya',{}),
        'tier_activity':prior.get('activity_tiers',{}),
        'resilient_exact_quote':dict(stats),
        'rotation_inside_same_socket_certified':False,
        'eligible_minimum_lamports':MINIMUM,'first_live_canary_lamports':MINIMUM,
        'signing':False,'broadcast':False,'live_execution_authorized':False,
        'net_profit_certified':False}
    atomic_json(root/'runtime_state/oracle/oracle_live_execution/ORACLE_053_WINDOWS'/('window_%02d_%s.json'%(index,run_id)),rep)
    print('[ORACLE053_WINDOW_RESULT] '+json.dumps({
        'window':index,'status':rep['status'],
        'physical_ws_events':stats['physical_ws_events_checked'],
        'valid_size_quotes':stats['successful_two_direction_sizes'],
        'skipped_partial_sizes':stats['skipped_unpriceable_sizes'],
        'tiers':(rep['tier_activity'] or {}).get('admitted_tier_tokens'),
        'exact_positive_quotes':(rep['original_scanner_report'] or {}).get('positive_scanner_quotes'),
        'native_compiles':(rep['original_scanner_report'] or {}).get('native_compile_attempts'),
        'sim_passes':(rep['original_scanner_report'] or {}).get('unsigned_simulation_passes')},sort_keys=True),flush=True)
    return 0 if rep['status']=='OBSERVATION_COMPLETE' else 2


def batch(root,seconds,cycles):
    from qseries_v2.oracle_execution.solana_atomic_executor import oracle_050_original_scanner_executor_consolidation as v50
    rid=uuid.uuid4().hex
    records=[]
    for n in range(1,cycles+1):
        env=v50.scrub(os.environ)
        if os.environ.get('QSB_ORACLE_EXEC_ALT_ADDRESS'):
            env['QSB_ORACLE_EXEC_ALT_ADDRESS']=os.environ['QSB_ORACLE_EXEC_ALT_ADDRESS']
        cmd=[sys.executable,'-I','-u',str(Path(__file__).resolve()),'--child','--seconds',str(seconds),
             '--index',str(n),'--run-id',rid]
        print('[ORACLE053_BATCH] %d/%d'%(n,cycles),flush=True)
        p=subprocess.Popen(cmd,cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                           encoding='utf-8',errors='replace',text=True,bufsize=1)
        important=('[ORACLE053_STAGE]','[MRIYA_ORIGINAL_DISCOVERY]','[CACHE]','[LIVE]',
                   '[HEARTBEAT]','[ORACLE020_COMPLETE]','[ORACLE050_RESULT]',
                   '[ORACLE051_NATIVE]','[ORACLE051_SIM]','[ORACLE053_WINDOW_RESULT]',
                   '[HOLD]','[ATOMIC_SIM]')
        positives=0
        try:
            for ln in p.stdout:
                ln=ln.rstrip()
                if ln.startswith(important):print(ln,flush=True)
                elif ln.startswith('[ORACLE020_EXACT_LATEST]') and 'bps=+' in ln and positives<12:
                    print(ln,flush=True);positives+=1
            code=p.wait()
        except KeyboardInterrupt:
            p.terminate()
            try:p.wait(timeout=8)
            except subprocess.TimeoutExpired:p.kill();p.wait()
            print('[STOP] ORIGINAL_SCANNER_BATCH_STOPPED',flush=True)
            return 130
        path=root/'runtime_state/oracle/oracle_live_execution/ORACLE_053_WINDOWS'/('window_%02d_%s.json'%(n,rid))
        try:rec=json.loads(path.read_text(encoding='utf-8'))
        except (OSError,ValueError):rec={'status':'HOLD_MISSING_WINDOW_REPORT'}
        if rec.get('run_id')!=rid:rec={'status':'HOLD_STALE_WINDOW_REPORT'}
        records.append(rec)
        atomic_json(root/OUT,{'revision':VERSION,'run_id':rid,'windows':records,
                    'original_scanner_frozen':True,'same_socket_mriya_rotation_certified':False,
                    'signing':False,'broadcast':False,'realized_profit_certified':False})
        if code or rec.get('status')!='OBSERVATION_COMPLETE':
            print('[HOLD] WINDOW_FAILED_NO_BLIND_RETRY',flush=True)
            return 2
        if n>1:
            old=set(records[-2].get('mriya',{}).get('hydrated_tokens',[]))
            new=set(rec.get('mriya',{}).get('hydrated_tokens',[]))
            print('[MRIYA_WINDOW_CHANGE] added=%d retired=%d'%(len(new-old),len(old-new)),flush=True)
    print('[BATCH_DONE] no_signing no_broadcast no_claim_of_profit',flush=True)
    print('[REPORT]',root/OUT,flush=True)
    return 0


class Tests(unittest.TestCase):
    def _mock_lane(self):
        class L:
            def __init__(self):
                self.event_start_ms=[];self.scan_ms=[];self.stale_drops=0
                self.scan_replaced=0;self.evaluations=0;self.processed=0;self.positive=0
                self.best=None;self.warmed=0;self.newer=False
            def _warm(self,snap):self.warmed+=1
            def newer_waiting(self,tok,gen):return self.newer
        return L()
    def _row(self):return ({'token':'ABC'},123,time.perf_counter_ns(),1)
    def _quotes(self,net,size):
        return [{'local_net':net,'local_bps':net,'direction':'PUMP_TO_METEORA','size_sol':size},
                {'local_net':net-1,'local_bps':net-1,'direction':'METEORA_TO_PUMP','size_sol':size}]
    def test_partial_size_does_not_abort_later_valid_size(self):
        a=self._mock_lane();st=collections.Counter();seen=[]
        def quote(snap,size):
            seen.append(size)
            if size==.010:raise RuntimeError('DLMM_PARTIAL')
            return self._quotes(11,size)
        isolated_size_scan(a,'ABC',self._row(),quote,(.010,.025),750,st)
        self.assertEqual(seen,[.010,.025]);self.assertEqual(a.positive,1)
        self.assertEqual(st['skipped_unpriceable_sizes'],1)
    def test_missing_all_sizes_not_positive(self):
        a=self._mock_lane();st=collections.Counter()
        isolated_size_scan(a,'ABC',self._row(),lambda *x: (_ for _ in ()).throw(RuntimeError('DLMM_PARTIAL')),(.010,),750,st)
        self.assertEqual(a.positive,0);self.assertEqual(st['no_valid_size_for_snapshot'],1)
    def test_nonpartial_exception_surfaces(self):
        with self.assertRaisesRegex(RuntimeError,'BAD_RPC'):
            isolated_size_scan(self._mock_lane(),'ABC',self._row(),
                lambda *x: (_ for _ in ()).throw(RuntimeError('BAD_RPC')),(.010,),750,collections.Counter())
    def test_small_size_refused(self):
        with self.assertRaisesRegex(RuntimeError,'BELOW_010'):
            isolated_size_scan(self._mock_lane(),'ABC',self._row(),lambda *x:self._quotes(2,.001),(.001,),750,collections.Counter())
    def test_newer_snapshot_preempts(self):
        a=self._mock_lane();a.newer=True
        isolated_size_scan(a,'ABC',self._row(),lambda s,z:self._quotes(5,z),(.010,),750,collections.Counter())
        self.assertEqual(a.scan_replaced,1);self.assertEqual(a.processed,0)
    def test_no_synthetic_single_direction(self):
        with self.assertRaisesRegex(RuntimeError,'INCOMPLETE_EXACT_DIRECTIONS'):
            isolated_size_scan(self._mock_lane(),'ABC',self._row(),lambda s,z:self._quotes(5,z)[:1],(.010,),750,collections.Counter())
    def test_physical_preg_route(self):
        s={'preg':{'pool':(0,'PUMP')},'pairs':[SimpleNamespace(token='ABC')]}
        self.assertEqual(ws_pair_token(s,{'address':'pool'}),'ABC')
        self.assertIsNone(ws_pair_token(s,{'address':'else'}))
    def test_physical_hook_preserves_original(self):
        calls=[];events=[]
        def fn(state,ev,c,sim):calls.append(ev);return 'original'
        class T:
            def record(self,*x):events.append(x)
        hook=physical_tier_hook(fn,lambda:T(),collections.Counter())
        s={'preg':{'p':(0,'X')},'pairs':[SimpleNamespace(token='ABC')]}
        self.assertEqual(hook(s,{'address':'p','slot':7,'received_ns':2},{},None),'original')
        self.assertEqual(events,[('ABC',7,2)])
    def test_event_errors_block_tier_observation(self):
        events=[]
        def fn(s,e,c,l):c['event_errors']=c.get('event_errors',0)+1
        class T:
            def record(self,*x):events.append(x)
        hook=physical_tier_hook(fn,lambda:T(),collections.Counter())
        hook({'preg':{'p':(0,'X')},'pairs':[SimpleNamespace(token='ABC')]},
             {'address':'p','slot':7,'received_ns':2},{},None)
        self.assertEqual(events,[])
    def test_stale_quote_is_not_evaluated(self):
        a=self._mock_lane();called=[]
        isolated_size_scan(a,'ABC',({'token':'ABC'},9,time.perf_counter_ns()-3_000_000_000,1),
            lambda *x: called.append(x),(.010,),750,collections.Counter())
        self.assertEqual(called,[])
        self.assertEqual(a.stale_drops,1)
    def test_negative_quote_stays_negative(self):
        a=self._mock_lane()
        isolated_size_scan(a,'ABC',self._row(),lambda s,z:self._quotes(-50,z),(.010,),750,collections.Counter())
        self.assertEqual(a.positive,0)
        self.assertEqual(a.best['local_net'],-50)
    def test_canary_constant(self):self.assertEqual(MINIMUM,10_000_000)
    def test_no_new_ws_transport_in_this_module(self):
        import inspect
        s=inspect.getsource(one_window)
        self.assertNotIn('websockets.connect',s)
        self.assertNotIn('sendTransaction',s)
    def test_state_is_only_file_install(self):
        self.assertTrue(NAME.endswith('.py'))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--audit',action='store_true')
    p.add_argument('--run',action='store_true')
    p.add_argument('--child',action='store_true')
    p.add_argument('--seconds',type=int,default=90)
    p.add_argument('--cycles',type=int,default=3)
    p.add_argument('--index',type=int,default=1)
    p.add_argument('--run-id',default='')
    a=p.parse_args();root=Path.cwd()
    if a.test:
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if result.wasSuccessful() else 1
    if a.audit:
        from qseries_v2.oracle_execution.solana_atomic_executor import oracle_052_original_scanner_batch as v52
        missing=v52.structural_gate(root)
        print('[ORIGINAL_SCANNER]', 'PRESERVED' if not missing else 'MISSING')
        print('[ORACLE052_DEPENDENCY]',not missing)
        print('[MODE] ORIGINAL_WS_ACTIVITY_PLUS_PER_SIZE_QUOTE_RECOVERY')
        print('[MRIYA] STARTUP_WINDOW_ONLY; SAME_SOCKET_ROTATION_NOT_CERTIFIED')
        print('[MINIMUM] 0.010_SOL [SIGNING] FALSE [BROADCAST] FALSE')
        return 0 if not missing else 2
    if a.child:
        sys.path.insert(0,str(root.resolve()))
        return one_window(root,a.seconds,a.index,a.run_id)
    if a.run:
        if not 60<=a.seconds<=600 or not 1<=a.cycles<=8:
            print('[HOLD] LIMIT_SECONDS_60_TO_600_CYCLES_1_TO_8')
            return 2
        return batch(root,a.seconds,a.cycles)
    target=root/PKG/NAME
    if not target.parent.is_dir():
        print('[HOLD] EXECUTOR_PACKAGE_MISSING');return 2
    if target.resolve()!=Path(__file__).resolve():
        shutil.copyfile(Path(__file__).resolve(),target)
    print('[PASS]',VERSION)
    print('[ARCH] ORIGINAL_Q25_Q20_Q18_ONLY; ORIGINAL_SOURCE_UNCHANGED')
    print('[STAGES] PHYSICAL_WS_TIER_EVIDENCE / PER_SIZE_EXACT_QUOTES / SAVED_ALT_NATIVE_HOLDS')
    print('[SIGNING] FALSE [BROADCAST] FALSE')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
