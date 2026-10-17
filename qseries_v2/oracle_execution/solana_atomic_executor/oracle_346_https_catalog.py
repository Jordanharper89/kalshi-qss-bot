"""ORACLE346 scanner-aligned bounded pool account catalog; HTTPS only, no WS."""
import sqlite3,json,pathlib,collections,time
from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as w
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
ROOT=pathlib.Path('runtime_state/oracle/final_boss_dual')
DB=ROOT/'oracle_346_catalog.sqlite3'

def discover(pairs,url,cap=24):
    assert 1<=len(pairs)<=100 and cap>=1
    ROOT.mkdir(parents=True,exist_ok=True)
    # Dedicated catalog store, never modify scanner or original witness DB.
    db=sqlite3.connect(DB,timeout=12)
    db.execute('CREATE TABLE IF NOT EXISTS latest(pubkey TEXT PRIMARY KEY,slot INTEGER NOT NULL,received_ns INTEGER NOT NULL,owner TEXT NOT NULL,lamports INTEGER NOT NULL,data_b64 TEXT NOT NULL,content_sha256 TEXT NOT NULL,source TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS watch(pubkey TEXT PRIMARY KEY,roles TEXT NOT NULL,token TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS pair_catalog(token TEXT PRIMARY KEY,pump_pool TEXT NOT NULL,meteora_pool TEXT NOT NULL,bin_total INTEGER NOT NULL,bin_selected INTEGER NOT NULL,discovery_complete INTEGER NOT NULL,structural_only INTEGER NOT NULL DEFAULT 1)')
    stats=collections.Counter()
    try:
        roles,catalog=w.watch_plan(pairs,db,url,stats,cap,core)
        db.commit()
        return catalog,roles,dict(stats)
    finally:db.close()
def read():
    db=sqlite3.connect('file:'+str(DB.resolve())+'?mode=ro',uri=True)
    try:
        cats={r[0]:dict(token=r[0],pump_pool=r[1],meteora_pool=r[2],bin_total=r[3],bin_selected=r[4],discovery_complete=bool(r[5])) for r in db.execute('SELECT token,pump_pool,meteora_pool,bin_total,bin_selected,discovery_complete FROM pair_catalog')}
        roles={r[0]:[tuple(z) for z in json.loads(r[1])] for r in db.execute('SELECT pubkey,roles FROM watch')}
        return cats,roles
    finally:db.close()
