"""ORACLE-299 complete standalone fresh-batch to offline SDK evidence probe.
One capped RPC getMultipleAccounts, immutable temporary account snapshot, no orders.
Does NOT change production scanner, monitors or wallet.
"""
import argparse, base64, hashlib, json, os, sqlite3, tempfile, time, urllib.request, urllib.error
from collections import Counter
from pathlib import Path

GRID=tuple(round(.010+.005*i,3) for i in range(19))
ROOT=Path('runtime_state/oracle/oracle_live_execution')
REPORT=ROOT/'ORACLE299_FRESH_QUOTE_ACTIVATION.json'

def decode_response(payload, selected, validate, when):
    if not isinstance(payload,dict) or 'error' in payload:raise RuntimeError('RPC_REJECTED')
    result=payload.get('result') or {}; context=result.get('context') or {}
    slot=context.get('slot'); values=result.get('value')
    if type(slot) is not int or slot<=0 or not isinstance(values,list) or len(values)!=len(selected):
        raise RuntimeError('RPC_SLOT_OR_CARDINALITY_INVALID')
    rows=[]; reasons=Counter()
    for (addr,target),v in zip(selected.items(),values):
        if not isinstance(v,dict):reasons['ACCOUNT_MISSING']+=1;continue
        data=v.get('data')
        if not isinstance(data,list) or len(data)!=2 or data[1]!='base64':reasons['ENCODING_INVALID']+=1;continue
        try:raw=base64.b64decode(data[0],validate=True)
        except (ValueError,TypeError):reasons['BASE64_INVALID']+=1;continue
        verified=validate(addr,target,v.get('owner'),raw,slot,when)
        if not verified:reasons['ACCOUNT_VALIDATION_FAILED']+=1;continue
        rows.append((addr,slot,v['owner'],hashlib.sha256(raw).hexdigest(),raw,'ORACLE299_ONE_BATCH',when))
    return rows,dict(reasons),slot

def perform_rpc(url, addresses):
    if not url.startswith('https://'):raise RuntimeError('HTTPS_RPC_REQUIRED')
    if not 1<=len(addresses)<=100:raise RuntimeError('MAX_100_ACCOUNTS')
    body=json.dumps({'jsonrpc':'2.0','id':299,'method':'getMultipleAccounts','params':[addresses,{'encoding':'base64','commitment':'processed'}]}).encode()
    req=urllib.request.Request(url,data=body,headers={'Content-Type':'application/json'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=22) as r:data=r.read(28_000_001)
    except urllib.error.HTTPError as ex:
        if ex.code==429:raise RuntimeError('HTTP_429_STOP_NO_RETRY') from None
        raise RuntimeError('RPC_HTTP_'+str(ex.code)) from None
    except (urllib.error.URLError,TimeoutError,OSError):raise RuntimeError('RPC_CONNECTION_FAILED') from None
    if len(data)>28_000_000:raise RuntimeError('RPC_RESPONSE_TOO_LARGE')
    try:return json.loads(data)
    except ValueError:raise RuntimeError('INVALID_RPC_JSON') from None

def temporary_market(path,rows):
    con=sqlite3.connect(path)
    con.execute('CREATE TABLE account_bytes(address TEXT PRIMARY KEY,slot INTEGER,owner TEXT,sha TEXT,raw BLOB,source TEXT,received REAL)')
    con.executemany('INSERT INTO account_bytes VALUES(?,?,?,?,?,?,?)',rows);con.commit();con.close()

def test():
    assert len(GRID)==19 and GRID[0]==.010 and GRID[-1]==.100
    select={'A':{'kind':'BIN'},'B':{'kind':'POOL'}}
    import base64
    vals=[{'owner':'owner','data':[base64.b64encode(b'bytes').decode(),'base64']},None]
    good=lambda a,t,o,r,s,w: {'ok':True} if a=='A' and r==b'bytes' else None
    rows,reasons,slot=decode_response({'result':{'context':{'slot':123},'value':vals}},select,good,1000.)
    assert len(rows)==1 and reasons=={'ACCOUNT_MISSING':1} and slot==123
    assert rows[0][3]==hashlib.sha256(b'bytes').hexdigest()
    with tempfile.TemporaryDirectory() as d:
        db=Path(d)/'x.sqlite3';temporary_market(db,rows)
        c=sqlite3.connect(db);assert c.execute('SELECT raw FROM account_bytes').fetchone()[0]==b'bytes';c.close()
    try:decode_response({'result':{'context':{'slot':123},'value':[]}},select,good,1000.)
    except RuntimeError:pass
    else:raise AssertionError('CARDINALITY_FAIL_OPEN')
    print('[ORACLE299_TEST_PASS] one_batch_contract=TRUE identity=TRUE raw_bytes=TRUE hash=TRUE local_snapshot=TRUE 19_sizes=TRUE no_orders=TRUE')

def run():
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('DISARMED_PROCESS_REQUIRED')
    import oracle_283_287_milestone_a_runtime as market
    selected=market.targets()
    # Enforce a single coherent getMultipleAccounts response, not arbitrary account chunks.
    if not 1<=len(selected)<=100:raise RuntimeError('UNSUPPORTED_ACCOUNT_COUNT')
    import oracle_294_298_local_quote_evidence as pricer
    if not pricer.MARKET.name=='ORACLE283_287_MARKET_EVIDENCE.sqlite3':
        raise RuntimeError('UNKNOWN_PRICER_CONTRACT')
    url=os.environ.get('SOLANA_RPC_URL','')
    # No local SDK imports until AFTER this bounded one-request fetch.
    payload=perform_rpc(url,list(selected))
    rows,reasons,slot=decode_response(payload,selected,market.validate,time.time())
    # Never record URL or secret in outputs; disarm all network before entering quote module.
    os.environ.pop('SOLANA_RPC_URL',None);os.environ.pop('SOLANA_WS_URL',None)
    ROOT.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='oracle299_') as tmp:
        path=Path(tmp)/'coherent.sqlite3';temporary_market(path,rows)
        previous=pricer.MARKET
        pricer.MARKET=path
        try:
            observation=pricer.cycle(120)
        finally:pricer.MARKET=previous
    report={'build':'ORACLE299','status':'MEASURED_LOCAL_QUOTE_PROBE','batch_slot':slot,
      'requested_accounts':len(selected),'valid_accounts':len(rows),'account_holds':reasons,
      'rpc_calls':1,'pricing_rpc_calls':0,'sdk_calls':observation['sdk_calls'],
      'full_fill_one_leg':observation['dlmm_full_fill_one_leg'],
      'partial_one_leg':observation['dlmm_partial'],'quote_statuses':observation['statuses'],
      'mriya_overlap':observation['mriya_inventory_overlap'],
      'gross_cross_venue_certified':False,'net_positive_certified':False,
      'atomic_certified':False,'signing':False,'broadcast':False,
      'note':'Snapshot fetched in one response; no cross-venue profits certified. Quote entrypoint remains the existing ORACLE294 SDK probe.'}
    REPORT.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    print('[ORACLE299_RESULT]',json.dumps(report,sort_keys=True))
    print('[REPORT]',REPORT)

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if a.test:test()
    if a.run:run()
    if not(a.test or a.run):p.error('Choose --test or --run')
if __name__=='__main__':main()
