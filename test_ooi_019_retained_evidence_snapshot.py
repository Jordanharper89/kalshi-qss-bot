import importlib
import sys
import tempfile
from pathlib import Path
from test_ooi_015_verified_slop_evidence_snapshot import fixture, snapshot, require, E
A=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_019_retained_evidence_snapshot')

def fixture_checks():
    with tempfile.TemporaryDirectory() as root:
        fixture(root);s=snapshot(root)
        ledgers=[Path(root)/E.PREDICTIONS,Path(root)/E.RESOLUTIONS]
        before=[p.read_bytes() for p in ledgers]
        p=A.retain_snapshot(s,root);raw=p.read_bytes()
        require(A.load_snapshot(p)==s,'snapshot roundtrip differs')
        require(A.retain_snapshot(s,root)==p and p.read_bytes()==raw,'snapshot retention not idempotent')
        require([p.read_bytes() for p in ledgers]==before,'SLOP ledgers mutated')
        p.write_text('{}')
        try:A.retain_snapshot(s,root)
        except ValueError:pass
        else:raise AssertionError('corrupted immutable snapshot overwritten')
    print('[PASS] OOI-019 durable derived snapshot, exact readback, collision guard; source ledgers untouched')

def physical_check():
    root=Path(__file__).resolve().parent
    s=A.capture_and_retain(root)
    print('[PHYSICAL_EVIDENCE_ROWS]',len(s.rows()))
    print('[CAPTURED_AT]',s.captured_at)
    print('[SNAPSHOT_HASH]',s.snapshot_hash)
    print('[PASS] real SLOP snapshot read and retained before future candidate freezes')
    print('[SCOPE] Evidence readback only; live candidate admission not certified; execution_authority=FALSE')

if __name__=='__main__':
    fixture_checks()
    if '--fixture-only' not in sys.argv:physical_check()
