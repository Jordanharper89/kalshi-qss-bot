
"""MTR-148: extract trusted implementation surfaces without importing runtime code."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'runtime_state/oracle/oracle_live_execution/mtr_148_official_verifier_binding_contract.json'
SOURCES = {
    'atomic_preflight': 'mtr_119_canonical_alt_atomic_preflight.py',
    'canonical_runtime': 'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py',
    'warm_cutover': 'mtr_114_controlled_replenishment_warm_cutover.py',
    'snapshot_pricer': 'qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py',
    'protected_gate': 'qseries_v2/oracle_execution/solana_atomic_executor/mtr_147_protected_economics_gate.py',
}
TOKENS = (
    'swap2', 'pumpswap', 'pump_sdk', 'min_out', 'minout', 'max_quote',
    'maxquote', 'simulate', 'simulation', 'atomic', 'priority_fee',
    'fee_lamports', 'residue', 'reconcil', 'protected', 'signed', 'quote',
)
DANGEROUS = ('private_key', 'secret_key', 'seed_phrase', 'mnemonic', 'keypair')

def line_symbols(path):
    """Only structural information: never dump code, literals or secrets."""
    data = path.read_text(encoding='utf-8', errors='replace')
    tree = ast.parse(data, filename=path.name)
    rows = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            if any(t in name.lower() for t in TOKENS):
                rows.append({'kind':type(node).__name__, 'name':name, 'line':node.lineno,
                    'args': [] if isinstance(node, ast.ClassDef) else [a.arg for a in node.args.args if not any(x in a.arg.lower() for x in DANGEROUS)]})
        if isinstance(node, ast.Call):
            # Inspect only an AST function path. Never extract call arguments.
            fn = node.func
            parts = []
            while isinstance(fn, ast.Attribute):
                parts.insert(0, fn.attr)
                fn = fn.value
            if isinstance(fn, ast.Name):
                parts.insert(0, fn.id)
            if parts and any(t in '.'.join(parts).lower() for t in TOKENS):
                pathstr = '.'.join(parts)
                if not any(x in pathstr.lower() for x in DANGEROUS):
                    rows.append({'kind':'Call', 'name':pathstr[:120], 'line':node.lineno})
    return sorted(rows, key=lambda r:(r['line'],r['name']))[:250]

def run():
    report = {'mtr':'MTR-148','mode':'READ_ONLY_OFFICIAL_VERIFIER_BINDING_CONTRACT',
        'sources':{},'missing':[], 'verified_protected_profit':False,
        'official_verifier_connected':False,'atomic_two_leg_proof_closed':False,
        'production_cutover':False,'scanner_modified':False,'private_key_used':False,
        'signing':False,'broadcast':False}
    for label, rel in SOURCES.items():
        src = ROOT / rel
        if not src.is_file():
            report['missing'].append(rel)
            continue
        try:
            report['sources'][label] = {'path':rel,'symbols':line_symbols(src)}
        except (OSError,SyntaxError,UnicodeError) as exc:
            report['missing'].append(rel+':'+type(exc).__name__)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2),encoding='utf-8')
    for label, obj in report['sources'].items():
        print('[MTR148_SOURCE]',label,obj['path'],'symbols=',len(obj['symbols']))
        for item in obj['symbols'][:35]:
            print('[MTR148_SYMBOL]',label,item['line'],item['kind'],item['name'])
    print('[MTR148_MISSING]',len(report['missing']))
    for path in report['missing']:
        print('[MTR148_MISSING_PATH]',path)
    print('[OFFICIAL_VERIFIER_CONNECTED] FALSE')
    print('[ATOMIC_TWO_LEG_PROOF_CLOSED] FALSE')
    print('[PRODUCTION_CUTOVER] FALSE')
    print('[SCANNER] FROZEN')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')
    print('[REPORT]',OUT)
    if report['missing']:
        raise SystemExit('[HOLD] Required implementation source absent')
    return report

if __name__=='__main__':
    run()

