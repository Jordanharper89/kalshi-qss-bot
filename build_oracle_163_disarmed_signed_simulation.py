
"""ORACLE-163 complete installer: disarmed signed simulation, no trade send.
Windows CMD: python build_oracle_163_disarmed_signed_simulation.py --test
             python build_oracle_163_disarmed_signed_simulation.py
"""
from __future__ import annotations
import argparse
import ast
import json
import re
from pathlib import Path

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
PROOF = Path('runtime_state/oracle/oracle_live_execution/ORACLE163_DISARMED_SIMULATION.json')
START = '    if not _live_010_armed():\n'
END = '    with LIVE_010_LOCK:\n'
MARKER = '# ORACLE163_DISARMED_SIMULATION_BOUNDARY\n'
BRANCH = '''    if not _live_010_armed():
        # ORACLE163_DISARMED_SIMULATION_BOUNDARY
        # Deliberately simulate only. Never fall through to the armed send block.
        if compiled.get('oracle162_signature_verified') is not True:
            print('[ORACLE163_SIM_HOLD] reason=UNVERIFIED_SIGNATURE', flush=True)
            return
        _raw163 = compiled.get('raw')
        if not isinstance(_raw163, (bytes, bytearray)) or not 100 <= len(_raw163) <= 1232:
            print('[ORACLE163_SIM_HOLD] reason=INVALID_PACKET_SIZE', flush=True)
            return
        if int(compiled.get('bytes', -1)) != len(_raw163):
            print('[ORACLE163_SIM_HOLD] reason=SIZE_FIELD_MISMATCH', flush=True)
            return
        print('[ORACLE163_SIM_ENTER] direction=%s bytes=%d broadcast=FALSE' %
              (str(direction), len(_raw163)), flush=True)
        try:
            _result163 = simulate_current(compiled, USER)
            if not isinstance(_result163, dict):
                print('[ORACLE163_SIM_HOLD] reason=NON_MAPPING_SIM_RESPONSE', flush=True)
                return
            _error163 = _result163.get('err')
            _units163 = _result163.get('unitsConsumed')
            if _error163 is None:
                print('[ORACLE163_SIM_RPC_PASS] units=%s broadcast=FALSE' %
                      str(_units163), flush=True)
            else:
                print('[ORACLE163_SIM_RPC_HOLD] error_type=%s units=%s broadcast=FALSE' %
                      (type(_error163).__name__, str(_units163)), flush=True)
        except Exception as _exc163:
            print('[ORACLE163_SIM_RPC_HOLD] exception=%s broadcast=FALSE' %
                  type(_exc163).__name__, flush=True)
        return
'''

def transform(source):
    if MARKER.strip() in source:
        if source.count(MARKER.strip()) != 1 or source.count(END) < 1:
            raise RuntimeError('HOLD_ORACLE163_ALREADY_INSTALLED_BUT_INVALID')
        return source
    if source.count(START) != 1:
        raise RuntimeError('HOLD_ORACLE163_DISARMED_BRANCH_NOT_UNIQUE')
    begin = source.index(START)
    end = source.find(END, begin)
    if end < 0 or end - begin > 1500:
        raise RuntimeError('HOLD_ORACLE163_SEND_BOUNDARY_NOT_FOUND')
    original = source[begin:end]
    if 'LIVE_010_READY_NOT_ARMED' not in original or not re.search(r'(?m)^        return\s*$', original):
        raise RuntimeError('HOLD_ORACLE163_UNEXPECTED_DISARMED_BRANCH')
    for required in ('ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED',
                     'CANARY_TRADE_LAMPORTS=50_000_000',
                     '_oracle162_verify_and_sign',
                     'def simulate_current('):
        if required not in source:
            raise RuntimeError('HOLD_ORACLE163_MISSING_GUARD_' + required[:35])
    result = source[:begin] + BRANCH + source[end:]
    ast.parse(result)
    return result

def test():
    branch = '''from __future__ import annotations
CANARY_TRADE_LAMPORTS=50_000_000
ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED=True
_oracle162_verify_and_sign=True
def simulate_current(compiled,user):
    return {'err': None, 'unitsConsumed': 123}
def _live_010_armed():
    return False
def boundary(compiled, USER, direction):
    if not _live_010_armed():
        print('[LIVE_010_READY_NOT_ARMED]')
        return
    with LIVE_010_LOCK:
        raise RuntimeError('must never send')
'''
    changed = transform(branch)
    assert transform(changed) == changed
    assert changed.count(MARKER.strip()) == 1
    assert 'simulate_current(compiled, USER)' in changed
    assert changed.index('        return\n    with LIVE_010_LOCK:') > changed.index(MARKER.strip())
    assert 'sendTransaction' not in BRANCH
    try:
        transform(branch.replace('LIVE_010_READY_NOT_ARMED', 'UNKNOWN_BRANCH'))
        raise AssertionError('missing fail-closed guard')
    except RuntimeError as exc:
        assert 'HOLD_ORACLE163' in str(exc)
    print('[TEST PASS] ORACLE163 disarmed signed simulation, idempotency, fail-closed guards')

def install():
    if not TARGET.is_file():
        raise RuntimeError('HOLD_ORACLE163_RUNTIME_NOT_FOUND')
    original = TARGET.read_text(encoding='utf-8')
    changed = transform(original)
    if changed == original:
        print('[INSTALL PASS] ORACLE163 already installed')
        return
    backup = TARGET.with_name('runtime.before_oracle163.py')
    if backup.exists() and backup.read_text(encoding='utf-8') != original:
        raise RuntimeError('HOLD_ORACLE163_BACKUP_ALREADY_EXISTS_DIFFERENT_CONTENT')
    if not backup.exists():
        backup.write_text(original, encoding='utf-8')
    TARGET.write_text(changed, encoding='utf-8')
    if TARGET.read_text(encoding='utf-8') != changed:
        raise RuntimeError('HOLD_ORACLE163_WRITE_VERIFICATION_FAILED')
    PROOF.parent.mkdir(parents=True, exist_ok=True)
    PROOF.write_text(json.dumps({'build':'ORACLE-163','mode':'DISARMED_SIMULATION_ONLY',
        'size_sol':'0.050','broadcast':False,'signature_required':True,
        'runtime':str(TARGET),'backup':str(backup)},indent=2),encoding='utf-8')
    print('[INSTALL PASS] ORACLE163 disarmed signed simulation boundary')
    print('[PROOF]', PROOF)
    print('[GUARD] scanner unchanged; armed send branch unchanged; broadcast disabled via secure launcher')

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--test',action='store_true')
    args=parser.parse_args()
    test() if args.test else install()
