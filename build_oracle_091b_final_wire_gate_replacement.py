"""ORACLE-091B complete replacement installer: final fail-closed wire gate.
No network calls, ALT mutation, signing, broadcasting, or scanner changes.
"""
import argparse
import ast
import shutil
from pathlib import Path

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
V77 = ROOT / 'oracle_077_native_executor.py'
V80 = ROOT / 'oracle_080_v1_atomic_fallback.py'
MARK = '# ORACLE091B_EXPORTED_COMPILER_FINAL_WIRE_GATE'
APPEND = '''

# ORACLE091B_EXPORTED_COMPILER_FINAL_WIRE_GATE
_oracle091b_previous_compile_native = compile_native

def compile_native(user, route, core, q87, root, extra_alt=None):
    """Gate every compiler result, including all v0/v1 fallbacks."""
    result = _oracle091b_previous_compile_native(
        user, route, core, q87, root, extra_alt)
    if not isinstance(result, dict):
        raise RuntimeError('ORACLE091B_COMPILER_RESULT_INVALID')
    if not result.get('ok'):
        return result
    wire = result.get('raw')
    declared = result.get('bytes')
    size = len(wire) if isinstance(wire, (bytes, bytearray)) else -1
    if not 66 <= size <= 1232 or type(declared) is not int or declared != size:
        rejected = dict(result)
        rejected.pop('raw', None)
        rejected.pop('msg', None)
        rejected.pop('used_alts', None)
        rejected['ok'] = False
        rejected['reason'] = 'ORACLE091B_HOLD_FINAL_WIRE_SIZE_OR_INTEGRITY'
        rejected['rejected_wire_bytes'] = size
        rejected['bytes'] = 0
        print('[ORACLE091B_WIRE_REJECT] size=%d declared=%s limit=1232' %
              (size, str(declared)[:24]), flush=True)
        return rejected
    print('[ORACLE091B_WIRE_PASS] size=%d limit=1232' % size, flush=True)
    return result
'''


def transform77(src):
    ast.parse(src)
    if MARK in src:
        if src.count(MARK) != 1:
            raise RuntimeError('ORACLE091B_DUPLICATE_MARKER')
        return src
    tree = ast.parse(src)
    if not any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and
               n.name == 'compile_native' for n in tree.body):
        raise RuntimeError('ORACLE091B_COMPILE_NATIVE_NOT_FOUND')
    out = src.rstrip() + '\n' + APPEND
    ast.parse(out)
    return out


def transform80(src):
    ast.parse(src)
    if 'MAX_V1 = 1232' in src:
        return src
    if src.count('MAX_V1 = 4096') != 1:
        raise RuntimeError('ORACLE091B_V80_LIMIT_UNRECOGNIZED')
    out = src.replace('MAX_V1 = 4096', 'MAX_V1 = 1232', 1)
    ast.parse(out)
    return out


def tests():
    fixture = '''def compile_native(user, route, core, q87, root, extra_alt=None):
    return {'ok': True, 'raw': bytes(route), 'bytes': route, 'msg': 'message', 'used_alts': []}
'''
    ns = {}
    exec(compile(transform77(fixture), '<fixture>', 'exec'), ns)
    for size in (1233, 1372, 4096):
        result = ns['compile_native'](None, size, None, None, None)
        assert result['ok'] is False and result['rejected_wire_bytes'] == size
        assert 'raw' not in result and 'msg' not in result
    for size in (1217, 1232):
        result = ns['compile_native'](None, size, None, None, None)
        assert result['ok'] and result['bytes'] == size
    assert transform77(transform77(fixture)) == transform77(fixture)
    bad = fixture.replace("'bytes': route", "'bytes': route+1")
    ns = {}
    exec(compile(transform77(bad), '<fixture>', 'exec'), ns)
    assert not ns['compile_native'](None, 1217, None, None, None)['ok']
    assert transform80('MAX_V1 = 4096\n') == 'MAX_V1 = 1232\n'
    assert transform80('MAX_V1 = 1232\n') == 'MAX_V1 = 1232\n'
    for p in (V77, V80):
        if not p.is_file():
            raise RuntimeError('ORACLE091B_DEPENDENCY_MISSING:' + str(p))
        ast.parse(p.read_text(encoding='utf-8'))
    print('[PASS] ORACLE091B_OVERSIZE_UNDERSIZE_DECLARED_SIZE_AND_REPEAT_TESTS')
    print('[BOUNDARY] NO_RPC NO_KEYS NO_SIGNING NO_BROADCAST NO_SCANNER_EDIT')


def install():
    tests()
    before = {p: p.read_text(encoding='utf-8') for p in (V77, V80)}
    after = {V77: transform77(before[V77]), V80: transform80(before[V80])}
    changed = [p for p in (V77, V80) if before[p] != after[p]]
    if not changed:
        print('[PASS] ORACLE091B_ALREADY_INSTALLED')
        return
    backups = {p: p.with_name(p.stem + '.before_oracle091b.py') for p in changed}
    for p, backup in backups.items():
        if backup.exists():
            raise RuntimeError('ORACLE091B_BACKUP_EXISTS:' + str(backup))
    completed = []
    try:
        for p in changed:
            shutil.copy2(p, backups[p])
            tmp = p.with_suffix('.oracle091b.tmp')
            tmp.write_text(after[p], encoding='utf-8')
            tmp.replace(p)
            completed.append(p)
        for p in changed:
            assert p.read_text(encoding='utf-8') == after[p]
        tests()
    except Exception:
        for p in completed:
            p.write_text(before[p], encoding='utf-8')
        print('[ROLLBACK] ORACLE091B_RESTORED_ORIGINAL_SOURCES')
        raise
    print('[PASS] ORACLE091B_FINAL_WIRE_GATE_INSTALLED')
    print('[HOLD] NO_ATOMIC_SIMULATION_OR_PROFIT_CERTIFICATION')
    print('[NEXT] Forward route 1343 bytes needs valid ALT coverage or safe instruction compression')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    tests() if args.test else install()
