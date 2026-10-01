"""ooi_019_retained_evidence_snapshot: existing Oracle OOS live-observation boundary."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_019_retained_evidence_snapshot.py'
TEST = ROOT / 'test_ooi_019_retained_evidence_snapshot.py'
PREVIOUS = ROOT / 'test_ooi_018_nonempty_existing_oos_handoff.py'
PINS = {'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_015_verified_slop_evidence_snapshot.py': '4526e05343b1182a2984fc369611e8c6a374129927b878dd543f180a8816fe15', 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_016_asof_comparable_statistics.py': '6f68723e529b87737dc7015485f4359668106a1baf9d86993c3d5fc92b8f65ff', 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_006_slop_universal_opportunity_materializer.py': '5be409c9892ec8e20f7d8dd0f5fa80ebd6a93b9593d1c064dcf6633bf29f4e0b', 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_007b_slop_existing_oos_intake.py': '8189373431dd622ddba91a72ab0d7d95838811fb2f219c1cf0acb5ca86e3142e'}
MODULE_SOURCE = '"""Retain immutable derived evidence snapshots; existing SLOP ledgers stay untouched."""\nfrom dataclasses import asdict\nfrom pathlib import Path\nimport json\nimport os\nimport tempfile\nfrom .ooi_015_verified_slop_evidence_snapshot import EvidenceSnapshot, read_evidence_snapshot, canonical\n\nEXECUTION_AUTHORITY = False\nARCHIVE = \'runtime_state/oracle_opportunity_intelligence/evidence_snapshots\'\n\ndef retain_snapshot(snapshot, root=None):\n    snapshot.rows()\n    root = Path(root or Path.cwd()).resolve()\n    directory = root / ARCHIVE\n    directory.mkdir(parents=True, exist_ok=True)\n    target = directory / (snapshot.snapshot_hash + \'.json\')\n    payload = canonical(asdict(snapshot)).encode(\'utf-8\')\n    if target.exists():\n        if target.read_bytes() != payload:\n            raise ValueError(\'Immutable snapshot path collision/corruption\')\n        return target\n    fd, name = tempfile.mkstemp(prefix=\'.snapshot-\', suffix=\'.tmp\', dir=str(directory))\n    try:\n        with os.fdopen(fd, \'wb\') as f:\n            f.write(payload)\n            f.flush()\n            os.fsync(f.fileno())\n        # Concurrent writers of the same content-addressed snapshot have identical bytes.\n        if target.exists() and target.read_bytes() != payload:\n            raise ValueError(\'Snapshot changed during publication\')\n        os.replace(name, target)\n    finally:\n        if os.path.exists(name):\n            os.unlink(name)\n    return target\n\ndef load_snapshot(path):\n    path = Path(path)\n    snapshot = EvidenceSnapshot(**json.loads(path.read_text(encoding=\'utf-8\')))\n    snapshot.rows()\n    if path.name != snapshot.snapshot_hash + \'.json\':\n        raise ValueError(\'Snapshot filename/hash mismatch\')\n    return snapshot\n\ndef capture_and_retain(root=None):\n    snapshot = read_evidence_snapshot(root)\n    retain_snapshot(snapshot, root)\n    return snapshot\n'
TEST_SOURCE = "import importlib\nimport sys\nimport tempfile\nfrom pathlib import Path\nfrom test_ooi_015_verified_slop_evidence_snapshot import fixture, snapshot, require, E\nA=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_019_retained_evidence_snapshot')\n\ndef fixture_checks():\n    with tempfile.TemporaryDirectory() as root:\n        fixture(root);s=snapshot(root)\n        ledgers=[Path(root)/E.PREDICTIONS,Path(root)/E.RESOLUTIONS]\n        before=[p.read_bytes() for p in ledgers]\n        p=A.retain_snapshot(s,root);raw=p.read_bytes()\n        require(A.load_snapshot(p)==s,'snapshot roundtrip differs')\n        require(A.retain_snapshot(s,root)==p and p.read_bytes()==raw,'snapshot retention not idempotent')\n        require([p.read_bytes() for p in ledgers]==before,'SLOP ledgers mutated')\n        p.write_text('{}')\n        try:A.retain_snapshot(s,root)\n        except ValueError:pass\n        else:raise AssertionError('corrupted immutable snapshot overwritten')\n    print('[PASS] OOI-019 durable derived snapshot, exact readback, collision guard; source ledgers untouched')\n\ndef physical_check():\n    root=Path(__file__).resolve().parent\n    s=A.capture_and_retain(root)\n    print('[PHYSICAL_EVIDENCE_ROWS]',len(s.rows()))\n    print('[CAPTURED_AT]',s.captured_at)\n    print('[SNAPSHOT_HASH]',s.snapshot_hash)\n    print('[PASS] real SLOP snapshot read and retained before future candidate freezes')\n    print('[SCOPE] Evidence readback only; live candidate admission not certified; execution_authority=FALSE')\n\nif __name__=='__main__':\n    fixture_checks()\n    if '--fixture-only' not in sys.argv:physical_check()\n"
INSTALL_TEST_ARGS = ['--fixture-only']

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def clear_cache():
    cache = TARGET.parent / '__pycache__'
    if cache.is_dir():
        for item in cache.glob(TARGET.stem + '.*.pyc'):
            item.unlink()

def atomic(path, raw):
    temp = path.with_name(path.name + '.ooi_019_retained_evidence_snapshot.tmp')
    require(not temp.exists(), 'Existing temporary file')
    try:
        temp.write_bytes(raw)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()

def main():
    require(TARGET.parent.is_dir() and PREVIOUS.is_file(), 'Existing subsystem or preceding test missing')
    for relative, expected in PINS.items():
        p = ROOT / relative
        require(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == expected,
                'Certified source differs: ' + relative)
    require(subprocess.run([sys.executable, '-B', str(PREVIOUS)], cwd=str(ROOT)).returncode == 0,
            'Preceding boundary failed; no production files changed')
    original = TARGET.read_bytes() if TARGET.exists() else None
    updated = MODULE_SOURCE.encode('utf-8')
    require(original is None or original == updated, 'Target differs; refusing overwrite')
    if TEST.exists():
        require(TEST.read_text(encoding='utf-8') == TEST_SOURCE, 'Existing test differs; refusing overwrite')
    compile(MODULE_SOURCE, str(TARGET), 'exec')
    compile(TEST_SOURCE, str(TEST), 'exec')
    if not TEST.exists():
        TEST.write_text(TEST_SOURCE, encoding='utf-8')
    changed = False
    try:
        require((TARGET.read_bytes() if TARGET.exists() else None) == original, 'Concurrent source change')
        atomic(TARGET, updated)
        changed = True
        clear_cache()
        require(subprocess.run([sys.executable, '-B', str(TEST)] + INSTALL_TEST_ARGS, cwd=str(ROOT)).returncode == 0,
                'Deterministic installation test failed')
    except BaseException:
        if changed and TARGET.exists() and TARGET.read_bytes() == updated and original is None:
            TARGET.unlink()
            clear_cache()
            print('[ROLLBACK] newly installed module removed', flush=True)
        raise
    print('[PASS] OOI_019_RETAINED_EVIDENCE_SNAPSHOT installed; deterministic checks passed', flush=True)
    print('[NEXT] Run ' + TEST.name + ' exactly as supplied; execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI_019_RETAINED_EVIDENCE_SNAPSHOT: ' + str(exc), flush=True)
        print('[STOP] Do not run the next installer; return complete output', flush=True)
        sys.exit(1)
