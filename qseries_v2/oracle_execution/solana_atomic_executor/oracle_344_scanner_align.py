"""ORACLE344 scanner bus and inventory alignment, read-only."""
import sqlite3,time,json,pathlib
from qseries_v2.oracle_execution.solana_atomic_executor import oracle_343_unified_feed_recovery as old
from qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness

def inventory(limit=500):
    return witness.inventory_pairs(limit)
def bus():
    db=sqlite3.connect(old.BUS.resolve().as_uri()+'?mode=ro',uri=True,timeout=3)
    db.execute('PRAGMA query_only=ON')
    return db
def validate_scanner(db):
    h=old.scanner_health(db,time.time_ns())
    if not h.get('ok'):raise RuntimeError('SCANNER_NOT_HEALTHY')
    return h
def matching_pair(nom,rows):
    k=(nom['token'],nom['pump_pool'],nom['meteora_pool'])
    matching=[p for p in rows if (p['token'],p['pump_pool'],p['meteora_pool'])==k]
    if len(matching)!=1:raise ValueError('CANDIDATE_POOL_NOT_IN_ADMITTED_INVENTORY')
    return matching[0]
def new_events(db,cursor):
    return old.next_nominations(db,cursor)
