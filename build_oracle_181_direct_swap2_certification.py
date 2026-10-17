
"""ORACLE181 full installer: disarmed direct warmed-route Swap2 certification."""
import argparse
import ast
from pathlib import Path

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
DEST = ROOT / 'oracle181_direct_swap2_certification.py'

CODE = r'''"""Direct 0.050 SOL two-leg signed-simulation diagnostic; NEVER broadcast."""
import argparse, asyncio, json, re, sys
from pathlib import Path
from . import runtime as r

OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE181_DIRECT_SWAP2.json')
DLMM = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
MEMO = 'MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'
DISC = bytes([65,75,63,76,235,91,91,136])

def inspect_route(route):
    import base64
    if not isinstance(route,dict) or route.get('start_lamports') != 50_000_000:
        raise RuntimeError('NOT_EXACT_050_SOL')
    original = route.get('original_candidates')
    if not isinstance(original,(list,tuple)) or not original:
        raise RuntimeError('NO_ATOMIC_CANDIDATES')
    found = 0
    for name,ixs in original:
        if not isinstance(ixs,(list,tuple)):
            raise RuntimeError('CANDIDATE_NOT_INSTRUCTION_LIST')
        meteora = [ix for ix in ixs if isinstance(ix,dict) and ix.get('programId')==DLMM]
        if len(meteora)!=1: raise RuntimeError('DLMM_LEG_NOT_UNIQUE')
        m=meteora[0]; keys=[a.get('pubkey') for a in m.get('accounts',[]) if isinstance(a,dict)]
        if len(keys)<17 or keys[13]!=MEMO or keys[15]!=DLMM:
            raise RuntimeError('SWAP2_NAMED_ACCOUNTS_OR_BINS_INCOMPLETE')
        if not all(a.get('isWritable') is True for a in m['accounts'][16:]):
            raise RuntimeError('BIN_ARRAY_NOT_WRITABLE')
        raw=base64.b64decode(m.get('data') or '',validate=True)
        if not raw.startswith(DISC) or len(raw)<25:
            raise RuntimeError('NOT_SWAP2_INSTRUCTION')
        pump=sum(ix.get('programId')=='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
                 for ix in ixs if isinstance(ix,dict))
        if pump!=1: raise RuntimeError('PUMP_LEG_NOT_UNIQUE')
        found+=1
    return {'candidate_count':found,'swap2_bin_arrays':len(keys)-16}

def classify_sim(sim):
    if not isinstance(sim,dict):return 'SIM_RESULT_NOT_MAPPING',None,None
    err=sim.get('err','MISSING_ERROR_FIELD')
    units=sim.get('units')
    if err is None and sim.get('oracle177_signed_sim_pass') is True:
        return 'SIGNED_SIM_PASS',units,None
    anchor=None
    if isinstance(err,dict):
        rows=err.get('InstructionError')
        if isinstance(rows,list) and len(rows)==2: anchor=rows
    if isinstance(anchor,list):
        code=anchor[1].get('Custom') if isinstance(anchor[1],dict) else None
        return 'INSTRUCTION_REJECTED',units,{'instruction':anchor[0],'custom_code':code}
    return 'SIM_HOLD',units,None

def run(max_pairs=8):
    source=Path(r.__file__).read_text(encoding='utf-8')
    for key in ('ORACLE180_SWAP2_BIN_ARRAY_CORRECTION',
                'ORACLE179_NORMALIZED_SIM_VERDICT',
                'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED'):
        if key not in source:raise RuntimeError('HOLD_MISSING_'+key)
    armed=getattr(r,'_live_010_armed',None)
    if not callable(armed) or armed():raise RuntimeError('HOLD_LIVE_DISARM_NOT_PROVEN')
    for name in ('same_snapshot_route','_fast_010_profit_lock_route','compile_current','simulate_current'):
        if not callable(getattr(r,name,None)):raise RuntimeError('HOLD_MISSING_'+name)
    rpc=r.q87.c.rpc
    def protected_rpc(method,*args,**kwargs):
        if str(method).lower().startswith('send') or str(method).lower()=='requestairdrop':
            raise RuntimeError('ORACLE181_BROADCAST_FORBIDDEN')
        return rpc(method,*args,**kwargs)
    rows=[]; attempted=set()
    async def diagnostic(state,seconds,lane):
        usable=[p for p in state.get('pairs',[]) if str(p.token) in r.READY_TOKENS]
        for pair in usable[:max_pairs]:
            token=str(pair.token)
            try:
                snap=r.immutable_snapshot(pair)
                quotes=r.q18.exact_snapshot_opportunities(snap,0.050)
            except Exception as exc:
                rows.append({'token':token[:10],'stage':'QUOTE_HOLD','error_type':type(exc).__name__});continue
            for direction in ('METEORA_TO_PUMP','PUMP_TO_METEORA'):
                if direction in attempted:continue
                opp=next((x for x in quotes if x.get('direction')==direction and
                          x.get('start')==50_000_000),None)
                if opp is None:continue
                row={'token':token[:10],'direction':direction,'diagnostic_only':True}
                try:
                    if armed():raise RuntimeError('LIVE_ARMED_DURING_DIAGNOSTIC')
                    route=r.same_snapshot_route(r.USER,snap,opp)
                    # Low min-out is limited to this disarmed simulation-only diagnostic.
                    bound=max(1,int(opp.get('local_end',0)*0.90))
                    route,_,_=r._fast_010_profit_lock_route(route,direction,bound)
                    row.update(inspect_route(route))
                    row['stage']='COMPILE'
                    compiled=r.compile_current(r.USER,route)
                    if not isinstance(compiled,dict) or compiled.get('ok') is not True:
                        row['stage']='COMPILE_HOLD';row['reason']='COMPILER_NO_LEGAL_PACKET'
                    else:
                        row['packet_bytes']=len(compiled.get('raw') or b'')
                        if row['packet_bytes']>1232 or compiled.get('oracle176_packet_verified') is not True:
                            raise RuntimeError('SELECTED_SIGNED_PACKET_UNCERTIFIED')
                        if armed():raise RuntimeError('LIVE_ARMED_BEFORE_SIM')
                        sim=r.simulate_current(compiled,r.USER)
                        row['stage'],row['compute_units'],row['failure']=classify_sim(sim)
                        attempted.add(direction)
                except Exception as exc:
                    row['stage']='HOLD';row['reason']=type(exc).__name__
                    message=str(exc);row['reason_code']=message if re.fullmatch(r'[A-Z][A-Z0-9_]{2,70}',message) else 'UNCLASSIFIED_RUNTIME_FAILURE'
                rows.append(row)
                print('[ORACLE181_DIRECT] dir=%s stage=%s bytes=%s error=%s broadcast=FALSE' %
                      (direction,row['stage'],row.get('packet_bytes','NA'),row.get('failure') or row.get('reason_code','NONE')),flush=True)
            if len(attempted)==2:break
    old_serve=r.serve_canonical
    r.q87.c.rpc=protected_rpc
    r.serve_canonical=diagnostic
    try:r.run(seconds=0.0)
    finally:
        r.serve_canonical=old_serve
        r.q87.c.rpc=rpc
    result={'build':'ORACLE181','simulation_only':True,'broadcast':False,
            'live_trade_certified':False,'routes':rows,
            'signed_sim_pass_directions':sorted(d for d in attempted if any(
                x.get('direction')==d and x.get('stage')=='SIGNED_SIM_PASS' for x in rows))}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('[ORACLE181_RESULT] simulated_directions=%d signed_pass=%d broadcast=FALSE' %
          (len(attempted),len(result['signed_sim_pass_directions'])),flush=True)
    print('[REPORT]',OUT)

def test():
    import base64
    swap={'programId':DLMM,'accounts':[{'pubkey':str(i),'isWritable':False} for i in range(16)]+
          [{'pubkey':'array','isWritable':True}],
          'data':base64.b64encode(DISC+bytes(17)).decode()}
    swap['accounts'][13]['pubkey']=MEMO;swap['accounts'][15]['pubkey']=DLMM
    buy={'programId':'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'}
    row={'start_lamports':50_000_000,'original_candidates':[('X',[swap,buy])]}
    assert inspect_route(row)['swap2_bin_arrays']==1
    row['start_lamports']=10_000_000
    try:inspect_route(row)
    except RuntimeError:pass
    else:raise AssertionError('incorrect amount accepted')
    assert classify_sim({'err':{'InstructionError':[3,{'Custom':3005}]},'units':10})[2]['custom_code']==3005
    assert classify_sim({'err':None,'units':10,'oracle177_signed_sim_pass':True})[0]=='SIGNED_SIM_PASS'
    print('[TEST PASS] ORACLE181 Swap2 layout, 0.050 SOL, Anchor error, fail closed')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--test',action='store_true');a.add_argument('--run',action='store_true')
    opts=a.parse_args();test() if opts.test else run() if opts.run else a.error('Use --test or --run')
'''

def test():
    ast.parse(CODE)
    assert 'sendTransaction' not in CODE and 'ORACLE181_BROADCAST_FORBIDDEN' in CODE
    assert 'r.serve_canonical=diagnostic' in CODE
    print('[INSTALLER TEST PASS] ORACLE181 protected direct-route module compiles')

def install():
    if not ROOT.is_dir() or not (ROOT/'runtime.py').is_file():
        raise RuntimeError('HOLD_ORACLE181_REPOSITORY_NOT_FOUND')
    src=(ROOT/'runtime.py').read_text(encoding='utf-8')
    for marker in ('ORACLE180_SWAP2_BIN_ARRAY_CORRECTION', 'ORACLE179_NORMALIZED_SIM_VERDICT',
                   'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED'):
        if marker not in src:raise RuntimeError('HOLD_ORACLE181_MISSING_'+marker)
    if DEST.exists() and DEST.read_text(encoding='utf-8')!=CODE:
        raise RuntimeError('HOLD_ORACLE181_EXISTING_MODULE_DIFFERS')
    DEST.write_text(CODE,encoding='utf-8')
    ast.parse(DEST.read_text(encoding='utf-8'))
    print('[INSTALL PASS] ORACLE181 standalone direct Swap2 diagnostic; scanner untouched; broadcast blocked')

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--test',action='store_true')
    opts=a.parse_args();test() if opts.test else install()
