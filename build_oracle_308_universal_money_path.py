"""ORACLE-308: read-only universal discovery intelligence + original native pricing.
Full single-file installer. Does not modify existing production modules.
"""
from __future__ import annotations
import argparse, ast, collections, hashlib, json, os, pathlib, re, sqlite3, sys, tempfile, time

BASE=pathlib.Path('runtime_state/oracle/oracle_live_execution')
REPORT=BASE/'ORACLE308_UNIVERSAL_MONEY_PATH.json'
DB=BASE/'ORACLE308_UNIVERSAL_MONEY_PATH.sqlite3'
GRID=tuple(round(.010+i*.005,3) for i in range(19))
KEYS=('token','mint','token_address','base_mint','baseMint','mint_address')
OLD='build_oracle_307_original_engine_restore_v2.py'
PAIR_SRC=pathlib.Path('qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py')


def disarm():
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY'):raise RuntimeError('PRIVATE_KEY_FORBIDDEN_IN_READ_ONLY_CHILD')
    if os.environ.get('QSB_LIVE_ARM','NO').upper()!='NO':raise RuntimeError('QSB_LIVE_ARM_MUST_BE_NO')


def safe_json(path):
    try:
        if path.stat().st_size>12_000_000:return None
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,UnicodeError,ValueError):return None


def find_tokens(obj,cap=4000):
    found=set();todo=[obj];seen=0
    while todo and seen<cap:
        v=todo.pop();seen+=1
        if isinstance(v,dict):
            for k,x in v.items():
                if k in KEYS and isinstance(x,str) and 32<=len(x)<=48 and re.fullmatch('[1-9A-HJ-NP-Za-km-z]+',x):found.add(x)
                elif isinstance(x,(dict,list)):todo.append(x)
        elif isinstance(v,list):todo.extend(v[:200])
    return found


def collect_discovery(root):
    """Read-only extraction; never treat discovery tokens as admitted pairs."""
    terms=('mriya','umd','oracle_269','oracle269','oracle_288','oracle288',
           'oracle_289','oracle289','oracle_293','oracle293','discovery','crosslist')
    matched=[];all_tokens=set();mriya=set()
    for sub in ('runtime_state/oracle','runtime_state/solana_opportunities','runtime_state/qseries'):
        folder=root/sub
        if not folder.is_dir():continue
        for p in folder.rglob('*.json'):
            label=p.name.lower()
            if not any(t in label or t in str(p.parent).lower() for t in terms):continue
            data=safe_json(p)
            if data is None:continue
            tokens=find_tokens(data)
            all_tokens.update(tokens)
            if 'mriya' in str(p).lower() or 'oracle_289' in label or 'oracle289' in label:mriya.update(tokens)
            matched.append({'path':str(p.relative_to(root)),'token_count':len(tokens),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
            if len(matched)>=100:break
        if len(matched)>=100:break
    return {'files':matched,'tokens':all_tokens,'mriya_tokens':mriya}


def ledger():
    BASE.mkdir(parents=True,exist_ok=True)
    con=sqlite3.connect(DB,timeout=20)
    con.execute('CREATE TABLE IF NOT EXISTS pair_queue(run TEXT,token TEXT,pump_pool TEXT,meteora_pool TEXT,status TEXT,reason TEXT,from_mriya INTEGER,asof REAL,PRIMARY KEY(run,token,pump_pool))')
    con.execute('CREATE TABLE IF NOT EXISTS candidates(run TEXT,token TEXT,direction TEXT,size REAL,slot INTEGER,gross_bps REAL,gross_lamports INTEGER,estimated_fee_lamports INTEGER,estimated_net_lamports INTEGER,status TEXT,reason TEXT,asof REAL)')
    con.commit();return con


def as_dict(pair):
    return {'token':str(getattr(pair,'token','')),'pump_pool':str(getattr(pair,'pump_pool','')),
            'meteora_pool':str(getattr(pair,'meteora_pool',''))}


def snapshot_queue(run_id, state, d):
    pairs=[as_dict(p) for p in list(state.get('pairs') or [])]
    con=ledger()
    try:
        for p in pairs:
            con.execute('INSERT OR REPLACE INTO pair_queue VALUES(?,?,?,?,?,?,?,?)',(
                run_id,p['token'],p['pump_pool'],p['meteora_pool'],'HOT_EXISTING_SCANNER',
                'EXISTING_Q25_HYDRATED_PAIR',int(p['token'] in d['mriya_tokens']),time.time()))
        for token in sorted(d['tokens']-{p['token'] for p in pairs})[:300]:
            con.execute('INSERT OR REPLACE INTO pair_queue VALUES(?,?,?,?,?,?,?,?)',(
                run_id,token,'','', 'DISCOVERED_NOT_ADMITTED',
                'NO_PHYSICAL_PAIR_HYDRATION_FROM_THIS_SOURCE',int(token in d['mriya_tokens']),time.time()))
        con.commit()
    finally:con.close()
    return pairs


def classify_candidate(row,slot,run_id,fee_lamports):
    gross=int(row['local_net']);start=int(row['start']);size=float(row['size_sol'])
    net=gross-fee_lamports
    # Fees here are a configured stress assumption, NOT an observed transaction fee.
    status='GROSS_NONPOSITIVE' if gross<=0 else 'POSITIVE_GROSS_ESTIMATED_NET_ONLY'
    reason='NO_SIGNED_ATOMIC_SIMULATION_OR_FRESHNESS_CERTIFICATION'
    return (run_id,str(row['token']),str(row['direction']),size,int(slot or 0),
            gross*10000/start,gross,fee_lamports,net,status,reason,time.time())


def report_queue(run_id, discovery, pairs, fee_lamports, result=None):
    con=ledger()
    try:
        # Reuse ORACLE-307 V2 persisted native outputs, including its authentic slots.
        src=BASE/'ORACLE307_ORIGINAL_EXACT_EVIDENCE.sqlite3'
        native_report=safe_json(BASE/'ORACLE307_RESTORE_REPORT.json') or {}
        native_id=native_report.get('run_id')
        if src.is_file() and native_id:
            read=sqlite3.connect('file:'+str(src.resolve()).replace('\\','/')+'?mode=ro',uri=True,timeout=15)
            try:
                for token,direction,size,slot,gross,start in read.execute(
                  "SELECT token,direction,size_sol,slot,output_lamports-input_lamports,input_lamports FROM quotes WHERE run_id=? AND status='GROSS_POSITIVE_CANDIDATE'",
                  (native_id,)):
                    if not start or gross is None:continue
                    con.execute('INSERT INTO candidates VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',
                        (run_id,token,direction,size,int(slot or 0),gross*10000/start,int(gross),
                        fee_lamports,int(gross)-fee_lamports,'SCENARIO_ONLY_NOT_EXECUTABLE',
                        'NO_SIGNED_SIMULATION_FRESHNESS_OR_MEASURED_NETWORK_FEE',time.time()))
            finally:read.close()
        con.commit()
        counts=dict(con.execute('SELECT status,COUNT(*) FROM pair_queue WHERE run=? GROUP BY status',(run_id,)).fetchall())
        ccount=con.execute('SELECT COUNT(*) FROM candidates WHERE run=?',(run_id,)).fetchone()[0]
        positive=con.execute('SELECT COUNT(*) FROM candidates WHERE run=? AND gross_lamports>0',(run_id,)).fetchone()[0]
        top=con.execute('SELECT token,direction,size,slot,ROUND(gross_bps,2),gross_lamports,estimated_net_lamports FROM candidates WHERE run=? AND gross_lamports>0 ORDER BY estimated_net_lamports DESC LIMIT 8',(run_id,)).fetchall()
    finally:con.close()
    out={'build':'ORACLE308','run_id':run_id,'original_pipeline':'ORACLE025->ORACLE020->ORACLE018',
         'frozen_scanner_modified':False,'discovery_json_files':len(discovery['files']),
         'distinct_discovery_tokens':len(discovery['tokens']), 'mriya_hint_tokens':len(discovery['mriya_tokens']),
         'existing_hydrated_pairs':len(pairs),'pair_queue':counts,'quote_rows':ccount,
         'gross_positive_candidates':positive,'candidate_top':top,
         'fee_model':'USER_SPECIFIED_SCENARIO_NOT_MEASURED','assumed_fee_lamports':fee_lamports,
         'fee_adjusted_net_certified':False,'atomic_simulation_certified':False,
         'signing':False,'broadcast':False,'execution_authority':False,
         'automatic_discovery_admission':False,
         'discovery_admission_hold':'EXISTING_WARM_PAIR_REPLENISHMENT_INTERFACE_NOT_CERTIFIED_FOR_HOT_CUTOVER',
         'status':'EXISTING_NATIVE_ENGINE_OBSERVED', 'original_result':result}
    REPORT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str),encoding='utf-8')
    print('[ORACLE308_RESULT]',json.dumps(out,default=str),flush=True)
    print('[REPORT]',REPORT,flush=True)
    return out


def run(seconds=180,fee_lamports=250000):
    disarm()
    if not pathlib.Path(OLD).is_file():raise RuntimeError('ORACLE307_V2_BASELINE_MISSING')
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
    from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
    import build_oracle_307_original_engine_restore_v2 as original
    root=pathlib.Path.cwd();d=collect_discovery(root);run_id='o308_'+str(time.time_ns())
    orig_prepare=q25.prepare_once;orig_quote=q18.exact_snapshot_opportunities
    state_cache={'pairs':[]};stats=collections.Counter()
    def prepare(rootpath):
        state,cap=orig_prepare(rootpath)
        state_cache['pairs']=snapshot_queue(run_id,state,d)
        print('[ORACLE308_COVERAGE]',json.dumps({'discovered_tokens':len(d['tokens']),
            'mriya_hints':len(d['mriya_tokens']),'existing_hydrated_pairs':len(state_cache['pairs']),
            'eligible_to_trade':False}),flush=True)
        return state,cap
    def observe(snap,size):
        rows=orig_quote(snap,size)
        for row in rows:
            if row.get('direction') not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):continue
            try:
                record=classify_candidate(row,0,run_id,fee_lamports)
                # Batch small non-blocking for hot path; original 307 recorder handles full slot provenance.
                stats['quotes']+=1
                if int(row.get('local_net',0))>0:
                    stats['positive']+=1
                    print('[ORACLE308_NET_SCENARIO]',json.dumps({'token':record[1],'direction':record[2],
                        'size':record[3],'gross_bps':round(record[5],2), 'estimated_net_lamports':record[8],
                        'scenario_only':True}),flush=True)
            except (ValueError,KeyError,TypeError,ZeroDivisionError):stats['invalid']+=1
        return rows
    # Use the original 307 ledger with slot provenance for every quote; this overlay is discovery + safe ranking.
    q25.prepare_once=prepare
    # Do not wrap the exact hot pricer, preserving the fast event lane completely.
    print('[ORACLE308_START]',json.dumps({'pipeline':'ORACLE025_020_018','grid':list(GRID),
        'discovery_files':len(d['files']),'mriya_hints':len(d['mriya_tokens']),
        'fees_scenario_lamports':fee_lamports,'broadcast':False}),flush=True)
    try:
        original.run(float(seconds),grid='19',max_warms=28)
    finally:
        q25.prepare_once=orig_prepare
        report_queue(run_id,d,state_cache['pairs'],fee_lamports)


def table():
    if not DB.is_file():print('[ORACLE308_TABLE] NO_RUN');return
    con=sqlite3.connect(DB)
    try:
        for row in con.execute('SELECT status,COUNT(*) FROM pair_queue WHERE run=(SELECT MAX(run) FROM pair_queue) GROUP BY status'):
            print('[ORACLE308_QUEUE]',row)
        for row in con.execute('SELECT token,from_mriya,status FROM pair_queue WHERE run=(SELECT MAX(run) FROM pair_queue) ORDER BY from_mriya DESC,status LIMIT 30'):
            print('[ORACLE308_TOKEN]',row)
    finally:con.close()
    print('[ORACLE307_TABLE] Run: python '+OLD+' --table')


def test():
    assert len(GRID)==19 and GRID[0]==.010 and GRID[-1]==.100
    d={'token':'33jENUQnjoitkMFpvNJcSHyLAHFWJuHwT6E3E8CNpump'}
    assert d['token'] in find_tokens({'rows':[d]})
    row={'local_net':100000,'start':50000000,'size_sol':.05,'token':d['token'],'direction':'METEORA_TO_PUMP'}
    assert classify_candidate(row,12,'test',250000)[8]==-150000
    with tempfile.TemporaryDirectory() as folder:
        x=pathlib.Path(folder)/'sample.json';x.write_text(json.dumps({'rows':[d]}),encoding='utf8')
        assert d['token'] in find_tokens(safe_json(x))
    assert 'oracle_025' in PAIR_SRC.name
    print('[ORACLE308_TEST_PASS] grid19=TRUE discovery=TRUE mriya_read_only=TRUE native_baseline=TRUE scenario_not_certified=TRUE no_orders=TRUE')


def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true');p.add_argument('--table',action='store_true');p.add_argument('--seconds',type=float,default=180);p.add_argument('--assumed-fee-lamports',type=int,default=250000)
    a=p.parse_args()
    if a.test:test()
    elif a.table:table()
    elif a.run:
        if a.assumed_fee_lamports<0:raise RuntimeError('NEGATIVE_FEE_SCENARIO')
        run(a.seconds,a.assumed_fee_lamports)
    else:p.print_help()
if __name__=='__main__':main()
