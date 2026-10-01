"""ooi_017_evidence_backed_materializer: grounded in the supplied physical source contracts."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_006_slop_universal_opportunity_materializer.py'
TEST = ROOT / 'test_ooi_017_evidence_backed_materializer.py'
PREVIOUS = ROOT / 'test_ooi_016_asof_comparable_statistics.py'
EXPECTED = '09741e4fce9ac99a72fad5fbda771ce949b9f31a0bc83391aafa04c839cde9e2'
PINS = {}
MODULE_SOURCE = '"""Existing SLOP materializer, extended with verified historical evidence."""\nfrom dataclasses import replace\nfrom datetime import timedelta\nfrom qseries_v2.oracle_intelligence.universal_opportunity_model.universal_opportunity import (\n    UniversalOpportunity, OpportunityType, OpportunityDirection, OpportunityStatus,\n    RiskLevel, OpportunityExecutionProfile, OpportunityTimeWindow, OpportunityEvidenceRef)\nfrom .ooi_015_verified_slop_evidence_snapshot import timestamp, utc_now\nfrom .ooi_016_asof_comparable_statistics import comparable_statistics\n\nREVISION = \'OOI_017_EVIDENCE_BACKED_EXISTING_MATERIALIZER\'\nEXECUTION_AUTHORITY = False\n\ndef materialize_slop(op, evidence_snapshot=None, policy=None, evaluated_at=None):\n    conditions = dict(op.conditions or {})\n    base = UniversalOpportunity(opportunity_id=str(op.prediction_id), market_id=str(op.pair_address),\n        market_type=\'SOLANA\', venue_id=\'SOLANA\', venue_name=\'Solana\',\n        opportunity_type=OpportunityType.UNKNOWN, direction=OpportunityDirection.BUY,\n        expected_value=0.0, expected_edge=0.0, confidence=0.0,\n        explanation=\'Prospective SLOP BUY_PRESSURE opportunity\',\n        supporting_prediction_ids=[str(op.prediction_id)], tags=[\'SLOP\', \'BUY_PRESSURE\', \'PROSPECTIVE\'],\n        raw_market={\'token_address\': str(op.token_address), \'pair_address\': str(op.pair_address)},\n        metadata={\'source_revision\': \'SLOP_078B\', \'frozen_at\': str(op.frozen_at), \'conditions\': conditions,\n            \'horizon_seconds\': op.horizon_seconds, \'target\': op.target, \'stop\': op.stop,\n            \'friction_bps\': op.friction_bps, \'execution_authority\': False},\n        read_only=True, status=OpportunityStatus.NEW, risk_level=RiskLevel.UNKNOWN,\n        execution=OpportunityExecutionProfile(required_execution_adapter=\'solana_wallet\'))\n    if evidence_snapshot is None:\n        return base\n    stats = comparable_statistics(op, evidence_snapshot, policy)\n    now = timestamp(evaluated_at or utc_now())\n    frozen = timestamp(op.frozen_at)\n    end = frozen + timedelta(seconds=60)\n    reasons = list(stats[\'reasons\'])\n    if now < frozen:\n        reasons.append(\'CANDIDATE_FREEZE_IS_IN_FUTURE\')\n    if now >= end:\n        reasons.append(\'CANDIDATE_EXPIRED\')\n    eligible = not reasons\n    metadata = dict(base.metadata, historical_evidence=stats,\n                    evidence_admission_eligible=eligible, evidence_hold_reasons=reasons,\n                    evaluated_at=now.isoformat(), calibrated_probability_available=False,\n                    execution_adapter_available=None, execution_adapter_invoked=False)\n    references = [OpportunityEvidenceRef(evidence_id=h, source=\'SLOP_067\',\n        evidence_type=\'historical_prospective_net_return\', created_at=evidence_snapshot.captured_at,\n        summary=\'Historical outcome; 200 bps friction already deducted\') for h in stats[\'evidence_hashes\']]\n    return replace(base,\n        expected_value=stats[\'historical_mean_net_return\'] if eligible else 0.0,\n        expected_edge=stats[\'historical_mean_net_return\'] if eligible else 0.0,\n        confidence=stats[\'historical_positive_net_wilson_lower\'] if eligible else 0.0,\n        explanation=(\'Historical comparable-cohort net return estimate; descriptive confidence, \'\n                     \'not a calibrated forecast probability.\'),\n        evidence_refs=references,\n        supporting_prediction_ids=[str(op.prediction_id)] + stats[\'supporting_prediction_ids\'],\n        metadata=metadata, risk_flags=[\'UNCALIBRATED_HISTORICAL_ESTIMATE\', \'ADAPTER_AVAILABILITY_UNVERIFIED\'],\n        time_window=OpportunityTimeWindow(discovered_at=frozen.isoformat(), valid_from=frozen.isoformat(),\n            valid_until=end.isoformat(), estimated_lifetime_seconds=60,\n            freshness_score=max(0.0, min(1.0, (end-now).total_seconds()/60))),\n        created_at=frozen.isoformat(), updated_at=now.isoformat())\n'
TEST_SOURCE = "import importlib\nimport tempfile\nfrom test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,candidate,require\nM=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_006_slop_universal_opportunity_materializer')\n\ndef main():\n    with tempfile.TemporaryDirectory() as root:\n        fixture(root);snap=snapshot(root);op=candidate()\n        legacy=M.materialize_slop(op)\n        require(legacy.confidence==legacy.expected_edge==0,'legacy no-evidence behavior changed')\n        a=M.materialize_slop(op,snap,evaluated_at=op.frozen_at)\n        b=M.materialize_slop(op,snap,evaluated_at=op.frozen_at)\n        require(a.to_dict()==b.to_dict() and a.fingerprint()==b.fingerprint(),'materialization not deterministic')\n        require(a.metadata['evidence_admission_eligible'] and abs(a.expected_edge-.055)<1e-12,'evidence mapping failed')\n        require(len(a.evidence_refs)==24 and len(a.supporting_prediction_ids)==25,'evidence lineage lost')\n        require(a.metadata['stop']==.05 and a.metadata['friction_bps']==200,'native frozen thesis changed')\n        require(a.execution.required_execution_adapter=='solana_wallet' and a.read_only,'adapter/authority contract failed')\n        require(a.metadata['execution_authority'] is False and a.metadata['execution_adapter_invoked'] is False,'authority changed')\n        expired=M.materialize_slop(op,snap,evaluated_at='2026-09-17T00:01:10+00:00')\n        require(not expired.metadata['evidence_admission_eligible'] and expired.confidence==expired.expected_edge==0,'expiry gate failed')\n        future=M.materialize_slop(candidate(frozen_at='2026-09-16T23:59:59+00:00'),snap,evaluated_at='2026-09-17T00:00:00+00:00')\n        require(not future.metadata['evidence_admission_eligible'],'future-data gate failed')\n    print('[PASS] OOI-017 existing materializer: supported historical edge/confidence, complete lineage, expiry/HOLD')\n    print('[SCOPE] Historical research estimate, not calibrated forecast; execution_authority=FALSE')\n\nif __name__=='__main__':main()\n"

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def clear_cache():
    cache = TARGET.parent / '__pycache__'
    if cache.is_dir():
        for item in cache.glob(TARGET.stem + '.*.pyc'):
            item.unlink()

def atomic(path, raw):
    temp = path.with_name(path.name + '.ooi_017_evidence_backed_materializer.tmp')
    require(not temp.exists(), 'Existing temporary file')
    try:
        temp.write_bytes(raw)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()

def main():
    require(TARGET.parent.is_dir() and PREVIOUS.is_file(), 'Existing subsystem or preceding test missing')
    for rel, expected in PINS.items():
        path = ROOT / rel
        require(path.is_file() and sha(path.read_bytes()) == expected,
                'Captured source differs: ' + rel)
    require(subprocess.run([sys.executable, '-B', str(PREVIOUS)], cwd=str(ROOT)).returncode == 0,
            'Preceding physical test failed; no files changed')
    original = TARGET.read_bytes() if TARGET.exists() else None
    updated = MODULE_SOURCE.encode('utf-8')
    require((original is None and EXPECTED is None) or
            (original is not None and sha(original) in (EXPECTED, sha(updated))),
            'Target differs from known predecessor; refusing overwrite')
    if TEST.exists():
        require(TEST.read_text(encoding='utf-8') == TEST_SOURCE, 'Existing test differs; refusing overwrite')
    compile(MODULE_SOURCE, str(TARGET), 'exec')
    compile(TEST_SOURCE, str(TEST), 'exec')
    if original is not None:
        backup = TARGET.with_name(TARGET.name + '.pre_ooi_017_evidence_backed_materializer_' + sha(original)[:12] + '.bak')
        require(not backup.exists() or backup.read_bytes() == original, 'Backup conflict')
        if not backup.exists():
            backup.write_bytes(original)
    if not TEST.exists():
        TEST.write_text(TEST_SOURCE, encoding='utf-8')
    changed = False
    try:
        require((TARGET.read_bytes() if TARGET.exists() else None) == original, 'Concurrent source change')
        atomic(TARGET, updated)
        changed = True
        clear_cache()
        require(subprocess.run([sys.executable, '-B', str(TEST)], cwd=str(ROOT)).returncode == 0,
                'Physical test failed')
    except BaseException:
        if changed and TARGET.exists() and TARGET.read_bytes() == updated:
            if original is None:
                TARGET.unlink()
            else:
                atomic(TARGET, original)
            clear_cache()
            print('[ROLLBACK] prior production boundary restored', flush=True)
        raise
    print('[PASS] OOI_017_EVIDENCE_BACKED_MATERIALIZER installed and tested; execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI_017_EVIDENCE_BACKED_MATERIALIZER: ' + str(exc), flush=True)
        print('[STOP] Do not run the next installer; return full output', flush=True)
        sys.exit(1)
