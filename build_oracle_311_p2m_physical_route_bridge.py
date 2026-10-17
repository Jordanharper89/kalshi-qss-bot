"""ORACLE-311: physical read-only P2M route+unsigned compile bridge.
Never touches wallet secrets, signs, simulates or broadcasts. Keeps original quote engine.
"""
from __future__ import annotations
import argparse, ast, contextlib, hashlib, json, os, pathlib, sqlite3, tempfile, time

ROOT=pathlib.Path('runtime_state/oracle/oracle_live_execution')
DB=ROOT/'ORACLE311_P2M_PHYSICAL_ROUTE.sqlite3'
REPORT=ROOT/'ORACLE311_P2M_PHYSICAL_ROUTE.json'
RUNTIME=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
LIMIT=1232
CANARY=10_000_000

def disarm():
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY') or os.environ.get('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('ORACLE311_REQUIRES_KEYLESS_DISARMED_CHILD')

def audit(path=RUNTIME):
    src=path.read_text(encoding='utf-8-sig'); tree=ast.parse(src,str(path))
    funcs={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    must={'same_snapshot_route','compile_current','simulate_current'}
    if not must.issubset(funcs):raise RuntimeError('MISSING_NATIVE_ROUTE_FUNCTIONS')
    r=ast.get_source_segment(src,funcs['same_snapshot_route']) or ''
    comp=ast.get_source_segment(src,funcs['compile_current']) or ''
    # Exact positive classification: P2M is the sole accepted direction in canonical source.
    p2m=('PUMP_TO_METEORA' in r and 'rewrite_pump_buy_bounds' in r
         and 'build_meteora_ix_hot' in r and 'DIRECTION_NOT_CERTIFIED' in r)
    m2p=('METEORA_TO_PUMP' in r and 'DIRECTION_NOT_CERTIFIED' not in r)
    return dict(runtime=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        p2m_builder_verified=p2m,m2p_builder_verified=m2p,
        unsigned_compiler_verified='compile_candidate' in comp,
        compiler_uses_alt='base_alts' in comp or 'lookup_table' in comp,
        packet_limit_bytes=LIMIT,signing=False,broadcast=False)

def open_db(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS physical (id INTEGER PRIMARY KEY, stamp REAL, token TEXT, direction TEXT, slot INTEGER, size REAL, gross INTEGER, gate TEXT, bytes INTEGER, error TEXT)')
    db.commit();return db

def save(db, row):
    db.execute('INSERT INTO physical(stamp,token,direction,slot,size,gross,gate,bytes,error) VALUES(?,?,?,?,?,?,?,?,?)',
        tuple(row.get(k) for k in ('stamp','token','direction','slot','size','gross','gate','bytes','error')))
    db.commit()

def attempt(rt,snap,opp,size,stamp,*,clock=time.time):
    """One fresh original snapshot, native P2M route and real unsigned compile only."""
    row=dict(stamp=stamp,token=str(snap.get('token','')),direction=str(opp.get('direction','')),
             slot=int(snap.get('slot',-1)),size=float(size),gross=int(opp.get('local_net',0)),
             gate='HOLD_UNKNOWN',bytes=None,error='')
    if row['direction']!='PUMP_TO_METEORA':row['gate']='HOLD_M2P_NATIVE_NOT_CERTIFIED';return row
    if round(size,3)!=.010 or int(opp.get('start',0))!=CANARY:
        row['gate']='HOLD_NOT_EXACT_010_SOL';return row
    if row['gross']<=0:row['gate']='HOLD_GROSS_NONPOSITIVE';return row
    if stamp>clock()+.1 or clock()-stamp>.5:row['gate']='HOLD_QUOTE_TOO_OLD';return row
    token=row['token'];templates=getattr(rt,'TEMPLATES',{})
    if token not in templates:row['gate']='HOLD_CANONICAL_EXECUTOR_TEMPLATE_NOT_BOUND';return row
    try:
        user=getattr(rt,'USER',None)
        if not user:row['gate']='HOLD_EXECUTOR_PUBLIC_WALLET_NOT_BOUND';return row
        route=rt.same_snapshot_route(user,snap,opp)
        if clock()-stamp>.5:row['gate']='HOLD_SNAPSHOT_EXPIRED_AFTER_ROUTE_BUILD';return row
        result=rt.compile_current(user,route)
        if not result.get('ok'):
            row['gate']='HOLD_NATIVE_UNSIGNED_COMPILE';row['error']=str(result.get('reason','FAILED'))[:160]
            return row
        row['bytes']=int(result['bytes'])
        if row['bytes']>LIMIT:row['gate']='HOLD_PACKET_TOO_LARGE';return row
        row['gate']='UNSIGNED_LEGAL_P2M_NEEDS_SIGNED_SIM_AND_NET_CERTIFICATION'
        return row
    except Exception as e:
        row['gate']='HOLD_NATIVE_ROUTE_ERROR';row['error']=type(e).__name__+':'+str(e)[:150]
        return row

def run(seconds):
    disarm();contract=audit()
    if not contract['p2m_builder_verified']:raise RuntimeError('P2M_NATIVE_FUNCTION_CONTRACT_CHANGED')
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
    import build_oracle_307_original_engine_restore_v2 as baseline
    original=baseline.passive_tap
    counts={};events=[0];started=time.time()
    with contextlib.closing(open_db(DB)) as db:
        def wrap(fn,evidence):
            original_pricer=original(fn,evidence)
            def tapped(snap,size):
                rows=original_pricer(snap,size)
                if round(float(size),3)!=.010:return rows
                for item in rows:
                    if int(item.get('local_net',0))<=0:continue
                    stamp=time.time()
                    result=attempt(rt,snap,item,size,stamp)
                    # Query slot already in the original WS envelope/context; no RPC per quote.
                    result['slot']=int(snap.get('slot',getattr(baseline.CTX,'slot',-1)) or -1)
                    save(db,result);events[0]+=1
                    counts[result['gate']]=counts.get(result['gate'],0)+1
                    print('[ORACLE311_PHYSICAL]',json.dumps(result,sort_keys=True),flush=True)
                return rows
            return tapped
        baseline.passive_tap=wrap
        try:
            print('[ORACLE311_START]',json.dumps(dict(contract=contract,canary_sol=.010,simulation=False,broadcast=False)),flush=True)
            baseline.run(seconds,'19')
        finally:
            baseline.passive_tap=original
            ROOT.mkdir(parents=True,exist_ok=True)
            report=dict(build='ORACLE311',contract=contract,seconds_elapsed=round(time.time()-started,2),
                processed_positive_canary_rows=events[0],gate_counts=counts,signing=False,
                broadcast=False,execution_admission=False,simulated_profit_certified=False)
            REPORT.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
            print('[ORACLE311_RESULT]',json.dumps(report,sort_keys=True),flush=True)

def test():
    class RT:
        TEMPLATES={'T':{'pump_pool':'P'}};USER='public-only'
        def same_snapshot_route(self,user,snap,opp):return {'route':True}
        def compile_current(self,user,route):return {'ok':True,'bytes':1190}
    sample={'token':'T','slot':100};opp={'direction':'PUMP_TO_METEORA','start':CANARY,'local_net':350000}
    assert attempt(RT(),sample,opp,.010,100.,clock=lambda:100.1)['gate'].startswith('UNSIGNED_LEGAL')
    assert attempt(RT(),sample,dict(opp,direction='METEORA_TO_PUMP'),.010,100.,clock=lambda:100.)['gate']=='HOLD_M2P_NATIVE_NOT_CERTIFIED'
    assert attempt(RT(),sample,opp,.010,100.,clock=lambda:101.)['gate']=='HOLD_QUOTE_TOO_OLD'
    class Over(RT):
        def compile_current(self,user,route):return {'ok':True,'bytes':1348}
    assert attempt(Over(),sample,opp,.010,100.,clock=lambda:100.)['gate']=='HOLD_PACKET_TOO_LARGE'
    with tempfile.TemporaryDirectory() as t:
        with contextlib.closing(open_db(pathlib.Path(t)/'db.sqlite3')) as db:
            save(db,attempt(RT(),sample,opp,.010,100.,clock=lambda:100.))
            assert db.execute('SELECT COUNT(*) FROM physical').fetchone()[0]==1
    print('[ORACLE311_TEST_PASS] P2M_PHYSICAL_CALL=TRUE CANARY=TRUE STALE=TRUE M2P_HOLD=TRUE PACKET=TRUE WINDOWS_SQLITE_CLOSED=TRUE NO_SIGN=TRUE')

def table():
    if not DB.is_file():print('[ORACLE311_TABLE] NO_EVIDENCE');return
    with contextlib.closing(sqlite3.connect(DB)) as db:
        for x in db.execute('SELECT token,direction,slot,size,gross,gate,bytes,error FROM physical ORDER BY id DESC LIMIT 25'):
            print('[ORACLE311_ROW]',json.dumps(dict(zip(('token','direction','slot','size','gross','gate','bytes','error'),x))))

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--audit',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--table',action='store_true');p.add_argument('--seconds',type=float,default=90)
    a=p.parse_args()
    if a.test:test()
    elif a.audit:print('[ORACLE311_AUDIT]',json.dumps(audit()))
    elif a.table:table()
    elif a.run:run(a.seconds)
    else:p.print_help()
if __name__=='__main__':main()
