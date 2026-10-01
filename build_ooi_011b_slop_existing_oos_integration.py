"""OOI_011B_SLOP_EXISTING_OOS_INTEGRATION: reuse the certified existing Oracle OOS."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_007b_slop_existing_oos_intake.py'
TEST = ROOT / 'test_ooi_011b_slop_existing_oos_integration.py'
PREVIOUS_TEST = ROOT / 'test_ooi_010b_slop_existing_oos_pipeline.py'
EXPECTED_SHA256 = '88aef805509ffaf7337310e0137b33c5fb2230839ae11e18886c400e604e4006'
MODULE_SOURCE = '"""SLOP entry points into the existing OOS. No execution authority."""\nfrom qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_006_slop_universal_opportunity_materializer import materialize_slop\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_operating_system import OpportunityOperatingSystem\n\nEXECUTION_AUTHORITY = False\nREAD_ONLY = True\nSOURCE = \'SLOP_BUY_PRESSURE\'\n\ndef _canonical(source):\n    opportunity = materialize_slop(source)\n    if opportunity.read_only is not True or opportunity.metadata.get(\'execution_authority\') is not False:\n        raise ValueError(\'Oracle read-only boundary violated\')\n    opportunity.fingerprint()\n    return opportunity\n\ndef intake_slop(source, oos):\n    """Register research in the caller-owned existing OOS; not trade approval."""\n    if not isinstance(oos, OpportunityOperatingSystem):\n        raise TypeError(\'An existing OpportunityOperatingSystem instance is required\')\n    opportunity = _canonical(source)\n    result = oos.intake(opportunity, source=SOURCE, metadata={\'execution_authority\': False, \'read_only\': True})\n    return opportunity, result\n\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_validation_engine import OpportunityValidationEngine, ValidationRuleConfig\n\ndef _validate(opportunity):\n    # Preserve the existing production validation defaults, including UNKNOWN handling.\n    return OpportunityValidationEngine(config=ValidationRuleConfig()).validate(opportunity)\n\ndef validate_slop(source):\n    opportunity = _canonical(source)\n    report = _validate(opportunity)\n    return opportunity, report\n\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_ranking_engine import OpportunityRankingEngine\n\ndef _partition(sources):\n    accepted, reports = [], []\n    for source in sources:\n        opportunity, report = validate_slop(source)\n        reports.append(report)\n        if report.is_accepted():\n            accepted.append(opportunity)\n    return accepted, reports\n\ndef rank_validated_slop(sources):\n    accepted, reports = _partition(sources)\n    result = OpportunityRankingEngine().rank(accepted)\n    return result, reports\n\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_pipeline import OpportunityPipeline\n\ndef process_validated_slop(sources, oos):\n    """Only accepted research reaches the caller-owned registry and ranking pipeline."""\n    if not isinstance(oos, OpportunityOperatingSystem):\n        raise TypeError(\'An existing OpportunityOperatingSystem instance is required\')\n    accepted, reports = _partition(sources)\n    pipeline = OpportunityPipeline(oos=oos, ranking_engine=OpportunityRankingEngine())\n    result = pipeline.process(accepted, source=SOURCE)\n    return result, reports\n'
TEST_SOURCE = "import copy\nimport importlib\nimport math\nfrom types import SimpleNamespace\n\nb = importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_007b_slop_existing_oos_intake')\n\ndef require(value, message):\n    if not value:\n        raise AssertionError(message)\n\ndef fixture():\n    return SimpleNamespace(prediction_id='P1', token_address='T1', pair_address='PAIR1',\n        frozen_at='2026-09-17T00:00:00Z', conditions={'order_flow': 'BUY_PRESSURE'},\n        horizon_seconds=60, target=.10, stop=-.05, friction_bps=200)\n\ndef verify(opportunity, source):\n    require(opportunity.read_only is True, 'read_only changed')\n    require(opportunity.metadata['execution_authority'] is False, 'execution authority changed')\n    for name in ('conditions', 'horizon_seconds', 'target', 'stop', 'friction_bps', 'frozen_at'):\n        require(opportunity.metadata[name] == getattr(source, name), 'thesis changed: ' + name)\n    require(b.EXECUTION_AUTHORITY is False and b.READ_ONLY is True, 'bridge authority changed')\n\ndef semantic(report):\n    return (report.opportunity_id, report.fingerprint, report.status,\n        report.passed_checks, report.failed_checks, report.warning_count, report.info_count,\n        tuple((c.check_id, c.severity, c.passed, c.message, c.field, repr(c.value)) for c in report.checks))\n\ndef run_checks():\n    gate = importlib.import_module('qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_subsystem_integration_gate')\n    source = fixture()\n    before = copy.deepcopy(vars(source))\n    opportunity, validation = b.validate_slop(source)\n    # Gate the same accepted set used by the production bridge. Never relax validation.\n    accepted = [opportunity] if validation.is_accepted() else []\n    result = gate.run_opportunity_subsystem_integration_gate(\n        opportunities=accepted, observed_at='2026-09-17T00:00:00Z', source=b.SOURCE)\n    print('[INTEGRATION_PASSED]', result.passed)\n    print('[ACCEPTED_COUNT]', len(accepted))\n    for check in result.checks:\n        print('[INTEGRATION_CHECK]', check)\n    require(result.read_only is True and result.execution_allowed is False, 'integration authority boundary failed')\n    require(result.verify_integration_hash(), 'integration hash verification failed')\n    require(result.passed is True and result.fail_count == 0, 'existing integration gate failed; stop here')\n    require(result.pass_count > 0, 'integration ran no passing checks')\n    gate.assert_opportunity_subsystem_read_only(result)\n    replay = gate.run_opportunity_subsystem_integration_gate(\n        opportunities=accepted, observed_at='2026-09-17T00:00:00Z', source=b.SOURCE)\n    require(replay.passed is True and replay.verify_integration_hash(), 'integration replay failed')\n    require((result.pass_count, result.fail_count) == (replay.pass_count, replay.fail_count), 'integration check totals differ')\n    verify(opportunity, source)\n    require(vars(source) == before, 'integration mutated source')\n    if not accepted:\n        print('[HOLD] SLOP fixture is not accepted by existing validation; no admitted opportunity certified')\n    print('[PASS] OOI-011B existing OOS integration contract; execution_authority=FALSE')\n    print('[SCOPE] deterministic fixture certification; live runtime activation not claimed')\n\ndef main():\n    from test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock\n    with fixed_validation_clock():\n        run_checks()\n\nif __name__ == '__main__':\n    main()\n"
MUTATE = False

def require(value, message):
    if not value:
        raise RuntimeError(message)

def atomic_write(path, content):
    temp = path.with_name(path.name + '.ooi_011b_slop_existing_oos_integration.tmp')
    require(not temp.exists(), 'Existing temporary file: ' + str(temp))
    try:
        temp.write_bytes(content)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()

def clear_cache():
    cache = TARGET.parent / '__pycache__'
    if cache.is_dir():
        for item in cache.glob(TARGET.stem + '.*.pyc'):
            item.unlink()

def main():
    require(PREVIOUS_TEST.is_file(), 'Missing preceding certified test: ' + PREVIOUS_TEST.name)
    require(TARGET.parent.is_dir(), 'Existing OOI subsystem directory missing')
    require(not TEST.exists(), 'This test already exists; run it directly instead of reinstalling')
    require(subprocess.run([sys.executable, '-B', str(PREVIOUS_TEST)], cwd=str(ROOT)).returncode == 0,
            'Preceding physical boundary failed; no files changed')
    original = TARGET.read_bytes() if TARGET.exists() else None
    if EXPECTED_SHA256 is None:
        require(original is None, 'OOI-007B target already exists; refusing overwrite')
    else:
        require(original is not None and hashlib.sha256(original).hexdigest() == EXPECTED_SHA256,
                'Installed OOI bridge differs from certified predecessor; no speculative overwrite')
    compile(MODULE_SOURCE, str(TARGET), 'exec')
    compile(TEST_SOURCE, str(TEST), 'exec')
    updated = MODULE_SOURCE.encode('utf-8')
    if original is not None and MUTATE:
        backup = TARGET.with_name(TARGET.name + '.pre_ooi_011b_slop_existing_oos_integration.bak')
        require(not backup.exists() or backup.read_bytes() == original, 'Backup conflict')
        if not backup.exists():
            backup.write_bytes(original)
    TEST.write_text(TEST_SOURCE, encoding='utf-8')
    try:
        if MUTATE:
            require((TARGET.read_bytes() if TARGET.exists() else None) == original, 'Concurrent file change')
            atomic_write(TARGET, updated)
            clear_cache()
        require(subprocess.run([sys.executable, '-B', str(TEST)], cwd=str(ROOT)).returncode == 0,
                'Physical test failed')
    except BaseException:
        if MUTATE and TARGET.exists() and TARGET.read_bytes() == updated:
            if original is None:
                TARGET.unlink()
            else:
                atomic_write(TARGET, original)
            clear_cache()
            print('[ROLLBACK] preceding bridge restored; generated test retained for diagnosis', flush=True)
        raise
    print('[PASS] OOI_011B_SLOP_EXISTING_OOS_INTEGRATION installed and physically tested', flush=True)
    print('[PASS] Oracle execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI_011B_SLOP_EXISTING_OOS_INTEGRATION: ' + str(exc), flush=True)
        print('[STOP] Do not run the next installer', flush=True)
        sys.exit(1)
