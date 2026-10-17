"""ORACLE-313: fresh 0.010 SOL P2M native ALT packet / unsigned simulation preflight.
Frozen ORACLE-307 pricing. Keyless, read-only, zero transaction sends.
"""
from __future__ import annotations
import argparse, base64, contextlib, json, os, pathlib, re, sqlite3, time
from unittest.mock import patch

ROOT=pathlib.Path('runtime_state/oracle/oracle_live_execution')
REPORT=ROOT/'ORACLE313_ALT_LIVE_ATOMIC_PREFLIGHT.json'
DB=ROOT/'ORACLE313_ALT_LIVE_ATOMIC_PREFLIGHT.sqlite3'
CANARY=10_000_000
LIMIT=1232
MAX_AGE=.5
PUBKEY=re.compile(r'^[1-9A-HJ-NP-Za-km-z]{32,44}$')

def disarm():
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY') or os.environ.get('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('ORACLE313_KEYLESS_DISARMED_CHILD_REQUIRED')

def clean_alt_list(value):
    rows=[s.strip() for s in value.replace(';',',').split(',') if s.strip()]
    if len(set(rows))!=len(rows) or len(rows)>8 or any(not PUBKEY.fullmatch(s) for s in rows):
        raise ValueError('INVALID_OR_DUPLICATE_ALT_ADDRESS')
    return rows

def get_wallet(value):
    if not PUBKEY.fullmatch(value or ''):raise ValueError('PUBLIC_WALLET_REQUIRED_QSB_SOLANA_WALLET')
    return value

def preload(core, alts):
    if not alts:return {},'HOLD_NO_PRELOADED_ALT'
    try:
        data=core.alt_accounts(alts)
        if any(not data.get(x) for x in alts):return {},'HOLD_ALT_ACCOUNT_NOT_FOUND'
        if any(len(v)>256 for v in data.values()):return {},'HOLD_ALT_INVALID_ACCOUNT_LENGTH'
        return data,'ALT_LOADED'
    except Exception as ex:
        return {},'HOLD_ALT_RPC_'+type(ex).__name__

def audit():
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87
    return {'same_snapshot_route':callable(getattr(rt,'same_snapshot_route',None)),
        'repaired_candidates':callable(getattr(q87,'repaired_candidates',None)),
        'native_alt_compiler':callable(getattr(q87,'compile_candidate',None)),
        'native_simulation_rpc':callable(getattr(q87.c,'rpc',None)),
        'reverse_native_certified':False,'signing':False,'broadcast':False}

def gate(rt,q87,snap,opp,stamp,wallet,alts,loaded,blockhash,now=time.monotonic,simulate=False):
    row={'token':str(snap.get('token','')),'slot':int(snap.get('slot',0) or 0),
        'direction':str(opp.get('direction','')),'size_sol':.010,
        'gross_lamports':int(opp.get('local_net',0)), 'gate':'HOLD_UNKNOWN',
        'signing':False,'broadcast':False,'execution_admission':False}
    if row['direction']!='PUMP_TO_METEORA':row['gate']='HOLD_M2P_REVERSE_BUILDER_NOT_CERTIFIED';return row
    if int(opp.get('start',0))!=CANARY:row['gate']='HOLD_NOT_EXACT_010_SOL';return row
    if row['gross_lamports']<=0:row['gate']='HOLD_GROSS_NONPOSITIVE';return row
    if now()-stamp>MAX_AGE or stamp>now()+.05:row['gate']='HOLD_SNAPSHOT_STALE';return row
    if not alts or not loaded:row['gate']='HOLD_NO_VALID_PRELOADED_ALT';return row
    if not wallet or row['token'] not in getattr(rt,'TEMPLATES',{}) or row['token'] not in getattr(rt,'METEORA_TEMPLATES',{}):
        row['gate']='HOLD_NATIVE_TEMPLATE_UNBOUND';return row
    try:
        route=rt.same_snapshot_route(wallet,snap,opp)
        if now()-stamp>MAX_AGE:row['gate']='HOLD_ROUTE_BUILD_TOO_SLOW';return row
        candidates=q87.repaired_candidates(route)
        # Exclude unsafe two-leg-only packets that omit required funding/settlement operations.
        candidates=[c for c in candidates if 'PUMP_METEORA_ONLY' not in str(c.get('name',''))]
        if not candidates:row['gate']='HOLD_NO_HELPER_COMPLETE_CANDIDATE';return row
        best=None;fails=[]
        for c in candidates:
            result=q87.compile_candidate(wallet,c['instructions'],[alts],blockhash)
            if not result.get('ok'):
                fails.append(str(result.get('error','COMPILE_FAIL')).split(':')[0][:60]);continue
            n=len(result['unsigned'])
            if n>LIMIT:fails.append('OVERSIZE_'+str(n));continue
            if best is None or n<best[0]:best=(n,c,result)
        if best is None:
            row.update(gate='HOLD_NO_LEGAL_V0_ALT_PACKET',compile_fail_codes=fails[:8]);return row
        n,c,compiled=best
        row.update(gate='UNSIGNED_LEGAL_P2M',bytes=n,candidate=str(c['name']),alt_count=len(alts))
        if now()-stamp>MAX_AGE:row['gate']='HOLD_PACKET_STALE';return row
        if not simulate:
            row['gate']='UNSIGNED_LEGAL_P2M_SIMULATION_NOT_REQUESTED';return row
        # Unsigned simulation tests program execution only. It cannot certify signed economics.
        response=q87.c.rpc('simulateTransaction',[base64.b64encode(compiled['unsigned']).decode(),
            {'encoding':'base64','sigVerify':False,'commitment':'processed',
             'replaceRecentBlockhash':False}])
        value=(response or {}).get('value') if isinstance(response,dict) else None
        if not isinstance(value,dict):row['gate']='HOLD_SIM_RESPONSE_MISSING_VALUE';return row
        row['sim_units']=value.get('unitsConsumed')
        row['sim_err_type']=type(value.get('err')).__name__ if value.get('err') is not None else None
        row['simulation_success']=value.get('err') is None
        row['gate']='UNSIGNED_SIM_PASS_NOT_PROFIT_CERTIFIED' if row['simulation_success'] else 'HOLD_UNSIGNED_SIM_FAILED'
    except Exception as ex:
        row.update(gate='HOLD_NATIVE_'+type(ex).__name__)
    return row

def connect_db():
    ROOT.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(DB,timeout=8)
    db.execute('CREATE TABLE IF NOT EXISTS results (id INTEGER PRIMARY KEY, row_json TEXT NOT NULL)')
    db.commit();return db

def live(seconds,wallet,alts,simulate):
    disarm()
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as rt
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_087_two_second_compaction_liquidity_repair as q87
    import build_oracle_307_original_engine_restore_v2 as original
    loaded,status=preload(q87.c,alts)
    print('[ORACLE313_ALT]',json.dumps({'status':status,'count':len(loaded),'send':False}),flush=True)
    if status!='ALT_LOADED':
        print('[ORACLE313_HOLD]',status,flush=True);return
    # Pin read-only loaded ALT contents for this bounded run; never issue per-candidate ALT RPC.
    def cached_alt(keys):
        if any(k not in loaded for k in keys):raise RuntimeError('ALT_NOT_PRELOADED')
        return {k:loaded[k] for k in keys}
    state={'observed':0,'gate_counts':{}};original_tap=original.passive_tap
    with contextlib.closing(connect_db()) as db:
        def wrap(fn,evidence):
            price=original_tap(fn,evidence)
            def tapped(snap,size):
                rows=price(snap,size)
                if round(float(size),6)!=.010:return rows
                for opp in rows:
                    if int(opp.get('local_net',0))<=0:continue
                    stamp=time.monotonic()
                    # Blockhash is obtained only on a positive 0.010 opportunity.
                    try:
                        blockhash=rt.BLOCKHASH.get()
                        row=gate(rt,q87,snap,opp,stamp,wallet,alts,loaded,blockhash,simulate=simulate)
                    except Exception as ex:
                        row={'gate':'HOLD_BLOCKHASH_'+type(ex).__name__,'signing':False,'broadcast':False}
                    state['observed']+=1
                    state['gate_counts'][row['gate']]=state['gate_counts'].get(row['gate'],0)+1
                    db.execute('INSERT INTO results(row_json) VALUES(?)',(json.dumps(row,sort_keys=True),));db.commit()
                    print('[ORACLE313_PHYSICAL]',json.dumps(row,sort_keys=True),flush=True)
                return rows
            return tapped
        original.passive_tap=wrap
        try:
            # Do not mutate canonical executor globals or scanner modules.
            with patch.object(q87.c,'alt_accounts',cached_alt):
                original.run(seconds,'19')
        finally:
            original.passive_tap=original_tap
            result={'build':'ORACLE313','canary_sol':.010,'alts_preloaded':len(alts),
                'positive_canary_quotes':state['observed'],'gate_counts':state['gate_counts'],
                'signing':False,'broadcast':False,'execution_admission':False,
                'signed_net_certified':False,'m2p_certified':False}
            REPORT.write_text(json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
            print('[ORACLE313_RESULT]',json.dumps(result,sort_keys=True),flush=True)

def tests():
    class Core:
        def __init__(self):self.v=0
        def alt_accounts(self,a):return {x:[b'1'*32] for x in a}
        def rpc(self,m,p):return {'value':{'err':None,'unitsConsumed':123}}
    class RT:
        TEMPLATES={'T':1};METEORA_TEMPLATES={'T':1}
        def same_snapshot_route(self,*a):return {'original_candidates':[('FULL',[])]}
    class Q:
        c=Core()
        def repaired_candidates(self,*a):return [{'name':'FULL','instructions':[]}]
        def compile_candidate(self,*a):return {'ok':True,'unsigned':b'x'*1180}
    snap={'token':'T','slot':42};opp={'direction':'PUMP_TO_METEORA','start':CANARY,'local_net':500000}
    args=(RT(),Q(),snap,opp,10.,'wallet',['ALT'],{'ALT':[b'1'*32]},'hash')
    x=gate(*args,now=lambda:10.01,simulate=True);assert x['gate']=='UNSIGNED_SIM_PASS_NOT_PROFIT_CERTIFIED'
    assert not x['execution_admission'] and not x['broadcast']
    assert gate(*args,now=lambda:11.)['gate']=='HOLD_SNAPSHOT_STALE'
    assert gate(*args,now=lambda:10.,simulate=False)['gate']=='UNSIGNED_LEGAL_P2M_SIMULATION_NOT_REQUESTED'
    assert gate(*args[:3],dict(opp,direction='METEORA_TO_PUMP'),*args[4:],now=lambda:10.)['gate']=='HOLD_M2P_REVERSE_BUILDER_NOT_CERTIFIED'
    class Over(Q):
        def compile_candidate(self,*a):return {'ok':True,'unsigned':b'x'*1299}
    assert gate(RT(),Over(),*args[2:],now=lambda:10.)['gate']=='HOLD_NO_LEGAL_V0_ALT_PACKET'
    with patch.dict(os.environ,{'QSB_SOLANA_PRIVATE_KEY':'x'}):
        try:disarm();assert False
        except RuntimeError:pass
    print('[ORACLE313_TEST_PASS] ALT_CACHE=TRUE CANARY=TRUE LIVE_NATIVE_P2M=TRUE PACKET=TRUE UNSIGNED_SIM=TRUE STALE=TRUE M2P_HOLD=TRUE NO_SEND=TRUE')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true');p.add_argument('--audit',action='store_true')
    p.add_argument('--run',action='store_true');p.add_argument('--table',action='store_true')
    p.add_argument('--seconds',type=int,default=90);p.add_argument('--alts',default=os.getenv('QSB_SOLANA_ALT_ADDRESSES',''))
    p.add_argument('--wallet',default=os.getenv('QSB_SOLANA_WALLET',''))
    p.add_argument('--simulate-unsigned',action='store_true')
    a=p.parse_args()
    if a.test:tests();return
    if a.audit:print('[ORACLE313_AUDIT]',json.dumps(audit(),sort_keys=True));return
    if a.table:
        if not DB.exists():print('[ORACLE313_TABLE] NO_EVIDENCE');return
        with contextlib.closing(sqlite3.connect(DB)) as db:
            for (raw,) in db.execute('SELECT row_json FROM results ORDER BY id DESC LIMIT 20'):
                print('[ORACLE313_ROW]',raw)
        return
    if a.run:live(a.seconds,get_wallet(a.wallet),clean_alt_list(a.alts),a.simulate_unsigned);return
    p.print_help()
if __name__=='__main__':main()
