"""OOI_009_SLOP_EXISTING_OOS_RANKING: reuse the certified existing Oracle OOS."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_007b_slop_existing_oos_intake.py'
TEST = ROOT / 'test_ooi_009_slop_existing_oos_ranking.py'
PREVIOUS_TEST = ROOT / 'test_ooi_008_slop_existing_oos_validation.py'
EXPECTED_SHA256 = '10f4417da71543c2dd93142c3b7d289f6c60ed54745d369f486b88064c5956cf'
MODULE_SOURCE = '"""SLOP entry points into the existing OOS. No execution authority."""\nfrom qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_006_slop_universal_opportunity_materializer import materialize_slop\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_operating_system import OpportunityOperatingSystem\n\nEXECUTION_AUTHORITY = False\nREAD_ONLY = True\nSOURCE = \'SLOP_BUY_PRESSURE\'\n\ndef _canonical(source):\n    opportunity = materialize_slop(source)\n    if opportunity.read_only is not True or opportunity.metadata.get(\'execution_authority\') is not False:\n        raise ValueError(\'Oracle read-only boundary violated\')\n    opportunity.fingerprint()\n    return opportunity\n\ndef intake_slop(source, oos):\n    """Register research in the caller-owned existing OOS; not trade approval."""\n    if not isinstance(oos, OpportunityOperatingSystem):\n        raise TypeError(\'An existing OpportunityOperatingSystem instance is required\')\n    opportunity = _canonical(source)\n    result = oos.intake(opportunity, source=SOURCE, metadata={\'execution_authority\': False, \'read_only\': True})\n    return opportunity, result\n\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_validation_engine import OpportunityValidationEngine, ValidationRuleConfig\n\ndef _validate(opportunity):\n    # Preserve the existing production validation defaults, including UNKNOWN handling.\n    return OpportunityValidationEngine(config=ValidationRuleConfig()).validate(opportunity)\n\ndef validate_slop(source):\n    opportunity = _canonical(source)\n    report = _validate(opportunity)\n    return opportunity, report\n\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_ranking_engine import OpportunityRankingEngine\n\ndef _partition(sources):\n    accepted, reports = [], []\n    for source in sources:\n        opportunity, report = validate_slop(source)\n        reports.append(report)\n        if report.is_accepted():\n            accepted.append(opportunity)\n    return accepted, reports\n\ndef rank_validated_slop(sources):\n    accepted, reports = _partition(sources)\n    result = OpportunityRankingEngine().rank(accepted)\n    return result, reports\n'
TEST_SOURCE = "import copy\nimport importlib\nimport math\nfrom types import SimpleNamespace\n\nb = importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_007b_slop_existing_oos_intake')\n\ndef require(value, message):\n    if not value:\n        raise AssertionError(message)\n\ndef fixture():\n    return SimpleNamespace(prediction_id='P1', token_address='T1', pair_address='PAIR1',\n        frozen_at='2026-09-17T00:00:00Z', conditions={'order_flow': 'BUY_PRESSURE'},\n        horizon_seconds=60, target=.10, stop=-.05, friction_bps=200)\n\ndef verify(opportunity, source):\n    require(opportunity.read_only is True, 'read_only changed')\n    require(opportunity.metadata['execution_authority'] is False, 'execution authority changed')\n    for name in ('conditions', 'horizon_seconds', 'target', 'stop', 'friction_bps', 'frozen_at'):\n        require(opportunity.metadata[name] == getattr(source, name), 'thesis changed: ' + name)\n    require(b.EXECUTION_AUTHORITY is False and b.READ_ONLY is True, 'bridge authority changed')\n\ndef semantic(report):\n    return (report.opportunity_id, report.fingerprint, report.status,\n        report.passed_checks, report.failed_checks, report.warning_count, report.info_count,\n        tuple((c.check_id, c.severity, c.passed, c.message, c.field, repr(c.value)) for c in report.checks))\n\ndef main():\n    source = fixture()\n    before = copy.deepcopy(vars(source))\n    result, reports = b.rank_validated_slop([source])\n    replay, repeat_reports = b.rank_validated_slop([copy.deepcopy(source)])\n    require(len(reports) == 1, 'validation report missing')\n    expected = 1 if reports[0].is_accepted() else 0\n    require(result.ranked_count == expected == len(result.opportunities), 'rejected research entered ranked feed')\n    require(result.read_only is True, 'ranking is not read-only')\n    require([r.fingerprint for r in result.opportunities] == [r.fingerprint for r in replay.opportunities], 'ranking identity/order differs')\n    require([semantic(r) for r in reports] == [semantic(r) for r in repeat_reports], 'validation replay differs')\n    for ranked in result.opportunities:\n        require(math.isfinite(float(ranked.score)), 'nonfinite score')\n        verify(ranked.opportunity, source)\n    # Direct engine compatibility probe is test-only and never enters the accepted feed.\n    opportunity = b._canonical(source)\n    raw = b.OpportunityRankingEngine().rank([opportunity])\n    require(raw.ranked_count == 1 and len(raw.opportunities) == 1, 'existing ranker cannot score canonical SLOP')\n    require(raw.opportunities[0].fingerprint == opportunity.fingerprint(), 'ranker fingerprint mismatch')\n    require(math.isfinite(float(raw.opportunities[0].score)), 'nonfinite direct score')\n    empty, empty_reports = b.rank_validated_slop([])\n    require(empty.ranked_count == 0 and empty_reports == [], 'empty ranking contract failed')\n    require(vars(source) == before, 'ranking mutated source')\n    print('[ACCEPTED_FEED_COUNT]', result.ranked_count)\n    print('[PASS] OOI-009 existing ranker compatibility and validation-filtered feed')\n    print('[PASS] ranking is research only; execution_authority=FALSE')\n\nif __name__ == '__main__':\n    main()\n"
MUTATE = True

def require(value, message):
    if not value:
        raise RuntimeError(message)

def atomic_write(path, content):
    temp = path.with_name(path.name + '.ooi_009_slop_existing_oos_ranking.tmp')
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
        backup = TARGET.with_name(TARGET.name + '.pre_ooi_009_slop_existing_oos_ranking.bak')
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
    print('[PASS] OOI_009_SLOP_EXISTING_OOS_RANKING installed and physically tested', flush=True)
    print('[PASS] Oracle execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI_009_SLOP_EXISTING_OOS_RANKING: ' + str(exc), flush=True)
        print('[STOP] Do not run the next installer', flush=True)
        sys.exit(1)
