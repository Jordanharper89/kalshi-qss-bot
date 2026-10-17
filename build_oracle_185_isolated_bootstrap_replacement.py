
"""ORACLE185: complete replacement standalone diagnostic; preserves Solana RPC method case."""
import argparse, ast
from pathlib import Path
ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
DEST=ROOT/'oracle185_isolated_bootstrap_replacement.py'
CODE=r'''"""Disarmed direct Swap2 test. Does not invoke scanner or send transactions."""
import argparse, json, os
from pathlib import Path
from . import runtime as r
from . import oracle181_direct_swap2_certification as q181
OUT=Path('runtime_state/oracle/oracle_live_execution/ORACLE185_DIRECT_RESULTS.json')
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
                row={'token':token[:10],'direction':direction,'diagnostic_only':True}
                try:
                    safety()
                    route=r.same_snapshot_route(user,snap,opp)
                    bound=max(1,int(opp.get('local_end',0)*0.90))
                    route,_,_=r._fast_010_profit_lock_route(route,direction,bound)
                    row.update(q181.inspect_route(route))
                    compiled=r.compile_current(user,route)
                    if not isinstance(compiled,dict) or compiled.get('ok') is not True:
                        row['stage']='COMPILE_HOLD'
                    else:
                        raw=compiled.get('raw')
                        row['bytes']=len(raw) if isinstance(raw,(bytes,bytearray)) else None
                        if row['bytes'] is None or row['bytes']>1232 or not compiled.get('oracle176_packet_verified'):
                            raise RuntimeError('ORACLE185_PACKET_NOT_CERTIFIED')
                        safety()
                        sim=r.simulate_current(compiled,user)
                        verdict,units,error=q181.classify_sim(sim)
                        row.update(stage=verdict,compute_units=units,failure=error)
                    completed.add(direction)
                except Exception as exc:
                    row.update(stage='HOLD',reason=type(exc).__name__)
                    message=str(exc)
                    if message.isascii() and message.isupper() and len(message)<100:
                        row['code']=message
                rows.append(row)
                print('[ORACLE185_ROUTE] direction=%s stage=%s bytes=%s reason=%s broadcast=FALSE' %
                    (direction,row['stage'],row.get('bytes'),row.get('code') or row.get('failure') or row.get('reason','NONE')),flush=True)
            if len(completed)==2:break
        status='DIRECT_DIAGNOSTIC_COMPLETED'
    except Exception as exc:
        status='HOLD_BOOTSTRAP';reason=type(exc).__name__
        print('[ORACLE185_BOOTSTRAP_HOLD]',reason,flush=True)
    finally:
        r.q87.c.rpc=old
        worker=getattr(r.q18,'_worker',None)
        if worker is not None:
            try:worker.close();r.q18._worker=None
            except Exception:pass
        report={'build':'ORACLE185','status':status,'reason':reason,'routes':rows,
                'scanner_started':False,'broadcast':False,'execution_authorized':False}
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('[ORACLE185_RESULT]',status,'routes=',len(rows),'broadcast=FALSE',flush=True)
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
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    test() if a.test else run() if a.run else p.error('choose --test or --run')
'''
def test():
    ast.parse(CODE)
    assert 'return original(method,*args,**kwargs)' in CODE and 'r.run(' not in CODE and 'r.serve_canonical(' not in CODE
    print('[INSTALLER TEST PASS] ORACLE185 complete isolated module parses')
def install():
    if not (ROOT/'runtime.py').is_file():raise RuntimeError('HOLD_ORACLE185_RUNTIME_MISSING')
    if not (ROOT/'oracle181_direct_swap2_certification.py').is_file():raise RuntimeError('HOLD_ORACLE185_ORACLE181_REQUIRED')
    if DEST.exists() and DEST.read_text(encoding='utf-8')!=CODE:raise RuntimeError('HOLD_ORACLE185_EXISTING_FILE_DIFFERS')
    DEST.write_text(CODE,encoding='utf-8')
    ast.parse(DEST.read_text(encoding='utf-8'))
    print('[INSTALL PASS] ORACLE185 direct route bootstrap; scanner unchanged; broadcast blocked')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true')
    a=p.parse_args();test() if a.test else install()
