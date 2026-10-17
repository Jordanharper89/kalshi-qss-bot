"""Read-only contract probe for ORACLE020's q18 exact pricing lineage."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LANE = ROOT / 'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'
OUT = ROOT / 'runtime_state/oracle/oracle_live_execution/mtr_146_official_pricer_lineage.json'


def resolve_import(tree, alias):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                if (item.asname or item.name.split('.')[0]) == alias:
                    return item.name
        if isinstance(node, ast.ImportFrom):
            for item in node.names:
                if (item.asname or item.name) == alias:
                    return (node.module + '.' + item.name) if node.module else None
    return None


def inspect_function(path, name):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    defs = [x for x in ast.walk(tree) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)) and x.name == name]
    if not defs:
        return None
    d = defs[0]
    calls = sorted(set(ast.unparse(n.func) for n in ast.walk(d) if isinstance(n, ast.Call)))
    keys = sorted(set(n.value for n in ast.walk(d) if isinstance(n, ast.Constant) and isinstance(n.value, str)
                      and any(t in n.value.lower() for t in ('net','fee','min','max','out','profit','bps','quote','route','pump','meteora','size','slip'))))
    return {'line': d.lineno, 'positional': [a.arg for a in d.args.posonlyargs+d.args.args],
            'kwonly': [a.arg for a in d.args.kwonlyargs], 'calls': calls[:100],
            'economic_field_literals': keys[:100], 'returns': sum(isinstance(n, ast.Return) for n in ast.walk(d))}


def run():
    if not LANE.is_file():
        raise SystemExit('[HOLD] ORACLE020 source missing')
    tree = ast.parse(LANE.read_text(encoding='utf-8'))
    modname = resolve_import(tree, 'q18')
    path = ROOT.joinpath(*(modname or '').split('.')).with_suffix('.py') if modname else None
    found = bool(path and path.is_file())
    exact = inspect_function(path, 'exact_snapshot_opportunities') if found else None
    worker = inspect_function(path, 'worker') if found else None
    lane_price = inspect_function(LANE, '_price')
    result = {'mtr': 'MTR-146', 'q18_import': modname, 'q18_file': str(path.relative_to(ROOT)) if found else None,
              'exact_function': exact, 'worker_function': worker, 'lane_price': lane_price,
              'module_resolved': found, 'exact_function_found': bool(exact),
              'official_protected_economics_verified': False,
              'live_pricing_cutover': False, 'scanner_modified': False,
              'private_key_used': False, 'signing': False, 'broadcast': False}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('[MTR146_Q18_IMPORT]', modname)
    print('[MTR146_Q18_FILE]', result['q18_file'])
    for key in ('exact_function', 'worker_function', 'lane_price'):
        value = result[key]
        print('[MTR146_FUNCTION]', key, 'FOUND' if value else 'MISSING')
        if value:
            print('[MTR146_ARGS]', key, value['positional'], value['kwonly'])
            print('[MTR146_CALLS]', key, ','.join(value['calls'][:35]))
            print('[MTR146_ECONOMIC_FIELDS]', key, ','.join(value['economic_field_literals'][:35]))
    print('[OFFICIAL_PROTECTED_ECONOMICS_VERIFIED] FALSE')
    print('[PRODUCTION_CUTOVER] FALSE')
    print('[SCANNER] FROZEN')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')
    print('[REPORT]', OUT)
    if not found or not exact:
        raise SystemExit('[HOLD] Official pricing function lineage unresolved')
    return result

if __name__ == '__main__':
    run()
