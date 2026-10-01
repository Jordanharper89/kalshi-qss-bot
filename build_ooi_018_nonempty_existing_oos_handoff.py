"""ooi_018_nonempty_existing_oos_handoff: grounded in the supplied physical source contracts."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_007b_slop_existing_oos_intake.py'
TEST = ROOT / 'test_ooi_018_nonempty_existing_oos_handoff.py'
PREVIOUS = ROOT / 'test_ooi_017_evidence_backed_materializer.py'
EXPECTED = '88aef805509ffaf7337310e0137b33c5fb2230839ae11e18886c400e604e4006'
PINS = {}
MODULE_SOURCE = '"""SLOP entry points into the existing OOS. No execution authority."""\nfrom qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_006_slop_universal_opportunity_materializer import materialize_slop\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_operating_system import OpportunityOperatingSystem\n\nEXECUTION_AUTHORITY = False\nREAD_ONLY = True\nSOURCE = \'SLOP_BUY_PRESSURE\'\n\ndef _canonical(source):\n    opportunity = materialize_slop(source)\n    if opportunity.read_only is not True or opportunity.metadata.get(\'execution_authority\') is not False:\n        raise ValueError(\'Oracle read-only boundary violated\')\n    opportunity.fingerprint()\n    return opportunity\n\ndef intake_slop(source, oos):\n    """Register research in the caller-owned existing OOS; not trade approval."""\n    if not isinstance(oos, OpportunityOperatingSystem):\n        raise TypeError(\'An existing OpportunityOperatingSystem instance is required\')\n    opportunity = _canonical(source)\n    result = oos.intake(opportunity, source=SOURCE, metadata={\'execution_authority\': False, \'read_only\': True})\n    return opportunity, result\n\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_validation_engine import OpportunityValidationEngine, ValidationRuleConfig\n\ndef _validate(opportunity):\n    # Preserve the existing production validation defaults, including UNKNOWN handling.\n    return OpportunityValidationEngine(config=ValidationRuleConfig()).validate(opportunity)\n\ndef validate_slop(source):\n    opportunity = _canonical(source)\n    report = _validate(opportunity)\n    return opportunity, report\n\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_ranking_engine import OpportunityRankingEngine\n\ndef _partition(sources):\n    accepted, reports = [], []\n    for source in sources:\n        opportunity, report = validate_slop(source)\n        reports.append(report)\n        if report.is_accepted():\n            accepted.append(opportunity)\n    return accepted, reports\n\ndef rank_validated_slop(sources):\n    accepted, reports = _partition(sources)\n    result = OpportunityRankingEngine().rank(accepted)\n    return result, reports\n\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_pipeline import OpportunityPipeline\n\ndef process_validated_slop(sources, oos):\n    """Only accepted research reaches the caller-owned registry and ranking pipeline."""\n    if not isinstance(oos, OpportunityOperatingSystem):\n        raise TypeError(\'An existing OpportunityOperatingSystem instance is required\')\n    accepted, reports = _partition(sources)\n    pipeline = OpportunityPipeline(oos=oos, ranking_engine=OpportunityRankingEngine())\n    result = pipeline.process(accepted, source=SOURCE)\n    return result, reports\n\ndef process_evidence_backed_slop(sources, evidence_snapshot, oos, policy=None, evaluated_at=None):\n    """Research-only evidence handoff into the existing registry/validator/ranker."""\n    if not isinstance(oos, OpportunityOperatingSystem):\n        raise TypeError(\'Existing OpportunityOperatingSystem instance required\')\n    accepted, reports, held = [], [], []\n    for source in sources:\n        opportunity = materialize_slop(source, evidence_snapshot=evidence_snapshot,\n                                       policy=policy, evaluated_at=evaluated_at)\n        if opportunity.read_only is not True or opportunity.metadata[\'execution_authority\'] is not False:\n            raise ValueError(\'Oracle authority boundary violated\')\n        report = _validate(opportunity)\n        reports.append(report)\n        if opportunity.metadata.get(\'evidence_admission_eligible\') is True and report.is_accepted():\n            accepted.append(opportunity)\n        else:\n            held.append({\'opportunity_id\': opportunity.opportunity_id,\n                         \'reasons\': opportunity.metadata.get(\'evidence_hold_reasons\', []),\n                         \'validation_accepted\': report.is_accepted()})\n    pipeline = OpportunityPipeline(oos=oos, ranking_engine=OpportunityRankingEngine())\n    result = pipeline.process(accepted, source=SOURCE)\n    return {\'pipeline\': result, \'validation_reports\': reports, \'held\': held,\n            \'accepted_count\': len(accepted), \'read_only\': True, \'execution_authority\': False}\n'
TEST_SOURCE = "import importlib\nimport tempfile\nfrom test_ooi_015_verified_slop_evidence_snapshot import fixture,snapshot,candidate,require\nfrom test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock\nB=importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_007b_slop_existing_oos_intake')\nG=importlib.import_module('qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_subsystem_integration_gate')\n\ndef main():\n    with tempfile.TemporaryDirectory() as root, fixed_validation_clock():\n        fixture(root);snap=snapshot(root);op=candidate()\n        oos=B.OpportunityOperatingSystem()\n        result=B.process_evidence_backed_slop([op],snap,oos,evaluated_at=op.frozen_at)\n        pipe=result['pipeline']\n        require(result['accepted_count']==1 and len(oos.all_records())==1,'nonempty registry handoff failed')\n        require(pipe.input_count==pipe.registered_count==pipe.ranked_count==1,'nonempty pipeline counts failed')\n        require(all(r.is_accepted() for r in result['validation_reports']),'default validator rejected positive fixture')\n        replay=B.process_evidence_backed_slop([op],snap,oos,evaluated_at=op.frozen_at)\n        require(replay['pipeline'].duplicate_count==1 and len(oos.all_records())==1,'nonempty duplicate handling failed')\n        opportunity=oos.all_records()[0].opportunity\n        gate=G.run_opportunity_subsystem_integration_gate(opportunities=[opportunity],observed_at=op.frozen_at,source=B.SOURCE)\n        require(gate.passed is True and gate.fail_count==0 and gate.verify_integration_hash(),'nonempty existing integration gate failed')\n        require(gate.read_only is True and gate.execution_allowed is False,'integration authority failure')\n        G.assert_opportunity_subsystem_read_only(gate)\n        held_oos=B.OpportunityOperatingSystem()\n        held=B.process_evidence_backed_slop([op],snap,held_oos,evaluated_at='2026-09-17T00:01:10+00:00')\n        require(held['accepted_count']==0 and len(held_oos.all_records())==0,'expired candidate registered')\n        fixture(root,count=2)\n        insufficient=B.process_evidence_backed_slop([op],snapshot(root),held_oos,evaluated_at=op.frozen_at)\n        require(insufficient['accepted_count']==0 and len(held_oos.all_records())==0,'insufficient cohort registered')\n    print('[PASS] OOI-018 NONEMPTY fixture: accepted=1 registered=1 ranked=1; replay duplicate=1')\n    print('[PASS] Actual OOS validation/ranking/integration gate; expiry and evidence HOLD exclusions')\n    print('[SCOPE] Deterministic fixture certification, NOT live admission or runtime activation')\n    print('[PASS] Oracle read_only=True execution_authority=FALSE; Q Series sole execution authority')\n\nif __name__=='__main__':main()\n"

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
    temp = path.with_name(path.name + '.ooi_018_nonempty_existing_oos_handoff.tmp')
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
        backup = TARGET.with_name(TARGET.name + '.pre_ooi_018_nonempty_existing_oos_handoff_' + sha(original)[:12] + '.bak')
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
    print('[PASS] OOI_018_NONEMPTY_EXISTING_OOS_HANDOFF installed and tested; execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI_018_NONEMPTY_EXISTING_OOS_HANDOFF: ' + str(exc), flush=True)
        print('[STOP] Do not run the next installer; return full output', flush=True)
        sys.exit(1)
