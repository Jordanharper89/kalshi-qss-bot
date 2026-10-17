"""ORACLE-129 complete installer: restore original fast event scanner, isolated
30-second replenishment, and nonblocking positive-quote handoff for guarded
executor review. Does not authorize real-money transactions.
Windows CMD: python build_oracle_129_fast_30s_positive_handoff.py
"""
from __future__ import annotations
import ast, os, pathlib, py_compile, shutil, subprocess, sys, tempfile, textwrap
ROOT=pathlib.Path.cwd()
PKG=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker'
Q20=ROOT/'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'
Q25=ROOT/'qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py'
NATIVE=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
SUP=PKG/'run_oracle126.py'

# Nonblocking observer: complete mint & pool identity, immutable snapshot slot,
# quote amount and direction. The executable can only be certified independently.
HANDOFF=textwrap.dedent('''\
import queue as _o129_queue
_o129_positive_queue = _o129_queue.Queue(maxsize=8192)
_o129_writer_started = False
_o129_dropped = 0

def _o129_positive_writer():
    import os as _os
    import json as _json
    from pathlib import Path as _Path
    p = _Path('runtime_state/oracle/oracle_live_execution/ORACLE_129_POSITIVE_CANDIDATES.jsonl')
    p.parent.mkdir(parents=True, exist_ok=True)
    while True:
        row = _o129_positive_queue.get()
        try:
            # Append-only research feed; never store credentials, never sign.
            with p.open('a', encoding='utf-8') as f:
                f.write(_json.dumps(row, sort_keys=True, default=str) + '\\n')
        finally:
            _o129_positive_queue.task_done()

def _o129_start_writer():
    global _o129_writer_started
    if not _o129_writer_started:
        import threading as _threading
        _threading.Thread(target=_o129_positive_writer, name='oracle129-positive-writer', daemon=True).start()
        _o129_writer_started = True

def _o129_offer(token, snap, slot, received_ns, best):
    global _o129_dropped
    import time as _time
    if int(best.get('local_net', 0)) <= 0:
        return
    age_ms = max(0.0, (_time.perf_counter_ns() - received_ns) / 1e6)
    if age_ms > MAX_START_AGE_MS:
        return
    row = {
        'revision': 'ORACLE-129', 'token': str(token),
        'pump_pool': str(snap.get('pump_pool', '')),
        'meteora_pool': str((snap.get('meteora') or {}).get('address', '')),
        'slot': int(slot), 'direction': str(best.get('direction', '')),
        'size_sol': float(best.get('size_sol', 0)),
        'quoted_local_net_lamports': int(best.get('local_net', 0)),
        'quoted_local_bps': float(best.get('local_bps', 0)),
        'captured_unix': _time.time(), 'age_ms': age_ms,
        'status': 'PRELIMINARY_ONLY_REQUIRES_ATOMIC_SIGNED_SIMULATION',
        'signing': False, 'broadcast': False,
    }
    if abs(row['size_sol'] - 0.010) > 1e-10:
        return
    try:
        _o129_positive_queue.put_nowait(row)
    except _o129_queue.Full:
        _o129_dropped += 1
        print('[ORACLE129_QUEUE_FULL] positives_dropped=%d' % _o129_dropped, flush=True)
''')
OFFER='''        if int(best["local_net"])>0:
            self.positive+=1
            _o129_offer(token,snap,slot,received_ns,best)'''

# All background discovery jobs live in a separate OS process, so their RPC
# latency, API throttling, and 429s cannot block the market-event pricing lane.
REPLENISH=textwrap.dedent('''\
"""ORACLE-129 background auxiliary replenisher: startup + 30 s cadence."""
from __future__ import annotations
import argparse, json, os, subprocess, sys, time
from pathlib import Path
ROOT=Path.cwd()
MODULES=[
 'qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_045b_evidence_window_hotset_lifecycle',
 'qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_071_continuous_mriya_replenishment',
]
DISCOVERY=''' + repr('''from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.mriya_python_paper_arb.crosslisted import crosslisted
import json,os,time
pump,pairs=crosslisted(Path.cwd(),capture_seconds=5,max_intersections=56)
rows=[]
for p in pairs:
    m=p.get("meteora") or {}
    if p.get("token") and p.get("pump_pool") and m.get("address"):
        rows.append({"token":p["token"],"pump_pool":p["pump_pool"],"meteora_pool":m["address"],"pump_activity":p.get("pump_activity",0),"observed_unix":time.time()})
f=Path("runtime_state/oracle/oracle_live_execution/ORACLE_122_UNIVERSAL_DISCOVERY.json")
f.parent.mkdir(parents=True,exist_ok=True)
t=f.with_suffix(".tmp")
t.write_text(json.dumps({"rows":rows,"observed_unix":time.time(),"pump_active_pools":pump.get("active_pools",0)},indent=2),encoding="utf-8")
os.replace(t,f)
print("[UNIVERSAL] active_pump_pools=%d crosslisted=%d"%(pump.get("active_pools",0),len(rows)),flush=True)
''') + '''
REPORT=ROOT/'runtime_state/oracle/oracle_live_execution/ORACLE_129_REPLENISH.json'
def clean_env():
    e=os.environ.copy()
    for k in list(e):
        if any(s in k.upper() for s in ('PRIVATE_KEY','SECRET_KEY','MNEMONIC','SEED_PHRASE')):
            del e[k]
    e['ORACLE_EXECUTION_AUTHORITY']='FALSE'
    return e

def cycle():
    env=clean_env(); records=[]
    for cmd in [[sys.executable,'-m',m] for m in MODULES]+[[sys.executable,'-c',DISCOVERY]]:
        name=cmd[2] if cmd[1]=='-m' else 'universal_crosslist'
        try:
            # Cap subprocess cost; timeout is reported and not counted as success.
            p=subprocess.run(cmd,cwd=ROOT,env=env,timeout=25,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            lines=p.stdout.splitlines()
            for s in lines[-5:]:
                if s.startswith(('[UNIVERSAL]','[REPLENISH]','[MRIYA_HOTSET]','[LIFECYCLE_COUNTS]','[WARM_SKIP]')):
                    print(s,flush=True)
            result={'job':name,'returncode':p.returncode,'seconds_limit':25,'rate_limited':any('429' in s for s in lines)}
        except subprocess.TimeoutExpired:
            result={'job':name,'returncode':None,'timeout':True}
        except Exception as ex:
            result={'job':name,'error':type(ex).__name__}
        records.append(result)
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    tmp=REPORT.with_suffix('.tmp')
    tmp.write_text(json.dumps({'revision':'ORACLE-129','completed_unix':time.time(),'jobs':records,'pricing_lane_separate':True,'live_hot_cutover_certified':False},indent=2),encoding='utf8')
    os.replace(tmp,REPORT)
    print('[REPLENISH_129] jobs=%s'%[(x['job'].split('.')[-1],x.get('returncode')) for x in records],flush=True)
    return records

def main():
    p=argparse.ArgumentParser();p.add_argument('--once',action='store_true');a=p.parse_args()
    while True:
        start=time.monotonic()
        cycle()
        if a.once:return 0
        # 30 s target between starts; slow cycles cannot overlap.
        time.sleep(max(0,30-(time.monotonic()-start)))
if __name__=='__main__':raise SystemExit(main())
''')

# Wrapper keeps the repo's existing ORACLE-126 fast process and Mriya supervision.
# It swaps the expensive 180-second auxiliary loop for our independent worker.
def supervisor_replace(src):
    original='''    helper=threading.Thread(target=discover_loop,args=(env,),daemon=True)
    helper.start()'''
    replacement='''    # ORACLE-129: independent, 30-second bounded replenishment OS process.
    # Does not block Q25/Q20 and never accesses signing credentials.
    helper=launch([sys.executable, str(ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle129_replenish.py')],env)
    print('[REPLENISH_129] separate_process=True target_period_seconds=30',flush=True)'''
    if replacement in src:return src
    if src.count(original)!=1:raise RuntimeError('HOLD_UNKNOWN_SUPERVISOR_LAUNCH_SURFACE')
    return src.replace(original,replacement)

def q20_replace(src):
    marker='''        if int(best["local_net"])>0:
            self.positive+=1'''
    if OFFER in src:return src
    if src.count(marker)!=1:raise RuntimeError('HOLD_UNKNOWN_Q20_POSITIVE_SEAM')
    if src.count('persistent=q19.persistent')!=1:raise RuntimeError('HOLD_UNKNOWN_Q20_IMPORT_SURFACE')
    if src.count('def _o129_offer('):raise RuntimeError('HOLD_PARTIAL_129')
    src=src.replace('persistent=q19.persistent',HANDOFF+'\npersistent=q19.persistent')
    src=src.replace(marker,OFFER)
    src=src.replace('''    lane=install()
''','''    _o129_start_writer()
    lane=install()
''')
    return src

def analyze(src):
    t=ast.parse(src); names={}
    for n in t.body:
        if isinstance(n,ast.Assign):
            for x in n.targets:
                if isinstance(x,ast.Name) and x.id in ('FAST_SIZES','EXPAND_SIZES','PREFERRED_SIZE_SOL'):
                    try:names[x.id]=ast.literal_eval(n.value)
                    except (ValueError,TypeError):names[x.id]='dynamic'
    return names

def run_tests():
    fixture='''persistent=q19.persistent
    lane=install()
        if int(best["local_net"])>0:
            self.positive+=1'''
    # Valid fixtures reflect positional seams, not necessarily parsable modules.
    new=q20_replace(fixture)
    assert new.count('def _o129_offer(')==1
    assert q20_replace(new)==new
    assert supervisor_replace('    helper=threading.Thread(target=discover_loop,args=(env,),daemon=True)\n    helper.start()').count('oracle129_replenish.py')==1
    assert 'put_nowait' in HANDOFF and 'status' in HANDOFF
    assert 'time.sleep(max(0,30-' in REPLENISH
    assert 'PRIVATE_KEY' in REPLENISH and 'ORACLE_EXECUTION_AUTHORITY' in REPLENISH
    ast.parse(HANDOFF);ast.parse(REPLENISH)
    print('[PASS] ORACLE129 deterministic handoff/cadence/secret-isolation/idempotence tests')

def install():
    run_tests()
    for p in (Q20,Q25,NATIVE,SUP):
        if not p.exists():raise SystemExit('[HOLD] Missing original module '+str(p))
    nsrc=NATIVE.read_text(encoding='utf-8')
    if 'EXECUTION_AUTHORITY=False' not in nsrc and 'EXECUTION_AUTHORITY = False' not in nsrc:
        raise SystemExit('[HOLD] Expected uncertified executor guard absent; manual review required')
    old_q=Q20.read_text(encoding='utf-8');old_sup=SUP.read_text(encoding='utf-8')
    vals=analyze(old_q)
    if vals.get('FAST_SIZES')!=(0.010,) or vals.get('EXPAND_SIZES')!=() or vals.get('PREFERRED_SIZE_SOL')!=0.010:
        raise SystemExit('[HOLD] ORACLE128 size=0.010 only not certified: '+str(vals))
    q=q20_replace(old_q);sup=supervisor_replace(old_sup)
    files={Q20:q,SUP:sup,PKG/'oracle129_replenish.py':REPLENISH}
    old={p:p.read_bytes() if p.exists() else None for p in files}
    for path,contents in files.items():ast.parse(contents)
    try:
        for p,contents in files.items():
            if old[p] is not None and p.read_text(encoding='utf-8')!=contents:
                backup=p.with_suffix(p.suffix+'.ORACLE129.preinstall.bak')
                if not backup.exists():shutil.copy2(p,backup)
            p.write_text(contents,encoding='utf-8',newline='\n')
            py_compile.compile(str(p),doraise=True)
        assert q20_replace(Q20.read_text(encoding='utf-8'))==Q20.read_text(encoding='utf-8')
        assert supervisor_replace(SUP.read_text(encoding='utf-8'))==SUP.read_text(encoding='utf-8')
        print('[PASS] ORACLE-129 installed; original Q25/Q20 WebSocket price loop preserved')
        print('[REPLENISH] independent process: target 30 s between cycle starts, bounded work/no overlaps')
        print('[POSITIVES] every positive 0.010 SOL local quote sent to nonblocking, append-only verification feed')
        print('[HOLD] Original native executor is unverified; quote alone cannot broadcast or guarantee profit')
        print('[GUARDS] PRIVATE_KEY_NOT_USED; SIGNING=FALSE; BROADCAST=FALSE')
        print('[RUN] python oracle120_credentials.py --run')
    except BaseException:
        for p,data in old.items():
            if data is None:p.unlink(missing_ok=True)
            else:p.write_bytes(data)
        raise
if __name__=='__main__':install()
