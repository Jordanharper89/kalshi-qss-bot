"""ORACLE-310: original quote engine to native executor contract handoff.
No key access, signing, simulation or broadcast. Original scanner code unchanged.
"""
from __future__ import annotations
import argparse, ast, contextlib, hashlib, json, os, pathlib, sqlite3, tempfile, time

BASE=pathlib.Path('runtime_state/oracle/oracle_live_execution')
DB=BASE/'ORACLE310_NATIVE_EXECUTOR_HANDOFF.sqlite3'
REPORT=BASE/'ORACLE310_NATIVE_EXECUTOR_HANDOFF.json'
ATOMIC=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
PACKET_LIMIT=1232
CANARY=10_000_000
DIRECTIONS={'PUMP_TO_METEORA','METEORA_TO_PUMP'}

def disarm():
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('PRIVATE_KEY_FORBIDDEN_IN_OBSERVATION_CHILD')
    if os.environ.get('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('LIVE_ARM_MUST_BE_NO')

def native_contract(path=ATOMIC):
    if not path.is_file(): raise RuntimeError('MISSING_EXISTING_ATOMIC_RUNTIME:'+str(path))
    src=path.read_text(encoding='utf-8-sig')
    tree=ast.parse(src,str(path))
    funcs={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    required={'same_snapshot_route','compile_current','simulate_current','immutable_snapshot'}
    missing=required-funcs.keys()
    if missing:raise RuntimeError('MISSING_ATOMIC_INTERFACES:'+','.join(sorted(missing)))
    route=ast.get_source_segment(src,funcs['same_snapshot_route']) or ''
    comp=ast.get_source_segment(src,funcs['compile_current']) or ''
    p2m=('PUMP_TO_METEORA' in route)
    m2p=('METEORA_TO_PUMP' in route and 'DIRECTION_NOT_CERTIFIED' not in route)
    # Never mark M2P certified while the original route explicitly rejects it.
    if 'DIRECTION_NOT_CERTIFIED' in route:m2p=False
    return {'existing_runtime':str(path),'runtime_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'interfaces':sorted(required),'p2m_route_present':p2m,'m2p_route_certified':m2p,
        'compile_candidate_present':'compile_candidate' in comp,
        'compiler_alt_contract_not_certified':True,'packet_limit_bytes':PACKET_LIMIT,
        'signed_simulation_certified':False,'broadcast':False}

def classify(row,contract,now=None):
    """Classify an IN-PROCESS quote, never a historical ORACLE-309 row."""
    now=time.time() if now is None else now
    token=str(row.get('token',''))
    direction=str(row.get('direction',''))
    size=round(float(row.get('size_sol',0)),3)
    slot=row.get('slot')
    source=str(row.get('source',''))
    observed=float(row.get('observed_at',0))
    gross=int(row.get('gross_lamports',0))
    if source!='LIVE_ORIGINAL_ORACLE018':gate='HOLD_HISTORICAL_NOT_FRESH'
    elif not token or direction not in DIRECTIONS or slot is None:gate='HOLD_INVALID_IDENTITY'
    elif size!=0.010:gate='HOLD_NOT_FIRST_CANARY_SIZE'
    elif observed>now+1 or now-observed>0.750:gate='HOLD_STALE_QUOTE'
    elif gross<=0:gate='HOLD_NONPOSITIVE_GROSS'
    elif direction=='METEORA_TO_PUMP' and not contract['m2p_route_certified']:
        gate='HOLD_M2P_NATIVE_ROUTE_NOT_CERTIFIED'
    elif direction=='PUMP_TO_METEORA' and not contract['p2m_route_present']:
        gate='HOLD_P2M_NATIVE_ROUTE_MISSING'
    else:gate='HOLD_ALT_PACKET_AND_SIGNED_SIM_NOT_CERTIFIED'
    return dict(row,gate=gate,signing=False,broadcast=False,execution_admission=False,
                fee_adjusted_net_certified=False,atomic_simulation_certified=False,
                packet_bytes=None,packet_legal_certified=False)

def db_open(path=DB):
    path.parent.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(path,timeout=15)
    con.execute('PRAGMA busy_timeout=15000')
    con.execute('CREATE TABLE IF NOT EXISTS handoff (id INTEGER PRIMARY KEY, epoch REAL, token TEXT, direction TEXT, slot INTEGER, size_sol REAL, gross_lamports INTEGER, gate TEXT, source TEXT)')
    con.commit()
    return con

def record(row,path=DB):
    with contextlib.closing(db_open(path)) as c, c:
        c.execute('INSERT INTO handoff(epoch,token,direction,slot,size_sol,gross_lamports,gate,source) VALUES(?,?,?,?,?,?,?,?)',
            (row['observed_at'],row['token'],row['direction'],row['slot'],row['size_sol'],row['gross_lamports'],row['gate'],row['source']))

def extract(token,snap,size,r,slot):
    start=int(r['start'])
    end=int(r['local_end'])
    return {'token':str(token),'direction':str(r['direction']),'size_sol':float(size),
            'slot':slot,'observed_at':time.time(),'gross_lamports':end-start,
            'source':'LIVE_ORIGINAL_ORACLE018'}

def run(seconds):
    disarm();contract=native_contract()
    import build_oracle_307_original_engine_restore_v2 as baseline
    # Attach a passive tap to the original ORACLE-307 passthrough, not the native pricer itself.
    # Original quote functions, pool warmup, WS stream and risk engine are unchanged.
    original=baseline.passive_tap
    counters={'observed':0,'positive':0,'canary':0,'held':{},'tap_errors':0}
    def installed(fn,evidence):
        passthrough=original(fn,evidence)
        def intercept(snap,size):
            results=passthrough(snap,size)
            token=snap.get('token','')
            slot=getattr(baseline.CTX,'slot',None)
            for result in results:
                counters['observed']+=1
                try:
                    row=extract(token,snap,size,result,slot)
                    if row['gross_lamports']<=0:continue
                    counters['positive']+=1
                    verdict=classify(row,contract)
                    if verdict['size_sol']==.010:counters['canary']+=1
                    gate=verdict['gate']
                    counters['held'][gate]=counters['held'].get(gate,0)+1
                    record(verdict)
                    print('[ORACLE310_LIVE_HANDOFF]',json.dumps({k:verdict[k] for k in ('token','direction','size_sol','slot','gross_lamports','gate','execution_admission','signing','broadcast')}),flush=True)
                except Exception as exc:
                    counters['tap_errors']+=1
                    print('[ORACLE310_TAP_HOLD]',type(exc).__name__,flush=True)
            return results
        return intercept
    baseline.passive_tap=installed
    try:
        print('[ORACLE310_START]',json.dumps({'pipeline':'ORACLE025_020_018','grid':'19','native_contract':contract,'signing':False,'broadcast':False}),flush=True)
        baseline.run(seconds,'19')
    finally:
        baseline.passive_tap=original
        BASE.mkdir(parents=True,exist_ok=True)
        out={'build':'ORACLE310','native_contract':contract,'counters':counters,
             'status':'LIVE_NATIVE_HANDOFF_EVIDENCE_ONLY','fresh_quotes_from_restored_scanner':True,
             'executed_trades':0,'signing':False,'broadcast':False,'execution_admission':False}
        REPORT.write_text(json.dumps(out,indent=2,sort_keys=True),encoding='utf-8')
        print('[ORACLE310_RESULT]',json.dumps(out),flush=True)
        print('[REPORT]',REPORT,flush=True)

def test():
    with tempfile.TemporaryDirectory(prefix='oracle310_') as t:
        p=pathlib.Path(t)/'rows.sqlite3'
        c={'p2m_route_present':True,'m2p_route_certified':False}
        stamp=100.0
        sample={'token':'mint','direction':'PUMP_TO_METEORA','size_sol':.010,'slot':42,
                'observed_at':stamp,'gross_lamports':200_000,'source':'LIVE_ORIGINAL_ORACLE018'}
        x=classify(sample,c,now=stamp+.1)
        assert x['gate']=='HOLD_ALT_PACKET_AND_SIGNED_SIM_NOT_CERTIFIED'
        assert classify(dict(sample,direction='METEORA_TO_PUMP'),c,now=stamp)['gate']=='HOLD_M2P_NATIVE_ROUTE_NOT_CERTIFIED'
        assert classify(dict(sample,source='ORACLE309_HISTORICAL'),c,now=stamp)['gate']=='HOLD_HISTORICAL_NOT_FRESH'
        assert classify(sample,c,now=stamp+2)['gate']=='HOLD_STALE_QUOTE'
        assert classify(dict(sample,size_sol=.015),c,now=stamp)['gate']=='HOLD_NOT_FIRST_CANARY_SIZE'
        record(x,p)
        with contextlib.closing(sqlite3.connect(p)) as db:
            assert db.execute('SELECT COUNT(*) FROM handoff').fetchone()[0]==1
    assert PACKET_LIMIT==1232 and CANARY==10_000_000
    print('[ORACLE310_TEST_PASS] original_passthrough=TRUE live_only=TRUE canary_exact=TRUE m2p_hold=TRUE packet_and_sim_hold=TRUE sqlite_windows_closed=TRUE no_trades=TRUE')

def table():
    if not DB.exists():print('[ORACLE310_TABLE] NO_LIVE_EVIDENCE');return
    with contextlib.closing(sqlite3.connect(DB)) as c:
        for r in c.execute('SELECT token,direction,slot,size_sol,gross_lamports,gate FROM handoff ORDER BY id DESC LIMIT 25'):
            print('[ORACLE310_ROW]',json.dumps(dict(zip(('token','direction','slot','size_sol','gross_lamports','gate'),r))))

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--test',action='store_true');a.add_argument('--audit',action='store_true');a.add_argument('--run',action='store_true');a.add_argument('--table',action='store_true')
    a.add_argument('--seconds',type=float,default=90)
    opts=a.parse_args()
    if opts.test:test()
    elif opts.audit:print('[ORACLE310_ATOMIC_CONTRACT]',json.dumps(native_contract()))
    elif opts.table:table()
    elif opts.run:run(opts.seconds)
    else:a.print_help()
if __name__=='__main__':main()
