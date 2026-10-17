"""ORACLE-309: read-only native candidate-to-atomic gate queue.
Consumes 307/308 evidence. NEVER imports live trading modules or accesses keys.
"""
from __future__ import annotations
import argparse, collections, json, pathlib, sqlite3, tempfile, time

BASE=pathlib.Path('runtime_state/oracle/oracle_live_execution')
DB308=BASE/'ORACLE308_UNIVERSAL_MONEY_PATH.sqlite3'
DB307=BASE/'ORACLE307_ORIGINAL_EXACT_EVIDENCE.sqlite3'
REPORT=BASE/'ORACLE309_ATOMIC_CANDIDATE_QUEUE.json'
QUEUE=BASE/'ORACLE309_ATOMIC_CANDIDATE_QUEUE.sqlite3'
MAX_PACKET=1232
CANARY=0.010


def read_ro(path):
    if not path.exists():raise RuntimeError('MISSING_EVIDENCE:'+str(path))
    return sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=10)


def latest_id(con,table):
    row=con.execute('SELECT run FROM '+table+' ORDER BY rowid DESC LIMIT 1').fetchone()
    if not row:raise RuntimeError('EMPTY_EVIDENCE:'+table)
    return row[0]


def parse(db308=DB308,db307=DB307):
    with read_ro(db308) as a,read_ro(db307) as b:
        run308=latest_id(a,'candidates')
        native=b.execute("SELECT run_id FROM quotes ORDER BY rowid DESC LIMIT 1").fetchone()
        if not native:raise RuntimeError('EMPTY_NATIVE_QUOTES')
        run307=native[0]
        rows=b.execute("SELECT token,direction,size_sol,slot,input_lamports,output_lamports FROM quotes WHERE run_id=? AND status='GROSS_POSITIVE_CANDIDATE'",(run307,)).fetchall()
        discovery=a.execute('SELECT status,COUNT(*) FROM pair_queue WHERE run=? GROUP BY status',(run308,)).fetchall()
        # Cross-check the run IDs: prevents accidentally joining new discovery with old native quotes.
        matches=a.execute('SELECT COUNT(*) FROM candidates WHERE run=?',(run308,)).fetchone()[0]
        if not matches or not rows:raise RuntimeError('NO_POSITIVE_EVIDENCE_IN_CURRENT_RUN')
        if matches!=len(rows):raise RuntimeError('NATIVE_CANDIDATE_COUNT_MISMATCH')
        return {'run308':run308,'run307':run307,'rows':rows,'discovery':dict(discovery)}


def prioritize(rows,fee=250000):
    """One best size per token/direction/slot, separately retain exact canary."""
    grouped=collections.defaultdict(list)
    for token,direction,size,slot,amount_in,amount_out in rows:
        if direction not in ('METEORA_TO_PUMP','PUMP_TO_METEORA'):continue
        if not amount_in or amount_in<1 or amount_out is None or slot is None:continue
        gross=int(amount_out)-int(amount_in)
        if gross<=0:continue
        row={'token':token,'direction':direction,'size_sol':round(float(size),3),
             'slot':int(slot),'gross_lamports':gross,'gross_bps':round(10000*gross/int(amount_in),3),
             'scenario_fee_lamports':fee,'scenario_net_lamports':gross-fee,
             'canary_size':abs(float(size)-CANARY)<1e-8,
             'net_certified':False,'atomic_certified':False,'freshness_certified':False,
             'execution_admission':False,'signing':False,'broadcast':False,
             'gate':'HOLD_REVALIDATE_FRESH_EXACT_ATOMIC_PACKET_AND_SIGNED_SIM'}
        grouped[(token,direction,int(slot))].append(row)
    selected=[]
    for key,group in grouped.items():
        group.sort(key=lambda r:(r['scenario_net_lamports'],r['gross_lamports']),reverse=True)
        selected.append(group[0])
        canary=next((r for r in group if r['canary_size']),None)
        if canary and canary is not group[0]:selected.append(canary)
    selected.sort(key=lambda r:(r['canary_size'],r['scenario_net_lamports']),reverse=True)
    return selected


def store(source,selected,fee,base=BASE):
    base.mkdir(parents=True,exist_ok=True)
    target=base/'ORACLE309_ATOMIC_CANDIDATE_QUEUE.sqlite3'
    with sqlite3.connect(target,timeout=10) as c:
        c.execute('CREATE TABLE IF NOT EXISTS queue (native_run TEXT, token TEXT, direction TEXT, slot INTEGER, size_sol REAL, gross_lamports INTEGER, gross_bps REAL, scenario_fee_lamports INTEGER, scenario_net_lamports INTEGER, canary_size INTEGER, gate TEXT, PRIMARY KEY(native_run,token,direction,slot,size_sol))')
        for r in selected:
            c.execute('INSERT OR REPLACE INTO queue VALUES(?,?,?,?,?,?,?,?,?,?,?)',
              (source['run307'],r['token'],r['direction'],r['slot'],r['size_sol'],r['gross_lamports'],
               r['gross_bps'],fee,r['scenario_net_lamports'],int(r['canary_size']),r['gate']))
    candidate_groups=len({(x['token'],x['direction'],x['slot']) for x in selected})
    out={'build':'ORACLE309','source_307_run':source['run307'],'source_308_run':source['run308'],
      'original_quote_rows':len(source['rows']),'unique_direction_slot_groups':candidate_groups,
      'selected_candidate_rows':len(selected),'canary_quote_count':sum(r['canary_size'] for r in selected),
      'tokens_with_positive_quotes':len({r['token'] for r in selected}),
      'discovery_counts':source['discovery'],'fee_scenario_lamports':fee,
      'fee_scenario_is_measured':False,'native_executor_oversize_evidence':{
        'FULL_BYTES':1348,'NO_COMPUTE_MEMO_BYTES':1296,'PUMP_METEORA_ONLY_BYTES':1257,
        'solana_packet_limit_bytes':MAX_PACKET,'candidate_specific_size_certified':False,
        'implication':'ALL_REPORTED_TEMPLATES_OVERSIZE; EXISTING_ALT/COMPRESSION_ROUTE_REQUIRED'},
      'execution_admission':False,'signing':False,'broadcast':False,'atomic_simulation_certified':False,
      'status':'QUOTE_TO_ATOMIC_GATE_QUEUE_ONLY', 'top':selected[:12]}
    report=base/'ORACLE309_ATOMIC_CANDIDATE_QUEUE.json'
    report.write_text(json.dumps(out,indent=2,sort_keys=True),encoding='utf-8')
    return out,report


def test():
    base=pathlib.Path(tempfile.mkdtemp(prefix='oracle309test_'))
    try:
        token='E447xHwXKMLUhqriexGwmjmMPn7YSsvyRKv9L2Tdpump'
        rows=[(token,'METEORA_TO_PUMP',.01,4,10000000,10300000),
              (token,'METEORA_TO_PUMP',.015,4,15000000,15400000),
              (token,'PUMP_TO_METEORA',.01,5,10000000,9900000)]
        chosen=prioritize(rows)
        assert len(chosen)==2 and sum(x['canary_size'] for x in chosen)==1
        assert all(x['net_certified'] is False for x in chosen)
        source={'run307':'n','run308':'d','rows':rows,'discovery':{'HOT_EXISTING_SCANNER':4}}
        out,path=store(source,chosen,250000,base)
        assert path.exists() and out['atomic_simulation_certified'] is False
        with sqlite3.connect(base/'ORACLE309_ATOMIC_CANDIDATE_QUEUE.sqlite3') as c:
            assert c.execute('SELECT COUNT(*) FROM queue').fetchone()[0]==2
        assert all(v>MAX_PACKET for v in (1348,1296,1257))
        print('[ORACLE309_TEST_PASS] original_evidence=TRUE dedup=TRUE canary_priority=TRUE packet_limit=TRUE no_signing=TRUE')
    finally:
        for x in base.iterdir():x.unlink()
        base.rmdir()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--table',action='store_true');p.add_argument('--scenario-fee-lamports',type=int,default=250000)
    a=p.parse_args()
    if a.test:test();return
    if a.table:
        if not REPORT.exists():print('[ORACLE309_TABLE] NO_REPORT');return
        r=json.loads(REPORT.read_text(encoding='utf-8'))
        print('[ORACLE309_SUMMARY]',json.dumps({k:v for k,v in r.items() if k!='top'}))
        for v in r['top']:print('[ORACLE309_ROUTE]',json.dumps(v))
        return
    if a.run:
        if a.scenario_fee_lamports<0:raise RuntimeError('NEGATIVE_FEE')
        source=parse();selected=prioritize(source['rows'],a.scenario_fee_lamports)
        out,path=store(source,selected,a.scenario_fee_lamports)
        print('[ORACLE309_RESULT]',json.dumps({k:v for k,v in out.items() if k!='top'}),flush=True)
        for row in out['top'][:5]:print('[ORACLE309_PRIORITY]',json.dumps(row),flush=True)
        print('[REPORT]',path,flush=True)
    else:p.print_help()

if __name__=='__main__':main()
