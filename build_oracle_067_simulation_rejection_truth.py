"""ORACLE-067: preserve bounded native simulation rejection evidence."""
from pathlib import Path
import ast
import shutil
import sys

BASE = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGETS = {
    'oracle_050_original_scanner_executor_consolidation.py': (
        'print("[ATOMIC_SIM] REJECTED", flush=True)',
        'print("[ATOMIC_SIM] REJECTED", _oracle067_sim_truth(sim), flush=True)',
    ),
    'oracle_054_reverse_native_handoff.py': (
        'print("[ORACLE054_SIM] REJECTED", flush=True)',
        'print("[ORACLE054_SIM] REJECTED", _oracle067_sim_truth(sim), flush=True)',
    ),
}
HELPER = '''# ORACLE067_BOUNDED_SIMULATION_REJECTION_TRUTH

def _oracle067_sim_truth(sim):
    """Only sanitized diagnostic structure; never expose credentials or packets."""
    if not isinstance(sim, dict):
        return {"response_type": type(sim).__name__, "reason": "NON_DICT_RESPONSE"}
    out = {}
    for key in ("err", "unitsConsumed", "logs", "reason", "error"):
        if key not in sim:
            continue
        value = sim[key]
        if key == "logs":
            if isinstance(value, list):
                out["log_count"] = len(value)
                out["program_failure_logs"] = [
                    str(x)[:160] for x in value
                    if isinstance(x, str) and ("failed:" in x or "Error:" in x)
                ][:3]
            continue
        if key == "unitsConsumed" and type(value) is int:
            out[key] = value
        elif key in ("err", "reason", "error"):
            out[key + "_type"] = type(value).__name__
            if isinstance(value, (str, int, float, bool, type(None))):
                out[key] = str(value)[:160]
            elif isinstance(value, dict):
                out[key + "_keys"] = sorted(str(k)[:40] for k in value)[:12]
    return out or {"reason": "NO_DIAGNOSTIC_FIELDS"}

'''


def transformed(name, source):
    marker = 'ORACLE067_BOUNDED_SIMULATION_REJECTION_TRUTH'
    if marker in source:
        assert '_oracle067_sim_truth(sim)' in source, 'PARTIAL_ORACLE067_INSTALL'
        return source
    old, new = TARGETS[name]
    assert source.count(old) == 1, 'SOURCE_ANCHOR_MISMATCH_' + name
    assert 'def ' in source and 'simulate_current' in source, 'SIMULATION_BOUNDARY_MISSING'
    source = HELPER + source.replace(old, new, 1)
    original = source[len(HELPER):]
    tree = ast.parse(original)
    nodes = tree.body
    index = 0
    if nodes and isinstance(nodes[0], ast.Expr) and isinstance(nodes[0].value, ast.Constant) and isinstance(nodes[0].value.value, str):
        index = nodes[0].end_lineno
    for node in nodes:
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node.lineno >= index:
            index = node.end_lineno
    lines = original.splitlines(keepends=True)
    source = ''.join(lines[:index]) + '\n' + HELPER + ''.join(lines[index:])
    ast.parse(source)
    return source


def test():
    for name in TARGETS:
        example = '"""doc"""\nimport os\n\ndef simulate_current():\n    print("[ATOMIC_SIM] REJECTED", flush=True)\n    print("[ORACLE054_SIM] REJECTED", flush=True)\n'
        changed = transformed(name, example)
        assert transformed(name, changed) == changed
        ast.parse(changed)
    print('[PASS] ORACLE067 idempotence and AST')
    print('[BOUNDARY] NO_RPC_NO_SIGNING_NO_BROADCAST')


def install():
    pending = []
    for name in TARGETS:
        path = BASE / name
        assert path.is_file(), 'MISSING_' + name
        old = path.read_text(encoding='utf-8')
        new = transformed(name, old)
        pending.append((path, old, new))
    for path, old, new in pending:
        if old == new:
            print('[ALREADY_INSTALLED]', path.name)
            continue
        backup = path.with_name(path.stem + '.before_oracle067.py')
        if not backup.exists():
            shutil.copy2(path, backup)
        path.write_text(new, encoding='utf-8')
        print('[PASS]', path.name)
    print('[BOUNDARY] DIAGNOSTICS_ONLY_NO_RPC_NO_SIGNING_NO_BROADCAST')


if __name__ == '__main__':
    test() if '--test' in sys.argv else install()