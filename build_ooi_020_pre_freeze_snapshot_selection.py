"""ooi_020_pre_freeze_snapshot_selection: existing Oracle OOS live-observation boundary."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_020_pre_freeze_snapshot_selection.py'
TEST = ROOT / 'test_ooi_020_pre_freeze_snapshot_selection.py'
PREVIOUS = ROOT / 'test_ooi_019_retained_evidence_snapshot.py'
PINS = {}
MODULE_SOURCE = '"""Select only an archived snapshot known no later than candidate freeze."""\nfrom pathlib import Path\nfrom .ooi_019_retained_evidence_snapshot import ARCHIVE, load_snapshot\nfrom .ooi_015_verified_slop_evidence_snapshot import timestamp\nfrom .ooi_016_asof_comparable_statistics import EvidencePolicy\n\nEXECUTION_AUTHORITY = False\n\ndef archived_snapshots(root=None):\n    directory = Path(root or Path.cwd()).resolve() / ARCHIVE\n    snapshots = [load_snapshot(p) for p in sorted(directory.glob(\'*.json\'))]\n    return tuple(sorted(snapshots, key=lambda s: (timestamp(s.captured_at), s.snapshot_hash)))\n\ndef select_pre_freeze_snapshot(frozen_at, snapshots, policy=None):\n    policy = policy or EvidencePolicy()\n    policy.validate()\n    cutoff = timestamp(frozen_at)\n    known = []\n    for snapshot in snapshots:\n        snapshot.rows()\n        if timestamp(snapshot.captured_at) <= cutoff:\n            known.append(snapshot)\n    if not known:\n        return None, \'NO_RETAINED_PRE_FREEZE_SNAPSHOT\'\n    selected = max(known, key=lambda s: (timestamp(s.captured_at), s.snapshot_hash))\n    if (cutoff - timestamp(selected.captured_at)).total_seconds() > policy.max_snapshot_age_seconds:\n        return None, \'STALE_PRE_FREEZE_SNAPSHOT\'\n    return selected, None\n'
TEST_SOURCE = "import importlib\nimport tempfile\nfrom dataclasses import replace\nfrom test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,require,E\nfrom test_ooi_019_retained_evidence_snapshot import A\nS=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_020_pre_freeze_snapshot_selection')\n\ndef timed(s, when):\n    body=dict(captured_at=when,rows_json=s.rows_json,prediction_ledger_hash=s.prediction_ledger_hash,\n              resolution_ledger_hash=s.resolution_ledger_hash,execution_authority=False)\n    return E.EvidenceSnapshot(snapshot_hash=E.digest(body),**body)\n\ndef main():\n    with tempfile.TemporaryDirectory() as root:\n        fixture(root);early=snapshot(root);late=timed(early,'2026-09-17T00:00:30+00:00')\n        A.retain_snapshot(late,root);A.retain_snapshot(early,root)\n        saved=S.archived_snapshots(root)\n        selected,reason=S.select_pre_freeze_snapshot('2026-09-17T00:00:10+00:00',saved)\n        require(selected==early and reason is None,'future snapshot displaced prior evidence')\n        selected2,_=S.select_pre_freeze_snapshot('2026-09-17T00:00:10+00:00',S.archived_snapshots(root))\n        require(selected2==selected,'restart evidence selection changed')\n        none,reason=S.select_pre_freeze_snapshot('2026-09-16T23:59:59+00:00',saved)\n        require(none is None and reason=='NO_RETAINED_PRE_FREEZE_SNAPSHOT','future-only archive admitted')\n        none,reason=S.select_pre_freeze_snapshot('2026-09-17T02:00:00+00:00',saved)\n        require(none is None and reason=='STALE_PRE_FREEZE_SNAPSHOT','stale archive admitted')\n        (Path(root)/A.ARCHIVE/'partial.tmp').write_text('partial crash write')\n        require(len(S.archived_snapshots(root))==2,'temporary write treated as retained snapshot')\n    print('[PASS] OOI-020 pre-freeze selection, restart stability, future/stale HOLD, incomplete-write exclusion')\n    print('[PASS] execution_authority=FALSE')\n\nfrom pathlib import Path\nif __name__=='__main__':main()\n"
INSTALL_TEST_ARGS = []

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def clear_cache():
    cache = TARGET.parent / '__pycache__'
    if cache.is_dir():
        for item in cache.glob(TARGET.stem + '.*.pyc'):
            item.unlink()

def atomic(path, raw):
    temp = path.with_name(path.name + '.ooi_020_pre_freeze_snapshot_selection.tmp')
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
    print('[PASS] OOI_020_PRE_FREEZE_SNAPSHOT_SELECTION installed; deterministic checks passed', flush=True)
    print('[NEXT] Run ' + TEST.name + ' exactly as supplied; execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI_020_PRE_FREEZE_SNAPSHOT_SELECTION: ' + str(exc), flush=True)
        print('[STOP] Do not run the next installer; return complete output', flush=True)
        sys.exit(1)
