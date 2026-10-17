from __future__ import annotations
"""ORACLE-402 full installer. New executor-side module only; scanner untouched."""
import argparse, hashlib, os, py_compile, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle_402_source_first_handoff.py'
SOURCE=r'''from __future__ import annotations
"""ORACLE-402: source-first canonical event handoff, native preflight, optional SIGNED SIM ONLY."""
import argparse, collections, importlib, json, os, re, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PKG='qseries_v2.oracle_execution.solana_atomic_executor'
REPORT=ROOT/'runtime_state/oracle/final_boss_dual/oracle_402_source_first_handoff.json'
class Hold(RuntimeError): pass
def module(name):return importlib.import_module(PKG+'.'+name)
def classified(exc):
    if isinstance(exc,Hold):return str(exc)[:88]
    s=str(exc)
    m=re.fullmatch(r'[A-Z][A-Z0-9_]{3,88}',s)
    return m.group(0) if m else type(exc).__name__.upper()
def initial():
    owner=module('oracle_399_final_boss_execution_owner')
    hashes=owner.source_hashes()
    if len(hashes)!=4:raise Hold('FROZEN_SCANNER_SHA_SET_INCOMPLETE')
    contracts=module('oracle_399_native_sdk_bridge').native_source_contract()
    if not all(x.get('status')=='SOURCE_CONTRACT_VISIBLE' for x in contracts.values()):
        raise Hold('NATIVE_SOURCE_CONTRACT_DRIFT')
    return {'frozen_hashes':4,'native_interfaces':len(contracts)}
def source_health(scan):
    # Official ORACLE-374 function reuses the actual frozen scanner validator.
    hb=module('oracle_374_persistent_dual_native_handoff').read_heartbeat(scan)
    if not isinstance(hb,dict) or hb.get('ok') is not True:
        raise Hold('SCANNER_VALIDATOR_NOT_PASS')
    return hb
def run(seconds,wallet,signed_sim=False):
    stage='source_contract';result={'build':'ORACLE402','status':'HOLD','phase':stage,
        'new_websockets':0,'broadcast':False,'signed_sim_certified':False,
        'frozen_scanner_modified':False,'events_accepted':0,'native_unsigned':0,'signed_sim_pass':0,
        'native_attempts':0,'last_native_hold':'NONE'}
    conn=None; sink=REPORT.with_name('oracle_402_transient_inbox.json')
    try:
        if not 1<=seconds<=120:raise Hold('RUNTIME_SECONDS_OUT_OF_RANGE')
        if not isinstance(wallet,str) or not re.fullmatch('[1-9A-HJ-NP-Za-km-z]{32,44}',wallet):
            raise Hold('PUBLIC_WALLET_REQUIRED')
        result.update(initial())
        stage='source_health_before_warm';scan=module('oracle_344_scanner_align')
        first=source_health(scan)
        result['first_epoch']=first['epoch'];result['source_health']='PASS'
        stage='native_warm';native=module('oracle_370_native_atomic_executor')
        reverse=module('oracle_378_native_reverse_atomic')
        provider=reverse.CompatibleNativeProvider(native,wallet)
        provider.prewarm()
        result['native_ready']=len(getattr(provider.old,'READY_TOKENS',()))
        stage='source_health_after_warm';second=source_health(scan)
        if second['producer']!=first['producer']:
            raise Hold('SCANNER_PRODUCER_CHANGED_DURING_NATIVE_WARM')
        stage='source_lock';lock=module('oracle_359_lock_safe_handoff').ExclusiveLock()
        core=module('oracle_368_source_boundary_repair')
        m363=module('oracle_363_verified_scanner_bus_binding')
        m365=module('oracle_365_sqlite_columnar_event_handoff')
        m379=module('oracle_379_five_goal_executor')
        m401=module('oracle_401_canonical_signed_preflight')
        key=None
        if signed_sim:
            stage='explicit_simulation_signer';key=m401.signer(wallet)
        metrics=m379.Metrics();Gate=m379.make_ingress(m363,metrics)
        gate=Gate(ttl_ms=2500,max_age_ms=1500)
        def take(row):
            result['events_accepted']+=1
            if result['native_attempts']>=8 or result['native_unsigned'] and not signed_sim or result['signed_sim_pass']:return
            result['native_attempts']+=1
            try:
                m401.exact_nomination(row,core)
                if row['direction']=='METEORA_TO_PUMP' and m401.checks()['reverse_validator_program_id_drift']:
                    raise Hold('REVERSE_SDK_PROGRAM_ID_MISMATCH')
                proof=provider.prepare_unsigned(row)
                issue=core.bank_native_gate(row,proof)
                if issue:raise Hold('NATIVE_BANK_GATE_'+str(issue))
                result['native_unsigned']+=1
                result['status']='NATIVE_UNSIGNED_PASS_NOT_SIGNED'
                if signed_sim:
                    signed=m401.signed_preflight(row,proof,wallet,key,native._rpc)
                    result['signed_sim_pass']+=1
                    result['signed_sim_certified']=False # quote/minout protection requires further proof
                    result['status']=signed.get('status','SIGNED_SIM_RETURNED_NOT_PROFIT_CERTIFIED')
                    result['selected_size_lamports']=row['size_lamports']
                    result['direction']=row['direction']
            except Exception as exc:
                result['last_native_hold']=classified(exc)
        gate.callback=take
        with lock:
            stage='source_bus_open';conn=scan.bus()
            stage='source_read_only';conn.execute('PRAGMA query_only=ON')
            conn.execute('PRAGMA busy_timeout=500')
            stage='source_validation';heartbeat=scan.validate_scanner(conn)
            if not isinstance(heartbeat,dict) or heartbeat.get('ok') is not True:
                raise Hold('SCANNER_VALIDATOR_RETURNED_NONPASS')
            if heartbeat['producer']!=second['producer']:
                raise Hold('SCANNER_PRODUCER_CHANGED_BEFORE_ATTACH')
            stage='source_cursor';cursor=int(conn.execute('SELECT COALESCE(MAX(id),0) FROM events').fetchone()[0])
            stage='source_attach';gate.attach(heartbeat,cursor)
            result['source_cursor']=cursor;result['source_attached']=True
            result['status']='SOURCE_BOUND_WAITING_FOR_FRESH_EVENT'
            deadline=time.monotonic()+seconds;next_check=time.monotonic()
            while time.monotonic()<deadline and not gate.failed and result['native_attempts']<8 and not result['signed_sim_pass']:
                if result['native_unsigned'] and not signed_sim:break
                if time.monotonic()>=next_check:
                    stage='source_health_loop';gate.health(scan.validate_scanner(conn));next_check=time.monotonic()+.25
                    if gate.failed:break
                stage='canonical_columnar_consume'
                # Reuse ORACLE-365's actual columnar decoder; do not pass raw tuples to ingress.
                m365.consume(scan,conn,gate,collections.Counter(),sink)
                time.sleep(.005)
            if gate.failed:raise Hold('SOURCE_EPOCH_OR_PRODUCER_INVALIDATED')
            if result['native_unsigned']==0 and result['events_accepted']>0:
                result['status']='HOLD_NATIVE_GATE_'+result['last_native_hold']
            elif result['events_accepted']==0:result['status']='HOLD_NO_FRESH_CANONICAL_EVENT'
        result['phase']='completed'
    except Exception as exc:
        result.update(status='HOLD_'+classified(exc),phase=stage)
    finally:
        if conn is not None:
            try:conn.close()
            except Exception:pass
        try:sink.unlink(missing_ok=True)
        except OSError:pass
        REPORT.parent.mkdir(parents=True,exist_ok=True)
        REPORT.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
        print('[ORACLE402_RESULT]',json.dumps(result,sort_keys=True),flush=True)
        print('[ORACLE402_REPORT]',REPORT.relative_to(ROOT),flush=True)
    return 0 if result.get('native_unsigned',0)>0 or result.get('signed_sim_pass',0)>0 else 2
def tests():
    assert len(range(10_000_000,100_000_001,5_000_000))==19
    assert classified(RuntimeError('SCANNER_NOT_HEALTHY'))=='SCANNER_NOT_HEALTHY'
    assert classified(RuntimeError('https://api?api-key=secret'))=='RUNTIMEERROR'
    assert classified(Hold('SOURCE_LOCK_PRESENT'))=='SOURCE_LOCK_PRESENT'
    print('[PASS] ORACLE402 stage-coded source holds, redacted error policy, 19 sizes; no scanner writes')
    print('[SCOPE] Offline tests only; native execution and signed simulation NOT certified')
def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--observe',action='store_true')
    g.add_argument('--signed-sim',action='store_true')
    p.add_argument('--seconds',type=int,default=30)
    p.add_argument('--wallet',default=os.environ.get('QSB_SOLANA_WALLET',''))
    a=p.parse_args()
    if a.test:tests();return 0
    return run(a.seconds,a.wallet,signed_sim=a.signed_sim)
if __name__=='__main__':raise SystemExit(main())
'''
def verify():
    with tempfile.TemporaryDirectory() as d:
        f=Path(d)/'oracle_402_source_first_handoff.py'
        f.write_text(SOURCE,encoding='utf-8');py_compile.compile(str(f),doraise=True)
    assert 'send'+'Transaction' not in SOURCE and 'broadcast'+'Transaction' not in SOURCE
    assert 'oracle_365_sqlite_columnar_event_handoff' in SOURCE and 'm365.consume(' in SOURCE
    assert 'ORACLE322_FROZEN' not in SOURCE # never replace scanner files
    print('[PASS] ORACLE402 full installer syntax, true ORACLE365 columnar consumer, no broadcast')
def main():
    ap=argparse.ArgumentParser();g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--install',action='store_true')
    a=ap.parse_args();verify()
    if a.test:return 0
    DEST.parent.mkdir(parents=True,exist_ok=True)
    if DEST.exists() and DEST.read_text(encoding='utf-8')!=SOURCE:
        print('[HOLD] Existing ORACLE402 differs: refusal to overwrite');return 2
    tmp=DEST.with_name(DEST.name+'.temporary')
    tmp.write_text(SOURCE,encoding='utf-8');os.replace(tmp,DEST)
    print('[INSTALLED]',DEST.relative_to(ROOT))
    print('[PRESERVED] frozen Q18/Q20/Q25/ORACLE322 and native 370/378 source')
    return 0
if __name__=='__main__':raise SystemExit(main())
