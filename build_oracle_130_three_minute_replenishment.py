"""ORACLE-130 full installer: 180-second background refresh, continuous fast WS.
Windows CMD: python build_oracle_130_three_minute_replenishment.py
"""
from pathlib import Path
import ast
import os
import py_compile
import shutil
import tempfile

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle129_replenish.py')
BEFORE = 'time.sleep(max(0,30-(time.monotonic()-start)))'
AFTER = 'time.sleep(max(0,180-(time.monotonic()-start)))'


def replacement(source):
    if source.count(AFTER) == 1 and BEFORE not in source:
        return source
    if source.count(BEFORE) != 1 or AFTER in source:
        raise RuntimeError('HOLD_UNEXPECTED_REPLENISHER_CADENCE')
    if 'def cycle():' not in source or 'def clean_env():' not in source:
        raise RuntimeError('HOLD_REPLENISHER_CONTRACT_MISSING')
    if 'universal_crosslist' not in source or 'qarb_071_continuous_mriya_replenishment' not in source:
        raise RuntimeError('HOLD_DISCOVERY_WORKERS_MISSING')
    source = source.replace(BEFORE, AFTER)
    source = source.replace('startup + 30 s cadence', 'startup + 180 s cadence')
    source = source.replace('30 s target between starts', '180 s target between starts')
    return source


def tests():
    fixture = '''def cycle():\n    pass\ndef clean_env():\n    pass\n# universal_crosslist qarb_071_continuous_mriya_replenishment\n# 30 s target between starts\ntime.sleep(max(0,30-(time.monotonic()-start)))\n'''
    revised = replacement(fixture)
    assert AFTER in revised and BEFORE not in revised
    assert replacement(revised) == revised
    assert '180 s target between starts' in revised
    try:
        replacement('def cycle(): pass')
    except RuntimeError:
        pass
    else:
        raise AssertionError('must refuse unsupported source')
    ast.parse(revised)
    print('[PASS] ORACLE-130 cadence, idempotence, fail-closed tests')


def install():
    tests()
    if not TARGET.is_file():
        raise SystemExit('[HOLD] ORACLE-129 replenisher missing: ' + str(TARGET))
    old = TARGET.read_text(encoding='utf-8')
    new = replacement(old)
    ast.parse(new)
    if new != old:
        backup = TARGET.with_suffix('.ORACLE130.preinstall.bak')
        if not backup.exists():
            shutil.copy2(TARGET, backup)
        with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=TARGET.parent,
                                         prefix='.oracle130_', suffix='.py', delete=False) as f:
            tmp = Path(f.name)
            f.write(new)
        try:
            py_compile.compile(str(tmp), doraise=True)
            os.replace(tmp, TARGET)
        finally:
            tmp.unlink(missing_ok=True)
    py_compile.compile(str(TARGET), doraise=True)
    assert replacement(TARGET.read_text(encoding='utf-8')) == TARGET.read_text(encoding='utf-8')
    print('[PASS] ORACLE-130 180-second auxiliary refresh installed')
    print('[PRESERVED] continuous Mriya WS; original Q25/Q20 fast event pricing; 0.010 SOL only')
    print('[PRESERVED] positive-candidate journal; HTTP429 handling; worker separation')
    print('[REPLENISH] first pass at startup, subsequent starts >=180 s apart, never overlap')
    print('[GUARD] signing and broadcasting remain disabled')
    print('[RUN] python oracle120_credentials.py --run')


if __name__ == '__main__':
    install()
