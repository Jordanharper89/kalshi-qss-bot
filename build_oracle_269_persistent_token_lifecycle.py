"""ORACLE-269 persistent HOT/ACTIVE/COLD research lifecycle; no network/orders."""
import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

BASE = Path('runtime_state/oracle/oracle_live_execution')
DB = BASE / 'ORACLE269_TOKEN_LIFECYCLE.json'
INPUTS = (BASE/'ORACLE268_CANONICAL_RAW.json', BASE/'ORACLE258_ROTATION_RAW.json')
EVENTS = BASE/'ORACLE269_ACCOUNT_EVENTS.jsonl'
GRID = [round(.010 + .005*i, 3) for i in range(19)]
DIRECTIONS = ('PUMP_TO_METEORA','METEORA_TO_PUMP')


def new_db():
    return {'build':'ORACLE269','schema':1,'tokens':{},'imports':{},'events_seen':{},'last_updated_utc':None,
            'scanner_changed':False,'execution_admission':False,'signing':False,'broadcast':False}


def load(path):
    if not path.exists(): return new_db()
    data=json.loads(path.read_text(encoding='utf-8'))
    if data.get('build')!='ORACLE269' or data.get('schema')!=1 or not isinstance(data.get('tokens'),dict):
        raise RuntimeError('UNTRUSTED_LIFECYCLE_STATE')
    if any(data.get(k) is not False for k in ('execution_admission','signing','broadcast')):
        raise RuntimeError('ARMED_STATE_REFUSED')
    return data


def token_state(db, mint):
    if not isinstance(mint,str) or not 32<=len(mint)<=44 or not all(c in '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz' for c in mint):
        return None
    return db['tokens'].setdefault(mint,{'tier':'COLD','observations':0,'valid_full_fills':0,
        'positive_gross':0,'best_gross_lamports':None,'last_observed':None,
        'last_market_slot':None,'last_pool_fingerprint':None,'fresh_reprice_eligible':False,
        'unpriced_reason':None,'source_tags':[],'last_size_sol':None,'last_direction':None})


def observe(db, row):
    if not isinstance(row,dict): return False
    t=token_state(db,row.get('mint'))
    if t is None:return False
    t['observations']+=1
    t['last_observed']=row.get('sampled_at') if isinstance(row.get('sampled_at'),str) else t['last_observed']
    if 'CANONICAL_QUOTE' not in t['source_tags']:t['source_tags'].append('CANONICAL_QUOTE')
    if row.get('status')=='FULL_FILL_GROSS_MEASURED':
        qs=row.get('directions')
        size=row.get('size_sol')
        if type(size) not in (int,float) or not any(abs(size-s)<1e-9 for s in GRID):return True
        start=round(size*1_000_000_000)
        if not isinstance(qs,list) or len(qs)!=2 or {q.get('direction') for q in qs if isinstance(q,dict)}!=set(DIRECTIONS):return True
        if any(type(q.get('start_lamports')) is not int or q['start_lamports']!=start or
               type(q.get('end_lamports')) is not int or q['end_lamports']<=0 or
               type(q.get('gross_lamports')) is not int or q['gross_lamports']!=q['end_lamports']-start for q in qs):return True
        t['valid_full_fills']+=1
        t['unpriced_reason']=None
        for q in qs:
            gross=q['gross_lamports']
            if gross>0:t['positive_gross']+=1
            if t['best_gross_lamports'] is None or gross>t['best_gross_lamports']:
                t['best_gross_lamports']=gross
                t['last_size_sol']=size
                t['last_direction']=q['direction']
    else:
        reason=row.get('exception_code') or row.get('status')
        t['unpriced_reason']=str(reason)[:80] if reason else None
    # Historical gross observations do not grant fresh state or execution authority.
    if t['tier']=='COLD' and t['valid_full_fills']>0:t['tier']='ACTIVE'
    return True


def ingest(db,path):
    if not path.exists():return {'path':str(path),'status':'MISSING'}
    blob=path.read_bytes()
    sha=hashlib.sha256(blob).hexdigest()
    if db['imports'].get(path.name)==sha:return {'path':str(path),'status':'UNCHANGED'}
    data=json.loads(blob)
    if data.get('build')!='ORACLE241' or not isinstance(data.get('observations'),list) or any(data.get(x) is not False for x in ('signing','broadcast','execution_admission')):
        raise RuntimeError('UNTRUSTED_CANONICAL_SOURCE:'+path.name)
    if len(data['observations'])>200000:raise RuntimeError('SOURCE_TOO_LARGE')
    count=sum(observe(db,r) for r in data['observations'])
    db['imports'][path.name]=sha
    return {'path':str(path),'status':'IMPORTED','observations':count}


def market_event(db,event):
    """Accept only externally verified account updates; never infer from timestamps."""
    if not isinstance(event,dict):return 'REJECT_SHAPE'
    mint=event.get('mint'); t=token_state(db,mint)
    if t is None:return 'REJECT_MINT'
    slot=event.get('slot'); fingerprint=event.get('pool_fingerprint')
    if type(slot) is not int or slot<=0 or not isinstance(fingerprint,str) or not (16<=len(fingerprint)<=128):return 'REJECT_STATE_PROVENANCE'
    if not event.get('verified_ws_account_update') is True or event.get('source') not in ('PUMPSWAP_WS','METEORA_WS'):
        return 'REJECT_UNVERIFIED_EVENT'
    key=f"{mint}:{event['source']}"
    prior=db['events_seen'].get(key)
    if prior and (slot<prior['slot'] or (slot==prior['slot'] and fingerprint==prior['fingerprint'])):return 'NO_NEW_STATE'
    if prior and slot==prior['slot'] and fingerprint!=prior['fingerprint']:return 'REJECT_CONFLICTING_SLOT'
    db['events_seen'][key]={'slot':slot,'fingerprint':fingerprint}
    t['tier']='HOT'
    t['last_market_slot']=max(slot,t['last_market_slot'] or 0)
    t['last_pool_fingerprint']=fingerprint
    t['fresh_reprice_eligible']=True
    if event['source'] not in t['source_tags']:t['source_tags'].append(event['source'])
    return 'HOT_NEW_VERIFIED_STATE'


def demote(db, hot_after_seconds=180, cold_after_seconds=3600):
    """No wallclock-based freshness assertion; transitions use observation age only."""
    now=datetime.now(timezone.utc)
    for t in db['tokens'].values():
        stamp=t.get('last_observed')
        try:
            age=(now-datetime.fromisoformat(stamp.replace('Z','+00:00'))).total_seconds()
        except (ValueError,TypeError,AttributeError):continue
        if age>=cold_after_seconds:t['tier']='COLD';t['fresh_reprice_eligible']=False
        elif age>=hot_after_seconds and t['tier']=='HOT':t['tier']='ACTIVE';t['fresh_reprice_eligible']=False


def save(db,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    db['last_updated_utc']=datetime.now(timezone.utc).isoformat()
    fd,tmp=tempfile.mkstemp(prefix='.oracle269_',suffix='.tmp',dir=path.parent)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(db,f,indent=2,sort_keys=True);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)


def test():
    mint='A'*32; d=new_db()
    def q(direction,end):return {'direction':direction,'start_lamports':10000000,'end_lamports':end,'gross_lamports':end-10000000}
    row={'mint':mint,'size_sol':.01,'status':'FULL_FILL_GROSS_MEASURED','directions':[q(DIRECTIONS[0],9990000),q(DIRECTIONS[1],9999000)]}
    assert observe(d,row) and d['tokens'][mint]['tier']=='ACTIVE'
    assert market_event(d,{'mint':mint,'slot':123,'pool_fingerprint':'abc123def456abc123def456','source':'METEORA_WS','verified_ws_account_update':True})=='HOT_NEW_VERIFIED_STATE'
    assert market_event(d,{'mint':mint,'slot':123,'pool_fingerprint':'abc123def456abc123def456','source':'METEORA_WS','verified_ws_account_update':True})=='NO_NEW_STATE'
    assert market_event(d,{'mint':mint,'slot':124,'pool_fingerprint':'changed456abc123def456','source':'METEORA_WS','verified_ws_account_update':False})=='REJECT_UNVERIFIED_EVENT'
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)/'state.json';save(d,p);r=load(p)
        assert r['tokens'][mint]['tier']=='HOT' and r['tokens'][mint]['positive_gross']==0
        source=Path(folder)/'raw.json'
        source.write_text(json.dumps({'build':'ORACLE241','signing':False,'broadcast':False,'execution_admission':False,'observations':[row]}))
        assert ingest(r,source)['status']=='IMPORTED' and ingest(r,source)['status']=='UNCHANGED'
    assert len(GRID)==19 and GRID[0]==.010 and GRID[-1]==.100
    print('[ORACLE269_TEST_PASS] restart=TRUE dedup=TRUE hot_reactivation=TRUE 19_sizes=TRUE no_orders=TRUE')


def run():
    if os.getenv('QSB_LIVE_ARM','NO').upper()!='NO' or os.getenv('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('DISARMED_CHILD_ENV_REQUIRED')
    db=load(DB)
    imports=[ingest(db,p) for p in INPUTS]
    ev=BASE/'ORACLE269_ACCOUNT_EVENTS.jsonl'
    events={}
    if ev.exists():
        with ev.open(encoding='utf-8') as f:
            for i,line in enumerate(f):
                if i>=10000:raise RuntimeError('EVENT_FEED_LIMIT')
                if not line.strip():continue
                result=market_event(db,json.loads(line));events[result]=events.get(result,0)+1
        # Important: replay after restart is idempotent via per-account slot/fingerprint.
    # Don't demote HOT based on quote timestamp: event timestamp not supplied here.
    save(db,DB)
    counts={x:sum(t['tier']==x for t in db['tokens'].values()) for x in ('HOT','ACTIVE','COLD')}
    print('[ORACLE269_RESULT]',json.dumps({'build':'ORACLE269','imports':imports,'tokens':len(db['tokens']),
        'tiers':counts,'event_results':events,'reprice_eligible':sum(t['fresh_reprice_eligible'] for t in db['tokens'].values()),
        'net_profit_certified':False,'event_feed_connected':ev.exists(),'signing':False,'broadcast':False,
        'execution_admission':False,'status':'STAGED_EVENT_LIFECYCLE_NOT_CONNECTED_TO_LIVE_WS'},sort_keys=True))
    print('[REPORT]',DB)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--test',action='store_true');ap.add_argument('--run',action='store_true')
    a=ap.parse_args()
    if not(a.test or a.run):ap.error('Specify --test or --run')
    if a.test:test()
    if a.run:run()
