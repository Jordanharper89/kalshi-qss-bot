"""ooi_021_existing_oos_observation_cycle: existing Oracle OOS live-observation boundary."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_021_existing_oos_observation_cycle.py'
TEST = ROOT / 'test_ooi_021_existing_oos_observation_cycle.py'
PREVIOUS = ROOT / 'test_ooi_020_pre_freeze_snapshot_selection.py'
PINS = {}
MODULE_SOURCE = '"""One read-only observation cycle using the existing source ledger and OOS."""\nfrom datetime import timedelta\nfrom pathlib import Path\nfrom .ooi_015_verified_slop_evidence_snapshot import PREDICTIONS, RESOLUTIONS, thesis_matches, timestamp, utc_now\nfrom .ooi_020_pre_freeze_snapshot_selection import archived_snapshots, select_pre_freeze_snapshot\nfrom .ooi_007b_slop_existing_oos_intake import OpportunityOperatingSystem, process_evidence_backed_slop\n\nEXECUTION_AUTHORITY = False\n\ndef read_current_sources(root):\n    from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions\n    from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_020_prospective_resolution_ledger import read_resolution_dicts\n    paths = [root / PREDICTIONS, root / RESOLUTIONS]\n    before = [p.read_bytes() for p in paths]\n    predictions = read_predictions(root)\n    resolutions = read_resolution_dicts(root)\n    if before != [p.read_bytes() for p in paths]:\n        raise RuntimeError(\'Source ledgers changed during observation cycle\')\n    return predictions, {str(r[\'prediction_id\']) for r in resolutions}\n\ndef is_owned_record(record):\n    op = record.opportunity\n    return (getattr(op, \'read_only\', None) is True and\n            op.metadata.get(\'source_revision\') == \'SLOP_078B\' and\n            op.metadata.get(\'execution_authority\') is False and\n            \'historical_evidence\' in op.metadata)\n\ndef observation_cycle(root, oos, evaluated_at=None, policy=None):\n    if not isinstance(oos, OpportunityOperatingSystem):\n        raise TypeError(\'Caller-owned existing OOS required\')\n    root = Path(root).resolve()\n    now = timestamp(evaluated_at or utc_now())\n    predictions, resolved_ids = read_current_sources(root)\n    snapshots = archived_snapshots(root)\n    source_ids = {str(p.prediction_id) for p in predictions}\n    removed = []\n    for record in list(oos.all_records()):\n        if not is_owned_record(record):\n            continue\n        op = record.opportunity\n        expiry = timestamp(op.time_window.valid_until)\n        reason = (\'RESOLVED\' if op.opportunity_id in resolved_ids else\n                  \'EXPIRED\' if now >= expiry else\n                  \'SOURCE_PREDICTION_MISSING\' if op.opportunity_id not in source_ids else None)\n        if reason:\n            oos.remove(record.fingerprint)\n            removed.append({\'opportunity_id\': op.opportunity_id, \'reason\': reason})\n    decisions = []\n    totals = {\'fresh_candidates\': 0, \'accepted\': 0, \'registered\': 0, \'duplicates\': 0,\n              \'held\': 0, \'expired_skipped\': 0, \'resolved_skipped\': 0, \'future_skipped\': 0}\n    for op in sorted(predictions, key=lambda p: (timestamp(p.frozen_at), str(p.prediction_id))):\n        pid = str(op.prediction_id)\n        if pid in resolved_ids:\n            totals[\'resolved_skipped\'] += 1\n            continue\n        start = timestamp(op.frozen_at)\n        if now < start:\n            totals[\'future_skipped\'] += 1\n            continue\n        if now >= start + timedelta(seconds=60):\n            totals[\'expired_skipped\'] += 1\n            continue\n        totals[\'fresh_candidates\'] += 1\n        if not thesis_matches(op):\n            totals[\'held\'] += 1\n            decisions.append({\'prediction_id\': pid, \'status\': \'HOLD\', \'reasons\': [\'THESIS_MISMATCH\']})\n            continue\n        snapshot, reason = select_pre_freeze_snapshot(op.frozen_at, snapshots, policy)\n        if snapshot is None:\n            totals[\'held\'] += 1\n            decisions.append({\'prediction_id\': pid, \'status\': \'HOLD\', \'reasons\': [reason]})\n            continue\n        result = process_evidence_backed_slop([op], snapshot, oos, policy=policy, evaluated_at=now.isoformat())\n        pipe = result[\'pipeline\']\n        admitted = result[\'accepted_count\']\n        totals[\'accepted\'] += admitted\n        totals[\'registered\'] += pipe.registered_count\n        totals[\'duplicates\'] += pipe.duplicate_count\n        totals[\'held\'] += 1 - admitted\n        failed_checks = [c.check_id for report in result[\'validation_reports\'] for c in report.checks\n                         if not c.passed and getattr(c.severity, \'value\', c.severity) == \'fail\']\n        decisions.append({\'prediction_id\': pid, \'status\': \'RESEARCH_ACCEPTED\' if admitted else \'HOLD\',\n            \'snapshot_hash\': snapshot.snapshot_hash, \'snapshot_captured_at\': snapshot.captured_at,\n            \'frozen_at\': str(op.frozen_at), \'validation_failed_checks\': failed_checks,\n            \'reasons\': [reason for held in result[\'held\'] for reason in held[\'reasons\']]})\n    own_records = [r for r in oos.all_records() if is_owned_record(r)]\n    return dict(totals, evaluated_at=now.isoformat(), source_prediction_count=len(predictions),\n        retained_snapshot_count=len(snapshots), decisions=decisions, removed=removed,\n        active_owned_count=len(own_records),\n        active_owned_fingerprints=sorted(r.fingerprint for r in own_records),\n        read_only=True, execution_authority=False)\n'
TEST_SOURCE = "import importlib\nimport json\nimport tempfile\nfrom dataclasses import asdict\nfrom pathlib import Path\nfrom test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,candidate,require,E\nfrom test_ooi_019_retained_evidence_snapshot import A\nfrom test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock\nC=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_021_existing_oos_observation_cycle')\n\ndef append_candidate(root, op):\n    p=Path(root)/E.PREDICTIONS\n    doc=json.loads(p.read_text());doc['predictions'].append(asdict(op));p.write_text(json.dumps(doc))\n\ndef main():\n    with tempfile.TemporaryDirectory() as root, fixed_validation_clock():\n        fixture(root);A.retain_snapshot(snapshot(root),root);op=candidate();append_candidate(root,op)\n        oos=C.OpportunityOperatingSystem()\n        first=C.observation_cycle(root,oos,evaluated_at='2026-09-17T00:00:20+00:00')\n        require(first['accepted']==first['registered']==first['active_owned_count']==1,'live-source fixture not admitted')\n        repeat=C.observation_cycle(root,oos,evaluated_at='2026-09-17T00:00:20+00:00')\n        require(repeat['duplicates']==1 and repeat['active_owned_count']==1,'duplicate registry entry')\n        fingerprints=repeat['active_owned_fingerprints']\n        expired=C.observation_cycle(root,oos,evaluated_at='2026-09-17T00:01:10+00:00')\n        require(expired['active_owned_count']==0 and len(expired['removed'])==1,'expired record remained')\n        fresh_oos=C.OpportunityOperatingSystem()\n        C.observation_cycle(root,fresh_oos,evaluated_at='2026-09-17T00:00:20+00:00')\n        p=Path(root)/E.RESOLUTIONS;doc=json.loads(p.read_text())\n        doc['resolutions'].append(dict(prediction_id=op.prediction_id,outcome='TARGET_FIRST',gross_return=.10,net_return=.08,\n            terminal_return=.10,mfe=.10,mae=0,friction_bps=200,execution_authority=False));p.write_text(json.dumps(doc))\n        resolved=C.observation_cycle(root,fresh_oos,evaluated_at='2026-09-17T00:00:30+00:00')\n        require(resolved['active_owned_count']==0 and resolved['fresh_candidates']==0,'resolved candidate remained active')\n    with tempfile.TemporaryDirectory() as root, fixed_validation_clock():\n        fixture(root);append_candidate(root,candidate());oos=C.OpportunityOperatingSystem()\n        report=C.observation_cycle(root,oos,evaluated_at='2026-09-17T00:00:20+00:00')\n        require(report['held']==1 and report['active_owned_count']==0,'missing snapshot silently bypassed')\n    print('[PASS] OOI-021 native prediction ledger -> existing OOS; deduplication, expiry, resolution removal, HOLD')\n    print('[SCOPE] Deterministic temporary-source fixture; execution_authority=FALSE')\n\nif __name__=='__main__':main()\n"
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
    temp = path.with_name(path.name + '.ooi_021_existing_oos_observation_cycle.tmp')
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
    print('[PASS] OOI_021_EXISTING_OOS_OBSERVATION_CYCLE installed; deterministic checks passed', flush=True)
    print('[NEXT] Run ' + TEST.name + ' exactly as supplied; execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI_021_EXISTING_OOS_OBSERVATION_CYCLE: ' + str(exc), flush=True)
        print('[STOP] Do not run the next installer; return complete output', flush=True)
        sys.exit(1)
