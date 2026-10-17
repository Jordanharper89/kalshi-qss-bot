
"""ORACLE-091: full installer, fail-closed post-compiler wire validation.
No scanner edits, network calls, secrets, ALT changes, signing, or broadcast.
"""
import argparse
import ast
import shutil
from pathlib import Path

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
V77 = ROOT / 'oracle_077_native_executor.py'
V80 = ROOT / 'oracle_080_v1_atomic_fallback.py'
MARK = '# ORACLE091_FINAL_WIRE_TRUTH'

GUARD = '''    # ORACLE091_FINAL_WIRE_TRUTH: apply AFTER all v0/v1 fallbacks.
    if result.get('ok'):
        wire = result.get('raw')
        size = len(wire) if isinstance(wire, (bytes, bytearray)) else -1
        declared = result.get('bytes')
        if size < 66 or size > 1232 or type(declared) is not int or declared != size:
            result = dict(result)
            result.pop('raw', None)
            result.pop('msg', None)
            result['ok'] = False
            result['reason'] = 'ORACLE091_HOLD_FINAL_WIRE_SIZE_OR_INTEGRITY'
            result['rejected_wire_bytes'] = size
            result['bytes'] = 0
            print('[ORACLE091_WIRE_REJECT] size=%d limit=1232' % size, flush=True)
        else:
            print('[ORACLE091_WIRE_PASS] size=%d limit=1232' % size, flush=True)
'''

ANCHOR = "    print('[ORACLE077_NATIVE_RESULT] ok=%s reason=%s attempts=%d' % ("

def transform77(source):
    if MARK in source:
        return source
    if source.count(ANCHOR) != 1 or 'def compile_native(' not in source:
        raise RuntimeError('ORACLE091_V77_ANCHOR_UNRECOGNIZED')
    out = source.replace(ANCHOR, GUARD + ANCHOR, 1)
    ast.parse(out)
    return out

def transform80(source):
    if 'MAX_V1 = 1232' in source:
        return source
    if source.count('MAX_V1 = 4096') != 1:
        raise RuntimeError('ORACLE091_V80_WIRE_LIMIT_UNRECOGNIZED')
    out = source.replace('MAX_V1 = 4096', 'MAX_V1 = 1232', 1)
    ast.parse(out)
    return out

def test():
    fixture = """def compile_native(user, route, core, q87, root, extra_alt=None):
    result = {'ok': True, 'reason': 'LEGAL_UNSIGNED_V1', 'raw': bytes(1372), 'bytes': 1372, 'attempts': []}
    print('[ORACLE077_NATIVE_RESULT] ok=%s reason=%s attempts=%d' % (
        bool(result.get('ok')), result.get('reason'), len(result.get('attempts') or [])))
    return result
"""
    adjusted = transform77(fixture)
    ns = {}
    exec(compile(adjusted, '<fixture>', 'exec'), ns)
    over = ns['compile_native'](None, None, None, None, None)
    assert not over['ok'] and over['rejected_wire_bytes'] == 1372
    assert 'raw' not in over and 'msg' not in over
    adjusted = adjusted.replace('bytes(1372)', 'bytes(1217)').replace(
        "'bytes': 1372", "'bytes': 1217")
    ns = {}
    exec(compile(adjusted, '<fixture>', 'exec'), ns)
    legal = ns['compile_native'](None, None, None, None, None)
    assert legal['ok'] and legal['bytes'] == 1217
    assert transform80('MAX_V1 = 4096\n').strip() == 'MAX_V1 = 1232'
    assert transform77(adjusted) == adjusted
    for p in (V77, V80):
        if not p.is_file():
            raise RuntimeError('ORACLE091_DEPENDENCY_MISSING:' + str(p))
        ast.parse(p.read_text(encoding='utf-8'))
    print('[PASS] ORACLE091_FINAL_WIRE_REJECTION_AND_VALID_V0_TESTS')
    print('[BOUNDARY] NO_RPC NO_KEYS NO_SIGNING NO_BROADCAST NO_SCANNER_EDIT')

def install():
    test()
    before = {p: p.read_text(encoding='utf-8') for p in (V77, V80)}
    revised = {V77: transform77(before[V77]), V80: transform80(before[V80])}
    if all(before[p] == revised[p] for p in revised):
        print('[PASS] ORACLE091_ALREADY_INSTALLED')
        return
    backups = {
        p: p.with_name(p.stem + '.before_oracle091.py')
        for p in revised
    }
    for p, source in revised.items():
        ast.parse(source)
    for p, backup in backups.items():
        if before[p] != revised[p] and backup.exists():
            raise RuntimeError('ORACLE091_BACKUP_ALREADY_EXISTS:' + str(backup))
    changed = []
    try:
        for p in revised:
            if before[p] == revised[p]:
                continue
            shutil.copy2(p, backups[p])
            temp = p.with_suffix('.oracle091.tmp')
            temp.write_text(revised[p], encoding='utf-8')
            temp.replace(p)
            changed.append(p)
        test()
    except Exception:
        for p in changed:
            p.write_text(before[p], encoding='utf-8')
        print('[ROLLBACK] ORACLE091_RESTORED_SOURCE_FILES')
        raise
    print('[PASS] ORACLE091_FINAL_WIRE_TRUTH_INSTALLED')
    print('[HOLD] NO_LIVE_ATOMIC_SIMULATION_CERTIFIED')
    print('[NEXT] Forward v0 1343 bytes with zero verified ALT coverage requires ALT/account compression work')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    test() if args.test else install()
