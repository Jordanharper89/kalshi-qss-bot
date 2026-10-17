from pathlib import Path
import ast

R = Path(__file__).resolve().parent
P = R / 'qseries_v2/oracle_execution/solana_atomic_executor'
M = P / 'mtr_150_simulation_input_contract.py'
T = R / 'test_mtr_150_simulation_input_contract.py'
MODULE = r'''
"""Inspect, never invoke, simulation and compiler boundaries."""
import ast, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'runtime_state/oracle/oracle_live_execution/mtr_150_simulation_input_contract.json'
SOURCES = {
    'runtime': 'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py',
    'preflight': 'mtr_119_canonical_alt_atomic_preflight.py',
    'gate': 'qseries_v2/oracle_execution/solana_atomic_executor/mtr_147_protected_economics_gate.py'
}
TARGETS = {'runtime': ('simulate_current',),
           'preflight': ('AtomicPreflight',),
           'gate': ('ProtectedEvidence', 'ProtectedCandidateGate')}
SENSITIVE = ('signed_tx', 'keypair', 'private_key', 'send_transaction',
             'send_raw_transaction', 'broadcast', 'submit', 'sign')

def dotted(n):
    try:
        return ast.unparse(n)
    except (ValueError, TypeError):
        return '?'

def inspect(path, targets):
    raw = path.read_bytes()
    tree = ast.parse(raw.decode('utf-8-sig', errors='replace'))
    found = {}
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name in targets:
            arguments = [] if isinstance(n, ast.ClassDef) else [a.arg for a in n.args.posonlyargs + n.args.args + n.args.kwonlyargs]
            calls = sorted(set(dotted(x.func) for x in ast.walk(n) if isinstance(x, ast.Call)))
            returns = sorted(set(dotted(x.value)[:100] for x in ast.walk(n) if isinstance(x, ast.Return) and x.value))
            fields = sorted(set(dotted(x)[:100] for x in ast.walk(n) if isinstance(x, ast.Attribute)))
            risks = [x for x in calls if any(s in x.lower() for s in SENSITIVE)]
            found[n.name] = {'line': n.lineno, 'args': arguments,
                'calls': calls[:100], 'returns': returns[:20],
                'fields': fields[:120], 'sensitive_calls': risks}
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'targets': found}

def run():
    report = {'mtr': 'MTR-150', 'mode': 'AST_ONLY', 'sources': {},
        'missing': [], 'simulator_invoked': False, 'verifier_connected': False,
        'atomic_proof_closed': False, 'cutover': False, 'signing': False,
        'broadcast': False, 'private_key_used': False, 'scanner_modified': False}
    for label, rel in SOURCES.items():
        path = ROOT / rel
        if not path.is_file():
            report['missing'].append(rel)
            continue
        data = inspect(path, TARGETS[label])
        report['sources'][label] = data
        for name in TARGETS[label]:
            if name not in data['targets']:
                report['missing'].append(label + ':' + name)
            else:
                entry = data['targets'][name]
                print('[MTR150_TARGET]', label, name, 'args=', ','.join(entry['args']))
                print('[MTR150_CALLS]', label, name, ','.join(entry['calls'][:35]))
                print('[MTR150_RETURNS]', label, name, ','.join(entry['returns'][:10]))
                print('[MTR150_SENSITIVE_DEPS]', label, name, ','.join(entry['sensitive_calls']) or 'NONE_IN_TARGET')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('[MTR150_MISSING]', report['missing'])
    print('[SIMULATOR_INVOKED] FALSE')
    print('[OFFICIAL_VERIFIER_CONNECTED] FALSE')
    print('[ATOMIC_TWO_LEG_PROOF_CLOSED] FALSE')
    print('[PRODUCTION_CUTOVER] FALSE')
    print('[SCANNER] FROZEN')
    print('[PRIVATE_KEY] NOT_USED')
    print('[SIGNING] FALSE')
    print('[BROADCAST] FALSE')
    print('[REPORT]', OUT)
    if report['missing']:
        raise SystemExit('[HOLD] Missing physical contract')
    return report

if __name__ == '__main__':
    run()
'''
TEST = r'''
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_150_simulation_input_contract as m

class Tests(unittest.TestCase):
    def test_ast_probe_does_not_import_or_call_source(self):
        with TemporaryDirectory() as d:
            p = Path(d) / 'example.py'
            p.write_text('def simulate_current(compiled, user):\n    return rpc(compiled, user)\n', encoding='utf-8')
            x = m.inspect(p, ('simulate_current',))
            self.assertEqual(x['targets']['simulate_current']['args'], ['compiled', 'user'])
            self.assertIn('rpc', x['targets']['simulate_current']['calls'])

    def test_real_contract_targets(self):
        for label, rel in m.SOURCES.items():
            path = m.ROOT / rel
            self.assertTrue(path.is_file(), rel)
            x = m.inspect(path, m.TARGETS[label])
            for name in m.TARGETS[label]:
                self.assertIn(name, x['targets'])

    def test_simulation_signature_and_fail_closed(self):
        x = m.inspect(m.ROOT / m.SOURCES['runtime'], ('simulate_current',))
        self.assertEqual(x['targets']['simulate_current']['args'], ['compiled', 'user'])
        r = m.run()
        for key in ('simulator_invoked', 'verifier_connected', 'atomic_proof_closed',
                    'cutover', 'signing', 'broadcast', 'private_key_used', 'scanner_modified'):
            self.assertFalse(r[key], key)

if __name__ == '__main__':
    unittest.main(verbosity=2)
'''
if not (P / 'mtr_147_protected_economics_gate.py').is_file():
    raise SystemExit('[HOLD] MTR-147 required')
for source in (MODULE, TEST):
    ast.parse(source)
M.write_text(MODULE, encoding='utf-8')
T.write_text(TEST, encoding='utf-8')
print('[PASS] MTR-150 full installer installed')
print('[SCOPE] Targeted AST-only boundary; simulator not invoked')
print('[SCANNER] FROZEN')
print('[PRIVATE_KEY] NOT_USED')
print('[SIGNING] FALSE')
print('[BROADCAST] FALSE')
