"""OOI-008C: certify default validation with identical inputs and a fixed test clock."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_007b_slop_existing_oos_intake.py'
TEST = ROOT / 'test_ooi_008c_slop_existing_oos_validation_replay_certification.py'
PREVIOUS_TEST = ROOT / 'test_ooi_007b_slop_existing_oos_intake.py'
EXPECTED_PREDECESSOR = '7139ea49a7cf49cc39eeebab2529987b88bf2b75f4400abcfc9d0c2351468cff'
MODULE_SOURCE = '"""SLOP entry points into the existing OOS. No execution authority."""\nfrom qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_006_slop_universal_opportunity_materializer import materialize_slop\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_operating_system import OpportunityOperatingSystem\n\nEXECUTION_AUTHORITY = False\nREAD_ONLY = True\nSOURCE = \'SLOP_BUY_PRESSURE\'\n\ndef _canonical(source):\n    opportunity = materialize_slop(source)\n    if opportunity.read_only is not True or opportunity.metadata.get(\'execution_authority\') is not False:\n        raise ValueError(\'Oracle read-only boundary violated\')\n    opportunity.fingerprint()\n    return opportunity\n\ndef intake_slop(source, oos):\n    """Register research in the caller-owned existing OOS; not trade approval."""\n    if not isinstance(oos, OpportunityOperatingSystem):\n        raise TypeError(\'An existing OpportunityOperatingSystem instance is required\')\n    opportunity = _canonical(source)\n    result = oos.intake(opportunity, source=SOURCE, metadata={\'execution_authority\': False, \'read_only\': True})\n    return opportunity, result\n\nfrom qseries_v2.oracle_intelligence.opportunity_operating_system.opportunity_validation_engine import OpportunityValidationEngine, ValidationRuleConfig\n\ndef _validate(opportunity):\n    # Preserve the existing production validation defaults, including UNKNOWN handling.\n    return OpportunityValidationEngine(config=ValidationRuleConfig()).validate(opportunity)\n\ndef validate_slop(source):\n    opportunity = _canonical(source)\n    report = _validate(opportunity)\n    return opportunity, report\n'
TEST_SOURCE = "import copy\nimport importlib\nimport math\nfrom types import SimpleNamespace\n\nb = importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_007b_slop_existing_oos_intake')\n\ndef require(value, message):\n    if not value:\n        raise AssertionError(message)\n\ndef fixture():\n    return SimpleNamespace(prediction_id='P1', token_address='T1', pair_address='PAIR1',\n        frozen_at='2026-09-17T00:00:00Z', conditions={'order_flow': 'BUY_PRESSURE'},\n        horizon_seconds=60, target=.10, stop=-.05, friction_bps=200)\n\ndef verify(opportunity, source):\n    require(opportunity.read_only is True, 'read_only changed')\n    require(opportunity.metadata['execution_authority'] is False, 'execution authority changed')\n    for name in ('conditions', 'horizon_seconds', 'target', 'stop', 'friction_bps', 'frozen_at'):\n        require(opportunity.metadata[name] == getattr(source, name), 'thesis changed: ' + name)\n    require(b.EXECUTION_AUTHORITY is False and b.READ_ONLY is True, 'bridge authority changed')\n\ndef semantic(report):\n    return (report.opportunity_id, report.fingerprint, report.status,\n        report.passed_checks, report.failed_checks, report.warning_count, report.info_count,\n        tuple((c.check_id, c.severity, c.passed, c.message, c.field, repr(c.value)) for c in report.checks))\n\nfrom contextlib import ExitStack, contextmanager\nimport datetime as datetime_module\nimport sys\nimport time as time_module\nfrom unittest.mock import patch\n\nREAL_DATETIME = datetime_module.datetime\nFIXED = REAL_DATETIME(2026, 9, 17, 0, 0, 0, tzinfo=datetime_module.timezone.utc)\n\nclass FixedDateTime(REAL_DATETIME):\n    @classmethod\n    def now(cls, tz=None):\n        if tz is None:\n            return FIXED.astimezone().replace(tzinfo=None)\n        return FIXED.astimezone(tz)\n\n    @classmethod\n    def utcnow(cls):\n        return FIXED.replace(tzinfo=None)\n\n    @classmethod\n    def today(cls):\n        return cls.now()\n\nclass ClockProxy:\n    def __init__(self, original, replacements):\n        self.original = original\n        self.replacements = replacements\n\n    def __getattr__(self, name):\n        if name in self.replacements:\n            return self.replacements[name]\n        return getattr(self.original, name)\n\n@contextmanager\ndef fixed_validation_clock():\n    # Only bindings in these loaded modules change, and only inside this test process.\n    prefixes = (\n        'qseries_v2.oracle_intelligence.opportunity_operating_system',\n        'qseries_v2.oracle_intelligence.universal_opportunity_model',\n        'qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence',\n    )\n    replacements = 0\n    with ExitStack() as stack:\n        for name, module in list(sys.modules.items()):\n            if module is None or not any(name == p or name.startswith(p + '.') for p in prefixes):\n                continue\n            for key, value in list(vars(module).items()):\n                replacement = None\n                if value is REAL_DATETIME:\n                    replacement = FixedDateTime\n                elif value is datetime_module:\n                    replacement = ClockProxy(datetime_module, {'datetime': FixedDateTime})\n                elif value is time_module:\n                    replacement = ClockProxy(time_module, {'time': lambda: FIXED.timestamp()})\n                elif value is time_module.time:\n                    replacement = lambda: FIXED.timestamp()\n                if replacement is not None:\n                    stack.enter_context(patch.object(module, key, replacement))\n                    replacements += 1\n        require(replacements > 0, 'No test clock binding found; refusing uncontrolled replay')\n        yield replacements\n\ndef main():\n    source = fixture()\n    source_before = copy.deepcopy(vars(source))\n    with fixed_validation_clock() as bindings:\n        opportunity, report = b.validate_slop(source)\n        verify(opportunity, source)\n        snapshot = copy.deepcopy(opportunity)\n        snapshot_before = copy.deepcopy(snapshot.to_dict())\n        original_before = copy.deepcopy(opportunity.to_dict())\n        replay = b._validate(snapshot)\n        require(snapshot.to_dict() == snapshot_before, 'validation mutated replay input')\n        require(opportunity.to_dict() == original_before, 'validation mutated original input')\n        require(report.fingerprint == opportunity.fingerprint(), 'validation fingerprint mismatch')\n        require(report.opportunity_id == opportunity.opportunity_id, 'validation identity mismatch')\n        require(report.read_only is True and replay.read_only is True, 'validation is not read-only')\n        require(type(report.is_accepted()) is bool, 'non-boolean validation decision')\n        require(len(report.checks) > 0, 'validation performed no checks')\n        left, right = semantic(report), semantic(replay)\n        if left != right:\n            labels = ('opportunity_id', 'fingerprint', 'status', 'passed_checks', 'failed_checks',\n                      'warning_count', 'info_count', 'checks')\n            for label, first, second in zip(labels, left, right):\n                if first != second:\n                    print('[REPLAY_DIFFERENCE]', label, flush=True)\n                    print('[FIRST]', repr(first), flush=True)\n                    print('[SECOND]', repr(second), flush=True)\n        require(left == right, 'identical-input fixed-clock validation replay differs')\n        require(report.is_accepted() == replay.is_accepted(), 'acceptance decision differs')\n    require(vars(source) == source_before, 'validation mutated SLOP source')\n    print('[FIXED_CLOCK]', FIXED.isoformat(), 'bindings=', bindings)\n    print('[VALIDATION_STATUS]', getattr(report.status, 'value', report.status))\n    print('[ACCEPTED]', report.is_accepted())\n    for check in report.checks:\n        if not check.passed:\n            print('[CHECK]', check.check_id, getattr(check.severity, 'value', check.severity), check.message)\n    print('[PASS] OOI-008C identical-input, fixed-clock validation replay')\n    print('[PASS] existing validation decision preserved; no threshold bypass')\n    print('[PASS] frozen BUY_PRESSURE / 60 seconds / +10% / -5% / 200 bps')\n    print('[PASS] read_only=True execution_authority=FALSE')\n\nif __name__ == '__main__':\n    main()\n"

def require(value, message):
    if not value:
        raise RuntimeError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def write_atomic(path, data):
    tmp = path.with_name(path.name + '.ooi008c.tmp')
    require(not tmp.exists(), 'Temporary file already exists: ' + str(tmp))
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()

def clear_cache():
    cache = TARGET.parent / '__pycache__'
    if cache.is_dir():
        for item in cache.glob(TARGET.stem + '.*.pyc'):
            item.unlink()

def main():
    require(TARGET.is_file(), 'Existing OOI bridge missing')
    require(PREVIOUS_TEST.is_file(), 'OOI-007B test missing')
    updated = MODULE_SOURCE.encode('utf-8')
    original = TARGET.read_bytes()
    require(digest(original) in (EXPECTED_PREDECESSOR, digest(updated)),
            'Bridge differs from known OOI-007B/008 source; refusing speculative overwrite')
    if TEST.exists():
        require(TEST.read_text(encoding='utf-8') == TEST_SOURCE,
                'OOI-008C test differs from this installer; refusing overwrite')
    print('[GATE] Rechecking OOI-007B intake', flush=True)
    require(subprocess.run([sys.executable, '-B', str(PREVIOUS_TEST)], cwd=str(ROOT)).returncode == 0,
            'OOI-007B failed; nothing installed')
    compile(MODULE_SOURCE, str(TARGET), 'exec')
    compile(TEST_SOURCE, str(TEST), 'exec')
    backup = TARGET.with_name(TARGET.name + '.pre_ooi008c_' + digest(original)[:12] + '.bak')
    require(not backup.exists() or backup.read_bytes() == original, 'Backup conflict')
    if not backup.exists():
        backup.write_bytes(original)
    if not TEST.exists():
        TEST.write_text(TEST_SOURCE, encoding='utf-8')
    changed = False
    try:
        require(TARGET.read_bytes() == original, 'Bridge changed during preflight')
        write_atomic(TARGET, updated)
        changed = True
        clear_cache()
        print('[GATE] Running installed default OOS validation; complete traceback follows on failure', flush=True)
        require(subprocess.run([sys.executable, '-B', str(TEST)], cwd=str(ROOT)).returncode == 0,
                'OOI-008C physical validation test failed')
    except BaseException:
        if changed and TARGET.read_bytes() == updated:
            write_atomic(TARGET, original)
            clear_cache()
            print('[ROLLBACK] prior bridge restored; OOI-008C test retained', flush=True)
        raise
    print('[PASS] OOI-008C validation installed and physically tested', flush=True)
    print('[NEXT] Await OOI-009B; old OOI-009/010 tests use the retired replay comparison', flush=True)
    print('[PASS] frozen thesis unchanged; execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI-008C: ' + str(exc), flush=True)
        print('[STOP] Do not run OOI-009 or OOI-010; return the full output above', flush=True)
        sys.exit(1)
