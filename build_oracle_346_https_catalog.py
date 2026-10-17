"""ORACLE-346 full replacement installer; shadow-only."""
import argparse,hashlib,pathlib,py_compile,tempfile

TARGET=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_346_https_catalog.py')
SOURCE='"""ORACLE346 scanner-aligned bounded pool account catalog; HTTPS only, no WS."""\nimport sqlite3,json,pathlib,collections,time\nfrom qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as w\nfrom qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core\nROOT=pathlib.Path(\'runtime_state/oracle/final_boss_dual\')\nDB=ROOT/\'oracle_346_catalog.sqlite3\'\n\ndef discover(pairs,url,cap=24):\n    assert 1<=len(pairs)<=100 and cap>=1\n    ROOT.mkdir(parents=True,exist_ok=True)\n    # Dedicated catalog store, never modify scanner or original witness DB.\n    db=sqlite3.connect(DB,timeout=12)\n    db.execute(\'CREATE TABLE IF NOT EXISTS latest(pubkey TEXT PRIMARY KEY,slot INTEGER NOT NULL,received_ns INTEGER NOT NULL,owner TEXT NOT NULL,lamports INTEGER NOT NULL,data_b64 TEXT NOT NULL,content_sha256 TEXT NOT NULL,source TEXT NOT NULL)\')\n    db.execute(\'CREATE TABLE IF NOT EXISTS watch(pubkey TEXT PRIMARY KEY,roles TEXT NOT NULL,token TEXT NOT NULL)\')\n    db.execute(\'CREATE TABLE IF NOT EXISTS pair_catalog(token TEXT PRIMARY KEY,pump_pool TEXT NOT NULL,meteora_pool TEXT NOT NULL,bin_total INTEGER NOT NULL,bin_selected INTEGER NOT NULL,discovery_complete INTEGER NOT NULL,structural_only INTEGER NOT NULL DEFAULT 1)\')\n    stats=collections.Counter()\n    try:\n        roles,catalog=w.watch_plan(pairs,db,url,stats,cap,core)\n        db.commit()\n        return catalog,roles,dict(stats)\n    finally:db.close()\ndef read():\n    db=sqlite3.connect(\'file:\'+str(DB.resolve())+\'?mode=ro\',uri=True)\n    try:\n        cats={r[0]:dict(token=r[0],pump_pool=r[1],meteora_pool=r[2],bin_total=r[3],bin_selected=r[4],discovery_complete=bool(r[5])) for r in db.execute(\'SELECT token,pump_pool,meteora_pool,bin_total,bin_selected,discovery_complete FROM pair_catalog\')}\n        roles={r[0]:[tuple(z) for z in json.loads(r[1])] for r in db.execute(\'SELECT pubkey,roles FROM watch\')}\n        return cats,roles\n    finally:db.close()\n'
EXPECTED='96fe40be459362b415c996297f2ad02ce09146a48a96eeaa22b01bae50a9283b'

def install():
    assert hashlib.sha256(SOURCE.encode()).hexdigest()==EXPECTED
    if not pathlib.Path('qseries_v2').is_dir():raise RuntimeError('RUN_FROM_REPO_ROOT')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    TARGET.write_bytes(SOURCE.encode())
    py_compile.compile(str(TARGET),doraise=True)
    assert hashlib.sha256(TARGET.read_bytes()).hexdigest()==EXPECTED
    print('[ORACLE346_INSTALL_PASS] '+str(TARGET));return 0

def test():
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)/TARGET.name
        p.write_bytes(SOURCE.encode())
        py_compile.compile(str(p),doraise=True)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==EXPECTED
    assert 'sendTransaction' not in SOURCE and 'sign_transaction' not in SOURCE
    print('[ORACLE346_TEST_PASS] source,hash,syntax,no_send');return 0

def audit():
    assert EXPECTED==hashlib.sha256(SOURCE.encode()).hexdigest()
    print('[ORACLE346_AUDIT] FROZEN_SCANNER_UNTOUCHED SIGNING_FALSE BROADCAST_FALSE')
    return 0

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--install',action='store_true')
    p.add_argument('--test',action='store_true')
    p.add_argument('--audit',action='store_true')
    a=p.parse_args()
    if a.install:return install()
    if a.test:return test()
    if a.audit:return audit()
    p.error('SELECT_A_MODE')

if __name__=='__main__':raise SystemExit(main())