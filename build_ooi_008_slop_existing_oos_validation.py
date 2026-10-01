"""OOI_008_SLOP_EXISTING_OOS_VALIDATION: reuse the certified existing Oracle OOS."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_007b_slop_existing_oos_intake.py'
TEST = ROOT / 'test_ooi_008_slop_existing_oos_validation.py'
PREVIOUS_TEST = ROOT / 'test_ooi_007b_slop_existing_oos_intake.py'
EXPECTED_SHA256 = '7139ea49a7cf49cc39eeebab2529987b88bf2b75f4400abcfc9d0c2351468cff'
MODULE_SOURCE = '"""SLOP entry points into the existing OOS. No execution authority."""\nfrom qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_006_slop_universal_opportunity_materializer import materialize_slop\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_operating_system import OpportunityOperatingSystem\n\nEXECUTION_AUTHORITY = False\nREAD_ONLY = True\nSOURCE = \'SLOP_BUY_PRESSURE\'\n\ndef _canonical(source):\n    opportunity = materialize_slop(source)\n    if opportunity.read_only is not True or opportunity.metadata.get(\'execution_authority\') is not False:\n        raise ValueError(\'Oracle read-only boundary violated\')\n    opportunity.fingerprint()\n    return opportunity\n\ndef intake_slop(source, oos):\n    """Register research in the caller-owned existing OOS; not trade approval."""\n    if not isinstance(oos, OpportunityOperatingSystem):\n        raise TypeError(\'An existing OpportunityOperatingSystem instance is required\')\n    opportunity = _canonical(source)\n    result = oos.intake(opportunity, source=SOURCE, metadata={\'execution_authority\': False, \'read_only\': True})\n    return opportunity, result\n\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_validation_engine import OpportunityValidationEngine, ValidationRuleConfig\n\ndef _validate(opportunity):\n    # Preserve the existing production validation defaults, including UNKNOWN handling.\n    return OpportunityValidationEngine(config=ValidationRuleConfig()).validate(opportunity)\n\ndef validate_slop(source):\n    opportunity = _canonical(source)\n    report = _validate(opportunity)\n    return opportunity, report\n'
TEST_SOURCE = "import copy\nimport importlib\nimport math\nfrom types import SimpleNamespace\n\nb = importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_007b_slop_existing_oos_intake')\n\ndef require(value, message):\n    if not value:\n        raise AssertionError(message)\n\ndef fixture():\n    return SimpleNamespace(prediction_id='P1', token_address='T1', pair_address='PAIR1',\n        frozen_at='2026-09-17T00:00:00Z', conditions={'order_flow': 'BUY_PRESSURE'},\n        horizon_seconds=60, target=.10, stop=-.05, friction_bps=200)\n\ndef verify(opportunity, source):\n    require(opportunity.read_only is True, 'read_only changed')\n    require(opportunity.metadata['execution_authority'] is False, 'execution authority changed')\n    for name in ('conditions', 'horizon_seconds', 'target', 'stop', 'friction_bps', 'frozen_at'):\n        require(opportunity.metadata[name] == getattr(source, name), 'thesis changed: ' + name)\n    require(b.EXECUTION_AUTHORITY is False and b.READ_ONLY is True, 'bridge authority changed')\n\ndef semantic(report):\n    return (report.opportunity_id, report.fingerprint, report.status,\n        report.passed_checks, report.failed_checks, report.warning_count, report.info_count,\n        tuple((c.check_id, c.severity, c.passed, c.message, c.field, repr(c.value)) for c in report.checks))\n\ndef main():\n    source = fixture()\n    before = copy.deepcopy(vars(source))\n    opportunity, report = b.validate_slop(source)\n    verify(opportunity, source)\n    _, replay = b.validate_slop(copy.deepcopy(source))\n    require(report.fingerprint == opportunity.fingerprint(), 'validation fingerprint mismatch')\n    require(report.opportunity_id == opportunity.opportunity_id, 'validation identity mismatch')\n    require(report.read_only is True, 'validation is not read-only')\n    require(type(report.is_accepted()) is bool, 'non-boolean validation decision')\n    require(len(report.checks) > 0, 'validation performed no checks')\n    require(semantic(report) == semantic(replay), 'validation decisions are not repeatable')\n    require(vars(source) == before, 'validation mutated source')\n    print('[VALIDATION_STATUS]', getattr(report.status, 'value', report.status))\n    print('[ACCEPTED]', report.is_accepted())\n    for check in report.checks:\n        if not check.passed:\n            print('[CHECK]', check.check_id, getattr(check.severity, 'value', check.severity), check.message)\n    print('[PASS] OOI-008 existing default validation executed; decision preserved')\n    print('[PASS] contract certification only; no admission threshold bypass; execution_authority=FALSE')\n\nif __name__ == '__main__':\n    main()\n"
MUTATE = True

def require(value, message):
    if not value:
        raise RuntimeError(message)

def atomic_write(path, content):
    temp = path.with_name(path.name + '.ooi_008_slop_existing_oos_validation.tmp')
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
        backup = TARGET.with_name(TARGET.name + '.pre_ooi_008_slop_existing_oos_validation.bak')
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
    print('[PASS] OOI_008_SLOP_EXISTING_OOS_VALIDATION installed and physically tested', flush=True)
    print('[PASS] Oracle execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI_008_SLOP_EXISTING_OOS_VALIDATION: ' + str(exc), flush=True)
        print('[STOP] Do not run the next installer', flush=True)
        sys.exit(1)
