"""OOI-006C: repair the existing materializer; no new runtime subsystem."""
import ast
import hashlib
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REL = Path('qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_006_slop_universal_opportunity_materializer.py')
TARGET = ROOT / REL
TEST = ROOT / 'test_ooi_006c_slop_enum_contract_repair.py'
CANONICAL = 'qseries_v2.oracle_intelligence.universal_opportunity_model.universal_opportunity'
MODULE = '.'.join(REL.with_suffix('').parts)

TEST_SOURCE = '''import copy
import importlib
import json
from types import SimpleNamespace

MODULE = "qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_006_slop_universal_opportunity_materializer"
CANONICAL = "qseries_v2.oracle_intelligence.universal_opportunity_model.universal_opportunity"

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def main():
    m = importlib.import_module(MODULE)
    c = importlib.import_module(CANONICAL)
    require(m.EXECUTION_AUTHORITY is False, 'execution authority changed')
    source = SimpleNamespace(prediction_id='P1', token_address='T1',
        pair_address='PAIR1', frozen_at='2026-09-17T00:00:00Z',
        conditions={'order_flow': 'BUY_PRESSURE'}, horizon_seconds=60,
        target=.10, stop=-.05, friction_bps=200)
    original = copy.deepcopy(vars(source))
    a = m.materialize_slop(source)
    b = m.materialize_slop(copy.deepcopy(source))
    require(isinstance(a, c.UniversalOpportunity), 'not canonical UniversalOpportunity')
    for name, cls, member in (
        ('opportunity_type', c.OpportunityType, 'UNKNOWN'),
        ('direction', c.OpportunityDirection, 'BUY'),
        ('status', c.OpportunityStatus, 'NEW'),
        ('risk_level', c.RiskLevel, 'UNKNOWN')):
        value = getattr(a, name)
        require(isinstance(value, cls) and value is getattr(cls, member), name + ' enum mismatch')
    require(a.read_only is True, 'read_only changed')
    require(a.metadata['execution_authority'] is False, 'metadata authority changed')
    for name in ('frozen_at', 'conditions', 'horizon_seconds', 'target', 'stop', 'friction_bps'):
        require(a.metadata[name] == original[name], 'frozen thesis changed: ' + name)
    require('P1' in a.supporting_prediction_ids, 'prediction lineage missing')
    require(vars(source) == original, 'source mutated')
    fp = a.fingerprint()
    require(isinstance(fp, str) and bool(fp.strip()), 'empty/non-string fingerprint')
    require(fp == a.fingerprint() == b.fingerprint(), 'fingerprint is not repeatable')
    require(a.opportunity_id == b.opportunity_id, 'identity is not repeatable')
    encoded = a.to_dict()
    require(isinstance(encoded, dict), 'to_dict contract failed')
    json.dumps(encoded, sort_keys=True, allow_nan=False)
    require(a.metadata['conditions']['order_flow'] == 'BUY_PRESSURE', 'BUY_PRESSURE lost')
    print('[PASS] canonical enums and direct fingerprint() certification')
    print('[PASS] deterministic identity, serialization, source immutability, prediction lineage')
    print('[PASS] frozen BUY_PRESSURE / 60 seconds / +10% / -5% / 200 bps')
    print('[PASS] OOI-006C read_only=True execution_authority=FALSE')

if __name__ == '__main__':
    main()
'''

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def repaired_source(source):
    tree = ast.parse(source)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'materialize_slop']
    require(len(functions) == 1, 'Expected exactly one existing materialize_slop function')
    calls = [n for n in ast.walk(functions[0]) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name) and n.func.id == 'UniversalOpportunity']
    require(len(calls) == 1, 'Expected one direct UniversalOpportunity constructor; no changes made')
    call = calls[0]
    require(not any(k.arg is None for k in call.keywords), 'Unresolved constructor **kwargs')
    require(not call.args, 'Unresolved positional constructor fields')
    mapping = {'opportunity_type': 'OpportunityType.UNKNOWN',
               'direction': 'OpportunityDirection.BUY',
               'status': 'OpportunityStatus.NEW', 'risk_level': 'RiskLevel.UNKNOWN'}
    keys = {k.arg: k for k in call.keywords}
    require('opportunity_type' in keys and 'direction' in keys, 'Missing known defective fields')
    require(isinstance(keys['opportunity_type'].value, ast.Constant)
            and keys['opportunity_type'].value.value == 'BUY_PRESSURE',
            'Source differs from certified OOI-006 defect; refusing speculative edit')
    require(isinstance(keys['direction'].value, ast.Constant)
            and keys['direction'].value.value == 'BUY', 'Unexpected direction contract')
    for field, member in mapping.items():
        value = ast.parse('_ooi006c_contract.' + member, mode='eval').body
        if field in keys:
            keys[field].value = value
        else:
            call.keywords.append(ast.keyword(arg=field, value=value))
    # Only four constructor fields and one import change. All metadata stays intact.
    statement = ast.Import(names=[ast.alias(name=CANONICAL, asname='_ooi006c_contract')])
    index = 1 if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str) else 0
    while index < len(tree.body) and isinstance(tree.body[index], ast.ImportFrom) and tree.body[index].module == '__future__':
        index += 1
    tree.body.insert(index, statement)
    ast.fix_missing_locations(tree)
    result = ast.unparse(tree) + '\n'
    compile(result, str(TARGET), 'exec')
    return result

def atomic_write(path, data):
    temp = path.with_name(path.name + '.ooi006c.tmp')
    require(not temp.exists(), 'Temporary file already exists: ' + str(temp))
    try:
        temp.write_bytes(data)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()

def clear_target_cache():
    cache = TARGET.parent / '__pycache__'
    if cache.is_dir():
        for file in cache.glob(TARGET.stem + '.*.pyc'):
            file.unlink()

def main():
    require(sys.version_info >= (3, 9), 'Python 3.9+ required')
    require(TARGET.is_file(), 'Run this installer from the repository root: ' + str(TARGET))
    require(not TEST.exists(), 'OOI-006C test already exists; run that test instead')
    original = TARGET.read_bytes()
    updated = repaired_source(original.decode('utf-8-sig')).encode('utf-8')
    compile(TEST_SOURCE, str(TEST), 'exec')
    backup = TARGET.with_name(TARGET.name + '.pre_ooi006c_' + hashlib.sha256(original).hexdigest()[:12] + '.bak')
    if backup.exists():
        require(backup.read_bytes() == original, 'Backup conflict')
    else:
        backup.write_bytes(original)
    TEST.write_text(TEST_SOURCE, encoding='utf-8')
    try:
        require(TARGET.read_bytes() == original, 'Materializer changed during installation')
        atomic_write(TARGET, updated)
        clear_target_cache()
        result = subprocess.run([sys.executable, '-B', str(TEST)], cwd=str(ROOT))
        require(result.returncode == 0, 'OOI-006C physical test failed')
    except BaseException:
        if TARGET.read_bytes() == updated:
            atomic_write(TARGET, original)
            clear_target_cache()
            print('[ROLLBACK] original materializer restored', flush=True)
        raise
    print('[PASS] OOI-006C repaired existing foundational materializer', flush=True)
    print('[NEXT] OOI-007B remains gated on this physical PASS', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI-006C: ' + str(exc), flush=True)
        print('[STOP] Do not proceed to OOI-007B', flush=True)
        sys.exit(1)
