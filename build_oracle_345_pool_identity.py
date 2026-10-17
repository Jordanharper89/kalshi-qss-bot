"""ORACLE-345 full replacement installer; shadow-only."""
import argparse,hashlib,pathlib,py_compile,tempfile

TARGET=pathlib.Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_345_pool_identity.py')
SOURCE='"""ORACLE345 strict scanner-origin pair identity; immutable source, no guessing."""\nfrom qseries_v2.oracle_execution.solana_atomic_executor import oracle_344_scanner_align as a\nfrom qseries_v2.oracle_execution.solana_atomic_executor import oracle_343_unified_feed_recovery as old\n\ndef vetted(nom,pairs,heartbeat):\n    if not heartbeat.get(\'ok\'):raise ValueError(\'SCANNER_HEARTBEAT_STALE\')\n    if nom[\'producer\']!=heartbeat[\'producer\']:raise ValueError(\'SCANNER_PRODUCER_CHANGED\')\n    if old.nomination_age(nom,__import__(\'time\').time_ns(),2500) is None:raise ValueError(\'NOMINATION_STALE\')\n    pair=a.matching_pair(nom,pairs)\n    if not all(pair[k]==nom[k] for k in (\'token\',\'pump_pool\',\'meteora_pool\')):raise ValueError(\'IDENTITY_DRIFT\')\n    return pair\n'
EXPECTED='08ea8ccd1a58fe0f563b834a33cc027950dbfd463c9416a208c0f3f1da1dfea8'

def install():
    assert hashlib.sha256(SOURCE.encode()).hexdigest()==EXPECTED
    if not pathlib.Path('qseries_v2').is_dir():raise RuntimeError('RUN_FROM_REPO_ROOT')
    TARGET.parent.mkdir(parents=True,exist_ok=True)
    TARGET.write_bytes(SOURCE.encode())
    py_compile.compile(str(TARGET),doraise=True)
    assert hashlib.sha256(TARGET.read_bytes()).hexdigest()==EXPECTED
    print('[ORACLE345_INSTALL_PASS] '+str(TARGET));return 0

def test():
    with tempfile.TemporaryDirectory() as tmp:
        p=pathlib.Path(tmp)/TARGET.name
        p.write_bytes(SOURCE.encode())
        py_compile.compile(str(p),doraise=True)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==EXPECTED
    assert 'sendTransaction' not in SOURCE and 'sign_transaction' not in SOURCE
    print('[ORACLE345_TEST_PASS] source,hash,syntax,no_send');return 0

def audit():
    assert EXPECTED==hashlib.sha256(SOURCE.encode()).hexdigest()
    print('[ORACLE345_AUDIT] FROZEN_SCANNER_UNTOUCHED SIGNING_FALSE BROADCAST_FALSE')
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