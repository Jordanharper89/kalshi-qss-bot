import copy
import importlib
import math
from types import SimpleNamespace

b = importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_007b_slop_existing_oos_intake')

def require(value, message):
    if not value:
        raise AssertionError(message)

def fixture():
    return SimpleNamespace(prediction_id='P1', token_address='T1', pair_address='PAIR1',
        frozen_at='2026-09-17T00:00:00Z', conditions={'order_flow': 'BUY_PRESSURE'},
        horizon_seconds=60, target=.10, stop=-.05, friction_bps=200)

def verify(opportunity, source):
    require(opportunity.read_only is True, 'read_only changed')
    require(opportunity.metadata['execution_authority'] is False, 'execution authority changed')
    for name in ('conditions', 'horizon_seconds', 'target', 'stop', 'friction_bps', 'frozen_at'):
        require(opportunity.metadata[name] == getattr(source, name), 'thesis changed: ' + name)
    require(b.EXECUTION_AUTHORITY is False and b.READ_ONLY is True, 'bridge authority changed')

def semantic(report):
    return (report.opportunity_id, report.fingerprint, report.status,
        report.passed_checks, report.failed_checks, report.warning_count, report.info_count,
        tuple((c.check_id, c.severity, c.passed, c.message, c.field, repr(c.value)) for c in report.checks))

from contextlib import ExitStack, contextmanager
import datetime as datetime_module
import sys
import time as time_module
from unittest.mock import patch

REAL_DATETIME = datetime_module.datetime
FIXED = REAL_DATETIME(2026, 9, 17, 0, 0, 0, tzinfo=datetime_module.timezone.utc)

class FixedDateTime(REAL_DATETIME):
    @classmethod
    def now(cls, tz=None):
        if tz is None:
            return FIXED.astimezone().replace(tzinfo=None)
        return FIXED.astimezone(tz)

    @classmethod
    def utcnow(cls):
        return FIXED.replace(tzinfo=None)

    @classmethod
    def today(cls):
        return cls.now()

class ClockProxy:
    def __init__(self, original, replacements):
        self.original = original
        self.replacements = replacements

    def __getattr__(self, name):
        if name in self.replacements:
            return self.replacements[name]
        return getattr(self.original, name)

@contextmanager
def fixed_validation_clock():
    # Only bindings in these loaded modules change, and only inside this test process.
    prefixes = (
        'qseries_v2.oracle_intelligence.opportunity_operating_system',
        'qseries_v2.oracle_intelligence.universal_opportunity_model',
        'qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence',
    )
    replacements = 0
    with ExitStack() as stack:
        for name, module in list(sys.modules.items()):
            if module is None or not any(name == p or name.startswith(p + '.') for p in prefixes):
                continue
            for key, value in list(vars(module).items()):
                replacement = None
                if value is REAL_DATETIME:
                    replacement = FixedDateTime
                elif value is datetime_module:
                    replacement = ClockProxy(datetime_module, {'datetime': FixedDateTime})
                elif value is time_module:
                    replacement = ClockProxy(time_module, {'time': lambda: FIXED.timestamp()})
                elif value is time_module.time:
                    replacement = lambda: FIXED.timestamp()
                if replacement is not None:
                    stack.enter_context(patch.object(module, key, replacement))
                    replacements += 1
        require(replacements > 0, 'No test clock binding found; refusing uncontrolled replay')
        yield replacements

def main():
    source = fixture()
    source_before = copy.deepcopy(vars(source))
    with fixed_validation_clock() as bindings:
        opportunity, report = b.validate_slop(source)
        verify(opportunity, source)
        snapshot = copy.deepcopy(opportunity)
        snapshot_before = copy.deepcopy(snapshot.to_dict())
        original_before = copy.deepcopy(opportunity.to_dict())
        replay = b._validate(snapshot)
        require(snapshot.to_dict() == snapshot_before, 'validation mutated replay input')
        require(opportunity.to_dict() == original_before, 'validation mutated original input')
        require(report.fingerprint == opportunity.fingerprint(), 'validation fingerprint mismatch')
        require(report.opportunity_id == opportunity.opportunity_id, 'validation identity mismatch')
        require(report.read_only is True and replay.read_only is True, 'validation is not read-only')
        require(type(report.is_accepted()) is bool, 'non-boolean validation decision')
        require(len(report.checks) > 0, 'validation performed no checks')
        left, right = semantic(report), semantic(replay)
        if left != right:
            labels = ('opportunity_id', 'fingerprint', 'status', 'passed_checks', 'failed_checks',
                      'warning_count', 'info_count', 'checks')
            for label, first, second in zip(labels, left, right):
                if first != second:
                    print('[REPLAY_DIFFERENCE]', label, flush=True)
                    print('[FIRST]', repr(first), flush=True)
                    print('[SECOND]', repr(second), flush=True)
        require(left == right, 'identical-input fixed-clock validation replay differs')
        require(report.is_accepted() == replay.is_accepted(), 'acceptance decision differs')
    require(vars(source) == source_before, 'validation mutated SLOP source')
    print('[FIXED_CLOCK]', FIXED.isoformat(), 'bindings=', bindings)
    print('[VALIDATION_STATUS]', getattr(report.status, 'value', report.status))
    print('[ACCEPTED]', report.is_accepted())
    for check in report.checks:
        if not check.passed:
            print('[CHECK]', check.check_id, getattr(check.severity, 'value', check.severity), check.message)
    print('[PASS] OOI-008C identical-input, fixed-clock validation replay')
    print('[PASS] existing validation decision preserved; no threshold bypass')
    print('[PASS] frozen BUY_PRESSURE / 60 seconds / +10% / -5% / 200 bps')
    print('[PASS] read_only=True execution_authority=FALSE')

if __name__ == '__main__':
    main()
