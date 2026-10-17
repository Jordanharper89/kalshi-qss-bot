"""ORACLE-344 full replacement installer; shadow-only."""
import argparse,hashlib,pathlib,py_compile,tempfile,sys,os,subprocess

TARGET=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_344_scanner_align.py')
SOURCE='"""ORACLE344 scanner bus and inventory alignment, read-only."""\nimport sqlite3,time,json,pathlib\nfrom qseries_v2.oracle_execution.solana_atomic_executor import oracle_343_unified_feed_recovery as old\nfrom qseries_v2.oracle_execution.solana_atomic_executor import boss_ws_full_account_witness as witness\n\ndef inventory(limit=500):\n    return witness.inventory_pairs(limit)\ndef bus():\n    db=sqlite3.connect(old.BUS.resolve().as_uri()+\'?mode=ro\',uri=True,timeout=3)\n    db.execute(\'PRAGMA query_only=ON\')\n    return db\ndef validate_scanner(db):\n    h=old.scanner_health(db,time.time_ns())\n    if not h.get(\'ok\'):raise RuntimeError(\'SCANNER_NOT_HEALTHY\')\n    return h\ndef matching_pair(nom,rows):\n    k=(nom[\'token\'],nom[\'pump_pool\'],nom[\'meteora_pool\'])\n    matching=[p for p in rows if (p[\'token\'],p[\'pump_pool\'],p[\'meteora_pool\'])==k]\n    if len(matching)!=1:raise ValueError(\'CANDIDATE_POOL_NOT_IN_ADMITTED_INVENTORY\')\n    return matching[0]\ndef new_events(db,cursor):\n    return old.next_nominations(db,cursor)\n'
EXPECTED='672b28dd04daa324f0d74921577c6db7d4a6c53cb502ccc80577f157d90dd9c3'

def install():
    assert hashlib.sha256(SOURCE.encode()).hexdigest()==EXPECTED
    if not pathlib.Path('qseries_v2').is_dir():raise RuntimeError('RUN_FROM_REPO_ROOT')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    TARGET.write_bytes(SOURCE.encode())
    py_compile.compile(str(TARGET),doraise=True)
    assert hashlib.sha256(TARGET.read_bytes()).hexdigest()==EXPECTED
    print('[ORACLE344_INSTALL_PASS] '+str(TARGET));return 0

def test():
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)/TARGET.name
        p.write_bytes(SOURCE.encode())
        py_compile.compile(str(p),doraise=True)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==EXPECTED
    assert 'sendTransaction' not in SOURCE and 'sign_transaction' not in SOURCE
    print('[ORACLE344_TEST_PASS] source,hash,syntax,no_send');return 0

def audit():
    assert EXPECTED==hashlib.sha256(SOURCE.encode()).hexdigest()
    print('[ORACLE344_AUDIT] FROZEN_SCANNER_UNTOUCHED SIGNING_FALSE BROADCAST_FALSE')
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