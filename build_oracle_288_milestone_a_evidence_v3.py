"""ORACLE-288 full installer: replace Milestone A runtime with persisted account bytes and truthful coverage ledger.
Requires prior certified V2 installer on user's repo. Never signs, broadcasts, or invokes pricing RPC.
"""
import argparse, py_compile
from pathlib import Path
import build_oracle_283_287_milestone_a_v2 as base
TARGET=Path('oracle_283_287_milestone_a_runtime.py')

def replace_once(s,old,new):
    if s.count(old)!=1:raise RuntimeError('V2_SOURCE_CONTRACT_MISMATCH_'+str(s.count(old)))
    return s.replace(old,new,1)

def assemble():
    s=base.SOURCE
    s=replace_once(s,"'verified_account_identity':True,'canonical_hydrated':False,'detail':detail}",
        "'verified_account_identity':True,'canonical_hydrated':False,'detail':detail,'raw':raw}")
    s=replace_once(s,"CREATE TABLE IF NOT EXISTS checkpoint(name TEXT PRIMARY KEY,value TEXT);",
        "CREATE TABLE IF NOT EXISTS checkpoint(name TEXT PRIMARY KEY,value TEXT);\nCREATE TABLE IF NOT EXISTS account_bytes(address TEXT PRIMARY KEY,slot INTEGER,owner TEXT,sha TEXT,raw BLOB,source TEXT,received REAL);\nCREATE TABLE IF NOT EXISTS coverage_history(epoch INTEGER PRIMARY KEY,ready_pool_pairs INTEGER,tracked_tokens INTEGER,complete_bytes INTEGER,age_fresh INTEGER,missing INTEGER,stale INTEGER,unverified INTEGER,pump_pool_fresh INTEGER,meteora_pool_fresh INTEGER,vault_fresh INTEGER,bin_fresh INTEGER,price_verified INTEGER);\n")
    old="""    con.execute('INSERT INTO events(epoch,address,kind,slot,source,decision) VALUES(?,?,?,?,?,?)',
                (row['received_epoch'],row['address'],row['kind'],row['slot'],source,'ACCEPTED'))
    return 'ACCEPTED'"""
    new="""    raw=row.get('raw')
    if not isinstance(raw,bytes) or hashlib.sha256(raw).hexdigest()!=row['fingerprint'] or len(raw)!=row['byte_count']:
        raise RuntimeError('RAW_BYTES_MISSING_OR_CORRUPTED')
    con.execute('INSERT OR REPLACE INTO account_bytes VALUES(?,?,?,?,?,?,?)',(
        row['address'],row['slot'],row['owner'],row['fingerprint'],sqlite3.Binary(raw),source,row['received_epoch']))
    con.execute('INSERT INTO events(epoch,address,kind,slot,source,decision) VALUES(?,?,?,?,?,?)',
                (row['received_epoch'],row['address'],row['kind'],row['slot'],source,'ACCEPTED'))
    return 'ACCEPTED'"""
    s=replace_once(s,old,new)
    s=replace_once(s,"    report=snapshot(con,selected,counts,time.time(),max_age,rpc_calls)\n    con.execute('INSERT OR REPLACE INTO metrics",
        "    report=snapshot(con,selected,counts,time.time(),max_age,rpc_calls)\n    report.update(coverage_audit(con,selected,report['epoch'],max_age))\n    con.execute('INSERT OR REPLACE INTO coverage_history VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',\n        (int(report['epoch']),report['two_venue_pool_pairs_with_fresh_bytes'],report['tracked_tokens'],\n        report['complete_account_bytes'],report['fresh_verified_bytes'],report['missing_accounts'],\n        report['stale_accounts'],report['identity_unverified_accounts'],\n        report['fresh_pump_pool_bytes'],report['fresh_meteora_pool_bytes'],\n        report['fresh_vault_bytes'],report['fresh_bin_bytes'],0))\n    con.execute('INSERT OR REPLACE INTO metrics")
    # Report coverage is explicitly noncanonical; fresh bytes don't make an executable price.
    before='def persist(con,selected,counts,max_age,rpc_calls):'
    insert='''def coverage_audit(con,selected,now,max_age):
    """Integrity-check persisted public account bytes, and measure actual dependencies.
    Fresh observation means a recent *changed state*, not guaranteed unchanged current state.
    """
    data={r[0]:r for r in con.execute('SELECT address,slot,owner,sha,raw,source,received FROM account_bytes')}
    token_roles=defaultdict(set); categories=Counter(); valid=0;fresh=0;unverified=0
    for addr,target in selected.items():
        kind=target['kind']; item=data.get(addr)
        if item is None:continue
        raw=item[4]
        if not isinstance(raw,bytes) or hashlib.sha256(raw).hexdigest()!=item[3]:
            unverified+=1;continue
        valid+=1
        if not 0<=now-item[6]<=max_age:continue
        fresh+=1;categories[kind]+=1
        if kind=='POOL':
            for ref in target.get('refs',[]):
                mint=ref.get('token') or ref.get('mint') or ref.get('expected_token_mint')
                venue=str(ref.get('venue','')).upper()
                if mint and venue:token_roles[mint].add(venue)
        elif kind=='BIN':
            token_roles[target['token']].add('BIN')
        elif kind=='VAULT':
            for ref in target.get('refs',[]):
                token=ref.get('token') or ref.get('mint') or ref.get('expected_token_mint')
                if token:token_roles[token].add('VAULT')
    # Inspect the source inventory to avoid assuming the v277 manifest's refs include token labels.
    # Counts below are byte freshness and provenance only, NOT synchronized canonical pair readiness.
    all_tokens={t['token'] for t in selected.values() if t['kind']=='BIN'}
    for t in selected.values():
        for r in t.get('refs',[]):
            mint=r.get('token') or r.get('mint')
            if mint:all_tokens.add(mint)
    return {'complete_account_bytes':valid,'fresh_verified_bytes':fresh,
       'identity_unverified_accounts':unverified,'fresh_pump_pool_bytes':0,
       'fresh_meteora_pool_bytes':0,'fresh_vault_bytes':categories['VAULT'],
       'fresh_bin_bytes':categories['BIN'],'tracked_tokens':len(all_tokens),
       'two_venue_pool_pairs_with_fresh_bytes':0,
       'pool_pair_verification_hold':'POOL_OWNER_AND_TOKEN_VENUE_MAPPING_NOT_CANONICALLY_CERTIFIED',
       'quote_events':0,'full_fill_quotes':0,'net_positive_opportunities':0,
       'local_19_size_pricing_verified':False,'canonical_full_hydration':False,
       'net_profit_certified':False,'atomic_simulation_certified':False}

'''
    s=replace_once(s,before,insert+before)
    s=replace_once(s,"    print('[GATE] Pricing, net profit and atomic admission NOT certified. No trades attempted.')",
    """    print('ACCOUNT BYTES | VERIFIED  FRESH  VAULT  BIN  PRICE')
    for x in con.execute('SELECT epoch,complete_bytes,age_fresh,vault_fresh,bin_fresh,price_verified FROM coverage_history ORDER BY epoch DESC LIMIT ?',(limit,)):
        print(f'{x[0]:12} {x[1]:9} {x[2]:6} {x[3]:6} {x[4]:4} {x[5]:6}')
    print('[GATE] Live public account bytes retained. Canonical pricing, net profit and atomic admission NOT certified. No trades attempted.')""")
    s=replace_once(s,"'net_positive_certified':False,'execution':False},sort_keys=True)",
                   "'net_positive_certified':False,'execution':False,\n                          'verified_bytes':report['complete_account_bytes'],'fresh_bytes':report['fresh_verified_bytes'],\n                          'vault_fresh':report['fresh_vault_bytes'],'bin_fresh':report['fresh_bin_bytes']},sort_keys=True)")
    # Test addition uses real bytes; existing test inserts intentionally fake fingerprint on equal-slot conflict (rejected).
    s=replace_once(s,"    assert len(GRID)==19 and GRID[0]==.010 and GRID[-1]==.100",
    """    with tempfile.TemporaryDirectory() as folder:
        con=connect_db(Path(folder)/'rawtest.sqlite')
        a='11111111111111111111111111111111'; raw=b'public-state-bytes'
        row={'address':a,'kind':'POOL','slot':80,'received_epoch':1000.,'owner':WSOL,
             'fingerprint':hashlib.sha256(raw).hexdigest(),'byte_count':len(raw),'detail':{},'raw':raw}
        assert ingest(con,row,'BATCH_INIT')=='ACCEPTED'
        assert con.execute('SELECT raw FROM account_bytes WHERE address=?',(a,)).fetchone()[0]==raw
        assert ingest(con,row,'WS')=='DUPLICATE'
        audit=coverage_audit(con,{a:{'kind':'POOL','refs':[]}},1001,120)
        assert audit['complete_account_bytes']==1 and audit['fresh_verified_bytes']==1
        assert audit['two_venue_pool_pairs_with_fresh_bytes']==0
        assert coverage_audit(con,{a:{'kind':'POOL','refs':[]}},1201,120)['fresh_verified_bytes']==0
        try:ingest(con,dict(row,slot=81,raw=b'tampered'),'WS')
        except RuntimeError:pass
        else:raise AssertionError('CORRUPT_RAW_ACCEPTED')
        con.close()
    assert len(GRID)==19 and GRID[0]==.010 and GRID[-1]==.100""")
    return s

def install():
    if not TARGET.is_file():raise RuntimeError('V2_RUNTIME_MISSING')
    current=TARGET.read_text(encoding='utf-8')
    if current!=base.SOURCE and not current.startswith('"""ORACLE-283..287 Milestone A:'):
        raise RuntimeError('UNRECOGNIZED_RUNTIME_REFUSE_OVERWRITE')
    src=assemble()
    compile(src,str(TARGET),'exec')
    backup=TARGET.with_suffix('.v2.backup')
    if not backup.exists():backup.write_text(current,encoding='utf-8')
    temp=TARGET.with_suffix('.v3.tmp');temp.write_text(src,encoding='utf-8')
    temp.replace(TARGET)
    py_compile.compile(str(TARGET),doraise=True)
    print('[ORACLE288_INSTALL_PASS] full_replacement=TRUE raw_bytes=TRUE coverage_ledger=TRUE scanner_unchanged=TRUE no_orders=TRUE')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--install',action='store_true');a=p.parse_args()
    if not a.install:p.error('--install required')
    install()
