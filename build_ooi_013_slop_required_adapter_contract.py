"""OOI-013: declare the canonical Solana adapter requirement in the existing materializer."""
import ast
import hashlib
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_006_slop_universal_opportunity_materializer.py'
CANONICAL = ROOT / 'qseries_v2/oracle_intelligence/universal_opportunity_model/universal_opportunity.py'
TEST = ROOT / 'test_ooi_013_slop_required_adapter_contract.py'
TEST_SOURCE = "import copy\nimport importlib\nfrom test_ooi_008c_slop_existing_oos_validation_replay_certification import fixed_validation_clock, fixture, verify\n\nb = importlib.import_module('qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_007b_slop_existing_oos_intake')\n\ndef require(value, message):\n    if not value:\n        raise AssertionError(message)\n\ndef main():\n    source = fixture()\n    original = copy.deepcopy(vars(source))\n    with fixed_validation_clock():\n        opportunity, report = b.validate_slop(source)\n        verify(opportunity, source)\n        require(opportunity.execution.required_execution_adapter == 'solana_wallet', 'wrong adapter requirement')\n        require(opportunity.confidence == 0 and opportunity.expected_edge == 0, 'unproven confidence or edge introduced')\n        checks = {check.check_id: check for check in report.checks}\n        require(checks['business.execution_adapter_required'].passed is True, 'adapter declaration not recognized')\n        require(checks['business.confidence_minimum'].passed is False, 'confidence guard bypassed')\n        require(checks['business.edge_minimum'].passed is False, 'edge guard bypassed')\n        require(report.is_accepted() is False, 'unproven opportunity admitted')\n        replay, repeated = b.validate_slop(copy.deepcopy(source))\n        require(opportunity.fingerprint() == replay.fingerprint(), 'identity differs on replay')\n        require(report.is_accepted() == repeated.is_accepted(), 'decision differs on replay')\n        result, reports = b.rank_validated_slop([source])\n        require(result.ranked_count == 0 and not reports[0].is_accepted(), 'rejected candidate entered feed')\n    require(vars(source) == original, 'SLOP input mutated')\n    print('[PASS] OOI-013 canonical required adapter metadata: solana_wallet')\n    print('[PASS] confidence/edge remain zero; default validation still rejects candidate')\n    print('[PASS] frozen thesis and execution_authority=FALSE preserved')\n    print('[SCOPE] Requirement declaration only; no adapter resolution, invocation, or availability certification')\n\nif __name__ == '__main__':\n    main()\n"

def require(value, message):
    if not value:
        raise RuntimeError(message)

def is_constructor(node, name):
    return isinstance(node, ast.Call) and (isinstance(node.func, ast.Name) and node.func.id == name or isinstance(node.func, ast.Attribute) and node.func.attr == name)

def transform(source, canonical):
    canonical_tree = ast.parse(canonical)
    factories = [n for n in ast.walk(canonical_tree) if isinstance(n, ast.FunctionDef) and n.name == 'solana_token_snipe']
    require(len(factories) == 1, 'Canonical Solana factory is ambiguous or absent')
    declarations = [k.value.value for n in ast.walk(factories[0]) if is_constructor(n, 'OpportunityExecutionProfile')
        for k in n.keywords if k.arg == 'required_execution_adapter' and isinstance(k.value, ast.Constant)]
    require(declarations == ['solana_wallet'], 'Canonical adapter contract differs; no changes made')
    tree = ast.parse(source)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'materialize_slop']
    require(len(functions) == 1, 'Expected one materialize_slop')
    calls = [n for n in ast.walk(functions[0]) if is_constructor(n, 'UniversalOpportunity')]
    require(len(calls) == 1, 'Expected one canonical opportunity construction')
    call = calls[0]
    require(not call.args and all(k.arg is not None for k in call.keywords), 'Unresolved positional arguments or kwargs')
    existing = [k for k in call.keywords if k.arg == 'execution']
    require(not existing, 'Existing execution mapping requires inspection; refusing replacement')
    expression = ast.parse('_ooi013_contract.OpportunityExecutionProfile(required_execution_adapter="solana_wallet")', mode='eval').body
    call.keywords.append(ast.keyword(arg='execution', value=expression))
    statement = ast.Import(names=[ast.alias(name='qseries_v2.oracle_intelligence.universal_opportunity_model.universal_opportunity', asname='_ooi013_contract')])
    index = 1 if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str) else 0
    while index < len(tree.body) and isinstance(tree.body[index], ast.ImportFrom) and tree.body[index].module == '__future__':
        index += 1
    tree.body.insert(index, statement)
    ast.fix_missing_locations(tree)
    return ast.unparse(tree) + '\n'

def write_atomic(path, data):
    temp = path.with_name(path.name + '.ooi013.tmp')
    require(not temp.exists(), 'Existing temporary file')
    try:
        temp.write_bytes(data)
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
    previous = ROOT / 'test_ooi_011b_slop_existing_oos_integration.py'
    require(previous.is_file() and TARGET.is_file() and CANONICAL.is_file(), 'Required certified source/test missing')
    require(not TEST.exists(), 'OOI-013 test already exists; inspect prior result before reinstalling')
    require(subprocess.run([sys.executable, '-B', str(previous)], cwd=str(ROOT)).returncode == 0, 'Preceding gate failed')
    original = TARGET.read_bytes()
    updated = transform(original.decode('utf-8-sig'), CANONICAL.read_text(encoding='utf-8-sig')).encode('utf-8')
    compile(updated, str(TARGET), 'exec')
    compile(TEST_SOURCE, str(TEST), 'exec')
    backup = TARGET.with_name(TARGET.name + '.pre_ooi013_' + hashlib.sha256(original).hexdigest()[:12] + '.bak')
    require(not backup.exists() or backup.read_bytes() == original, 'Backup conflict')
    if not backup.exists():
        backup.write_bytes(original)
    TEST.write_text(TEST_SOURCE, encoding='utf-8')
    changed = False
    try:
        require(TARGET.read_bytes() == original, 'Concurrent source change')
        write_atomic(TARGET, updated)
        changed = True
        clear_cache()
        require(subprocess.run([sys.executable, '-B', str(TEST)], cwd=str(ROOT)).returncode == 0, 'Physical adapter contract test failed')
    except BaseException:
        if changed and TARGET.read_bytes() == updated:
            write_atomic(TARGET, original)
            clear_cache()
            print('[ROLLBACK] original materializer restored', flush=True)
        raise
    print('[PASS] OOI-013 existing materializer updated; execution_authority=FALSE', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('[FAIL] OOI-013: ' + str(exc), flush=True)
        print('[STOP] Return complete output', flush=True)
        sys.exit(1)
