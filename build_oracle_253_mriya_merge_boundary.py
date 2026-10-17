"""ORACLE-253: offline Mriya merge-branch inspection. No RPC or execution."""
import argparse
import ast
import json
from pathlib import Path

SOURCE = Path('qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/engine.py')
PRIOR = Path('runtime_state/oracle/oracle_live_execution/ORACLE252_MRIYA_HANDOFF.json')
OUT = Path('runtime_state/oracle/oracle_live_execution/ORACLE253_MRIYA_MERGE_BOUNDARY.json')
TARGETS = ('mriya_hot_tokens', 'raw_candidate_universe', 'candidate_universe')


def expression(node):
    """Disclose code structure without exposing hardcoded literals or secrets."""
    text = ast.unparse(node)
    if len(text) > 220:
        return '[EXPRESSION_OVER_220_CHARS]'
    if any(term in text.lower() for term in ('secret', 'api_key', 'authorization', 'private_key', 'helius')):
        return '[POTENTIALLY_SENSITIVE_EXPRESSION]'
    return text


def branch_info(fn):
    findings = []
    for n in ast.walk(fn):
        if isinstance(n, (ast.If, ast.While, ast.IfExp)):
            findings.append({'line': n.lineno, 'type': type(n).__name__,
                             'condition': expression(n.test)})
        elif isinstance(n, ast.For):
            findings.append({'line': n.lineno, 'type': 'For',
                             'target': expression(n.target),
                             'iter': expression(n.iter)})
        elif isinstance(n, ast.Return) and n.value is not None:
            findings.append({'line': n.lineno, 'type': 'Return',
                             'value': expression(n.value)})
        elif isinstance(n, ast.Assign):
            lhs = ','.join(expression(t) for t in n.targets)
            if any(word in lhs.lower() for word in ('raw', 'hot', 'mriya', 'candidate', 'found', 'limit', 'cap', 'token', 'mint', 'out')):
                findings.append({'line': n.lineno, 'type': 'Assign',
                                 'target': lhs[:120], 'value': expression(n.value)})
        elif isinstance(n, ast.Call):
            label = expression(n.func)
            if any(term in label.lower() for term in ('append', 'extend', 'update', 'discover', 'mriya', 'universe', 'sorted', 'set')):
                findings.append({'line': n.lineno, 'type': 'Call', 'name': label})
    return sorted(findings, key=lambda x: x['line'])[:100]


def analyze(source, prior):
    tree = ast.parse(source)
    funcs = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    absent = sorted(set(TARGETS) - set(funcs))
    records = [{'function': name, 'first_line': funcs[name].lineno,
                'branch_flow': branch_info(funcs[name])} for name in TARGETS if name in funcs]
    hot = set(prior.get('mriya_missing_from_raw', []))
    overlap = set(prior.get('mriya_raw_overlap', []))
    exact = set(prior.get('mriya_exact_overlap', []))
    return {
        'build': 'ORACLE253', 'source': str(SOURCE), 'function_count': len(records),
        'missing_functions': absent, 'functions': records,
        'previous_handoff': {'mriya_identities': prior.get('mriya_return_identities'),
                             'raw_identities': prior.get('raw_identities'),
                             'exact_identities': prior.get('exact_candidate_identities'),
                             'mriya_raw_overlap': len(overlap),
                             'mriya_exact_overlap': len(exact),
                             'mriya_excluded_from_raw': sorted(hot)},
        'root_cause_certified': False, 'current_live_freshness_certified': False,
        'execution_admission': False, 'signing': False, 'broadcast': False,
        'status': 'HOLD_MRIYA_MERGE_DECISION_REQUIRED'
    }


def test():
    src = '''def mriya_hot_tokens(root):
    return []
def raw_candidate_universe(root):
    a = mriya_hot_tokens(root)
    if not a:
        return []
    return a
def candidate_universe(root):
    return raw_candidate_universe(root)
'''
    prior = {'mriya_return_identities': 2, 'raw_identities': 1,
             'mriya_missing_from_raw': ['A'*32], 'mriya_raw_overlap': ['B'*32],
             'mriya_exact_overlap': ['B'*32]}
    result = analyze(src, prior)
    assert result['function_count'] == 3
    assert result['previous_handoff']['mriya_excluded_from_raw'] == ['A'*32]
    assert any(x['type']=='If' for x in result['functions'][1]['branch_flow'])
    assert not result['execution_admission'] and not result['root_cause_certified']
    print('[ORACLE253_TEST_PASS] source_branches=TRUE prior_lineage=TRUE no_execution=TRUE')


def run():
    if not SOURCE.is_file() or not PRIOR.is_file():
        raise RuntimeError('HOLD_REQUIRED_LOCAL_FILES_MISSING')
    prior = json.loads(PRIOR.read_text(encoding='utf-8'))
    if prior.get('build') != 'ORACLE252' or prior.get('signing') is not False or prior.get('broadcast') is not False:
        raise RuntimeError('HOLD_UNTRUSTED_PRIOR_REPORT')
    result = analyze(SOURCE.read_text(encoding='utf-8'), prior)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('[ORACLE253_RESULT]', json.dumps({'functions': result['function_count'],
        'missing_functions': result['missing_functions'],
        'mriya_missing_from_raw': len(result['previous_handoff']['mriya_excluded_from_raw']),
        'status': result['status'], 'signing': False, 'broadcast': False}, sort_keys=True))
    for fn in result['functions']:
        print('[ORACLE253_BRANCHES]', json.dumps(fn, sort_keys=True))
    print('[REPORT]', OUT)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--test', action='store_true')
    p.add_argument('--run', action='store_true')
    a = p.parse_args()
    if not (a.test or a.run):
        p.error('specify --test or --run')
    if a.test:
        test()
    if a.run:
        run()