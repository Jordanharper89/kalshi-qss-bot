"""Disarmed direct Swap2 test. Does not invoke scanner or send transactions."""
import argparse, json, os
from pathlib import Path
from . import runtime as r
from . import oracle181_direct_swap2_certification as q181
OUT=Path('runtime_state/oracle/oracle_live_execution/ORACLE186_DIRECT_RESULTS.json')
DIRECTIONS=('METEORA_TO_PUMP','PUMP_TO_METEORA')
def restricted_rpc_factory(original):
    def guarded(method,*args,**kwargs):
        name=str(method)
        low=name.lower()
        if low.startswith('send') or low in ('requestairdrop','simulatebundle','gettransactionconfirmation'):
            raise RuntimeError('ORACLE185_BROADCAST_FORBIDDEN')
        return original(method,*args,**kwargs)  # CRITICAL: original case preserved
    return guarded
def safety():
    if os.getenv('QSB_LIVE_ARM','').upper()=='YES':
        raise RuntimeError('ORACLE185_ARMED_ENVIRONMENT')
    src=Path(r.__file__).read_text(encoding='utf-8')
    for marker in ('ORACLE180_SWAP2_BIN_ARRAY_CORRECTION',
                   'ORACLE179_NORMALIZED_SIM_VERDICT',
                   'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED'):
        if marker not in src:raise RuntimeError('ORACLE185_MISSING_GUARD_'+marker)
    armed=getattr(r,'_live_010_armed',None)
    if not callable(armed) or armed():raise RuntimeError('ORACLE185_NOT_DISARMED')
def bootstrap():
    account=r.q87.c.rpc('getAccountInfo',
        ['11111111111111111111111111111111',{'encoding':'base64'}])
    if not isinstance(account,dict) or not isinstance(account.get('value'),dict):
        raise RuntimeError('ORACLE185_RPC_PREFLIGHT_FAILED')
    print('[ORACLE185_RPC_CASE_PASS] getAccountInfo accepted',flush=True)
    state,_=r.q25.prepare_once(Path.cwd())
    r.q25.bind_cached_state(state)
    warmed=r.install_proven_hot_math(state)
    _,user=r.q87.c.sim_identity()
    if not user:raise RuntimeError('ORACLE185_WALLET_NOT_AVAILABLE')
    r.USER=user
    r.prebuild_templates(state,user)
    r.prebuild_meteora_templates(state,user,warmed)
    pairs=[]
    for pair in state.get('pairs',[]):
        if str(pair.token) not in r.READY_TOKENS:continue
        try:
            r.q18.worker().warm(str(pair.pump_pool))
            pairs.append(pair)
        except Exception as exc:
            print('[ORACLE185_WARM_HOLD]',str(pair.token)[:10],type(exc).__name__,flush=True)
    if not pairs:raise RuntimeError('ORACLE185_NO_READY_PAIRS')
    r.BLOCKHASH.refresh()
    return pairs,user
def run(max_pairs=11):
    safety()
    old=r.q87.c.rpc
    r.q87.c.rpc=restricted_rpc_factory(old)
    rows=[];completed=set();status='HOLD';reason=None
    try:
        pairs,user=bootstrap()
        for pair in pairs[:max_pairs]:
            token=str(pair.token)
            try:
                snap=r.immutable_snapshot(pair)
                quotes=r.q18.exact_snapshot_opportunities(snap,0.050)
            except Exception as exc:
                rows.append({'token':token[:10],'stage':'QUOTE_HOLD','error':type(exc).__name__})
                continue
            for direction in DIRECTIONS:
                if direction in completed:continue
                opp=next((q for q in quotes if q.get('direction')==direction
                          and q.get('start')==50_000_000),None)
                if opp is None:continue
                row={'token':token[:10],'direction':direction,'diagnostic_only':True,'stage':'ADMISSION'}
                try:
                    safety()
                    row['stage']='ROUTE_CONSTRUCTION'
                    route=r.same_snapshot_route(user,snap,opp)
                    bound=max(1,int(opp.get('local_end',0)*0.90))
                    row['stage']='PROFIT_LOCK'
                    route,_,_=r._fast_010_profit_lock_route(route,direction,bound)
                    row['stage']='SWAP2_ACCOUNT_LAYOUT'
                    row.update(q181.inspect_route(route))
                    row['stage']='NATIVE_COMPILE'
                    compiled=r.compile_current(user,route)
                    if not isinstance(compiled,dict) or compiled.get('ok') is not True:
                        row['stage']='COMPILE_HOLD'
                        row['reason_code']='NO_LEGAL_PACKET_OR_ALT_UNAVAILABLE'
                        row['compile_reason']=str(compiled.get('reason','UNKNOWN'))[:60]
                    else:
                        raw=compiled.get('raw')
                        row['bytes']=len(raw) if isinstance(raw,(bytes,bytearray)) else None
                        if row['bytes'] is None or row['bytes']>1232 or not compiled.get('oracle176_packet_verified'):
                            raise RuntimeError('ORACLE185_PACKET_NOT_CERTIFIED')
                        safety()
                        row['stage']='SIGNED_SIMULATION'
                        sim=r.simulate_current(compiled,user)
                        verdict,units,error=q181.classify_sim(sim)
                        row.update(stage=verdict,compute_units=units,failure=error)
                    completed.add(direction)
                except Exception as exc:
                    failed_at=row['stage']
                    row.update(stage='HOLD',failed_at=failed_at,reason=type(exc).__name__)
                    import re
                    message=str(exc)
                    m=re.fullmatch(r'[A-Z][A-Z0-9_]{3,95}',message)
                    row['code']=message if m else 'ERROR_DETAIL_REDACTED'
                    print('[ORACLE186_HOLD] direction=%s at=%s code=%s type=%s' %
                          (direction,failed_at,row['code'],type(exc).__name__),flush=True)
                rows.append(row)
                print('[ORACLE186_ROUTE] direction=%s stage=%s bytes=%s reason=%s broadcast=FALSE' %
                    (direction,row['stage'],row.get('bytes'),row.get('code') or row.get('failure') or row.get('reason','NONE')),flush=True)
            if len(completed)==2:break
        status='DIRECT_DIAGNOSTIC_COMPLETED'
    except Exception as exc:
        status='HOLD_BOOTSTRAP';reason=type(exc).__name__
        print('[ORACLE186_BOOTSTRAP_HOLD]',reason,flush=True)
    finally:
        r.q87.c.rpc=old
        worker=getattr(r.q18,'_worker',None)
        if worker is not None:
            try:worker.close();r.q18._worker=None
            except Exception:pass
        report={'build':'ORACLE186','status':status,'reason':reason,'routes':rows,
                'scanner_started':False,'broadcast':False,'execution_authorized':False}
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('[ORACLE186_RESULT]',status,'routes=',len(rows),'broadcast=FALSE',flush=True)
        print('[REPORT]',OUT,flush=True)
def test():
    calls=[]
    wrapped=restricted_rpc_factory(lambda name,*a,**kw:calls.append(name) or {'value':{}})
    wrapped('getAccountInfo',[])
    wrapped('getRecentPrioritizationFees',[])
    assert calls==['getAccountInfo','getRecentPrioritizationFees']
    try:wrapped('sendTransaction',[])
    except RuntimeError:pass
    else:raise AssertionError('send allowed')
    assert len(calls)==2
    print('[TEST PASS] ORACLE185 correct RPC case preserved, sending forbidden')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--max-pairs',type=int,default=4)
    a=p.parse_args()
    test() if a.test else run(max_pairs=max(1,min(a.max_pairs,8))) if a.run else p.error('choose --test or --run')
