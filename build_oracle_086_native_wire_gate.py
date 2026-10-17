"""ORACLE-086 complete installer: canonical serialized-wire limit gate.
No RPC, key access, signing, broadcast, or scanner edits.
"""
from pathlib import Path
import argparse
import ast
import shutil

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle_077_native_executor.py')
MARK = '# ORACLE086_NATIVE_WIRE_LIMIT_GATE'
OLD = "assert len(bytes(result.get('raw') or b'')) <= (4096 if result.get('version') == 1 else 1232)"
NEW = '''# ORACLE086_NATIVE_WIRE_LIMIT_GATE
        wire = result.get('raw')
        if not isinstance(wire, (bytes, bytearray)):
            raise RuntimeError('ORACLE086_SERIALIZED_WIRE_MISSING')
        if len(wire) > 1232:
            raise RuntimeError('ORACLE086_SERIALIZED_WIRE_TOO_LARGE:%d' % len(wire))'''


def check_wire(wire):
    if not isinstance(wire, (bytes, bytearray)):
        raise RuntimeError('ORACLE086_SERIALIZED_WIRE_MISSING')
    if len(wire) > 1232:
        raise RuntimeError('ORACLE086_SERIALIZED_WIRE_TOO_LARGE:%d' % len(wire))
    return True


def tests():
    for size in (0, 1207, 1232):
        assert check_wire(bytes(size))
    for size in (1233, 1372, 4096):
        try:
            check_wire(bytes(size))
        except RuntimeError as exc:
            assert 'TOO_LARGE' in str(exc)
        else:
            raise AssertionError('Oversized wire accepted: %s' % size)
    try:
        check_wire(None)
    except RuntimeError as exc:
        assert 'MISSING' in str(exc)
    else:
        raise AssertionError('Missing wire accepted')
    assert TARGET.is_file(), 'Canonical executor missing'
    source = TARGET.read_text(encoding='utf-8')
    assert 'def compile_native(' in source
    assert 'def simulate_native(' in source
    if MARK not in source:
        assert source.count(OLD) == 1, 'Existing size gate differs; no modifications made'
    else:
        assert source.count(MARK) == 1
    ast.parse(source)
    print('[PASS] ORACLE086_WIRE_BOUNDARY_TESTS')
    print('[PASS] ORACLE086_CANONICAL_EXECUTOR_CONTRACT')
    print('[BOUNDARY] NO_RPC NO_PRIVATE_KEY NO_SIGNING NO_BROADCAST')


def install():
    tests()
    source = TARGET.read_text(encoding='utf-8')
    if MARK in source:
        print('[PASS] ORACLE086_ALREADY_INSTALLED')
        return
    revised = source.replace(OLD, NEW, 1)
    ast.parse(revised)
    backup = TARGET.with_name(TARGET.stem + '.before_oracle086.py')
    if backup.exists():
        raise RuntimeError('ORACLE086_BACKUP_EXISTS_REFUSING_OVERWRITE')
    shutil.copy2(TARGET, backup)
    tmp = TARGET.with_suffix('.oracle086.tmp')
    tmp.write_text(revised, encoding='utf-8')
    tmp.replace(TARGET)
    print('[PASS] ORACLE086_NATIVE_WIRE_LIMIT_INSTALLED')
    print('[BACKUP]', backup)
    print('[TARGET]', TARGET)
    print('[HOLD] PumpSwap funding still requires repair; live execution not authorized')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    tests() if args.test else install()
