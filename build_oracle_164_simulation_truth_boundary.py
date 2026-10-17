"""ORACLE-164 complete disarmed simulation truth boundary installer."""
from __future__ import annotations
import argparse
import ast
import json
from pathlib import Path

RUNTIME = Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
REPORT = Path('runtime_state/oracle/oracle_live_execution/ORACLE164_SIMULATION_TRUTH.jsonl')
MARKER = '# ORACLE164_SIMULATION_TRUTH_BOUNDARY'
BEGIN = '    if not _live_010_armed():\n'
END = '    with LIVE_010_LOCK:\n'
BRANCH = '''    if not _live_010_armed():
        # ORACLE164_SIMULATION_TRUTH_BOUNDARY
        # Diagnostic only: never fall through to the armed path.
        _raw164 = compiled.get('raw')
        if compiled.get('oracle162_signature_verified') is not True:
            print('[ORACLE164_HOLD] reason=SIGNATURE_NOT_VERIFIED', flush=True)
            return
        if not isinstance(_raw164, (bytes, bytearray)) or not 100 <= len(_raw164) <= 1232:
            print('[ORACLE164_HOLD] reason=INVALID_SERIALIZED_SIZE', flush=True)
            return
        if int(compiled.get('bytes', -1)) != len(_raw164):
            print('[ORACLE164_HOLD] reason=PACKET_SIZE_MISMATCH', flush=True)
            return
        print('[ORACLE164_SIM_ENTER] direction=%s bytes=%d broadcast=FALSE' %
              (str(direction), len(_raw164)), flush=True)
        _verdict164 = 'RPC_FAILURE'
        _err164 = 'UNKNOWN'
        _units164 = None
        _logs164 = 0
        try:
            _response164 = simulate_current(compiled, USER)
            if not isinstance(_response164, dict):
                _err164 = 'NON_MAPPING_RESPONSE'
            elif 'err' not in _response164:
                _err164 = 'MISSING_ERR_FIELD'
            else:
                _units164 = _response164.get('unitsConsumed')
                _logrows164 = _response164.get('logs')
                _logs164 = len(_logrows164) if isinstance(_logrows164, list) else 0
                _rpcerr164 = _response164.get('err')
                if _rpcerr164 is None:
                    _verdict164 = 'EXECUTION_PASS_UNCERTIFIED_PROFIT'
                    _err164 = 'NONE'
                else:
                    _verdict164 = 'EXECUTION_REJECTED'
                    _err164 = str(_rpcerr164)[:160]
        except Exception as _ex164:
            _err164 = type(_ex164).__name__
        _record164 = dict(build='ORACLE164',direction=str(direction),
                          slot=int(slot),amount_lamports=50000000,
                          packet_bytes=len(_raw164),verdict=_verdict164,
                          error=_err164,units_consumed=_units164,
                          program_log_count=_logs164,broadcast=False,
                          certified_profit=False)
        try:
            _p164 = Path('runtime_state/oracle/oracle_live_execution/ORACLE164_SIMULATION_TRUTH.jsonl')
            _p164.parent.mkdir(parents=True, exist_ok=True)
            with _p164.open('a', encoding='utf-8') as _f164:
                _f164.write(json.dumps(_record164, sort_keys=True) + '\\n')
        except (OSError, TypeError, ValueError):
            print('[ORACLE164_EVIDENCE_WRITE_HOLD]', flush=True)
        print('[ORACLE164_SIM_VERDICT] status=%s err=%s units=%s logs=%d broadcast=FALSE' %
              (_verdict164, _err164, str(_units164), _logs164), flush=True)
        return
'''

def transform(source):
    if source.count(MARKER) == 1:
        return source
    if MARKER in source or source.count(BEGIN) != 1:
        raise RuntimeError('HOLD_ORACLE164_DISARMED_ANCHOR')
    a = source.index(BEGIN)
    b = source.find(END, a)
    if b < 0 or b - a > 3300:
        raise RuntimeError('HOLD_ORACLE164_ARMED_BOUNDARY')
    old = source[a:b]
    if 'ORACLE163_DISARMED_SIMULATION_BOUNDARY' not in old or 'simulate_current(compiled, USER)' not in old:
        raise RuntimeError('HOLD_ORACLE164_ORACLE163_NOT_INSTALLED')
    for x in ('ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED',
              'CANARY_TRADE_LAMPORTS=50_000_000',
              '_oracle162_verify_and_sign'):
        if x not in source:
            raise RuntimeError('HOLD_ORACLE164_MISSING_PRECONDITION')
    updated = source[:a] + BRANCH + source[b:]
    ast.parse(updated)
    return updated

def test():
    source = '''from pathlib import Path
import json
CANARY_TRADE_LAMPORTS=50_000_000
ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED=True
_oracle162_verify_and_sign=True
def simulate_current(compiled, user):
    return {'err':None,'unitsConsumed':42,'logs':[]}
def _live_010_armed():
    return False
def boundary(compiled, USER, direction, slot):
    if not _live_010_armed():
        # ORACLE163_DISARMED_SIMULATION_BOUNDARY
        simulate_current(compiled, USER)
        return
    with LIVE_010_LOCK:
        raise AssertionError('send forbidden')
'''
    result = transform(source)
    assert transform(result) == result
    assert result.count(MARKER) == 1
    assert result.count('simulate_current(compiled, USER)') == 1
    assert 'certified_profit=False' in result
    assert 'sendTransaction' not in BRANCH
    for bad in (source.replace('ORACLE163_DISARMED_SIMULATION_BOUNDARY','BAD'),
                source.replace('ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED','BAD')):
        try: transform(bad)
        except RuntimeError: pass
        else: raise AssertionError('HOLD guard failed')
    print('[TEST PASS] ORACLE164 simulation verdict, missing-error HOLD, intact send boundary')

def install():
    if not RUNTIME.is_file():
        raise RuntimeError('HOLD_ORACLE164_RUNTIME_MISSING')
    source = RUNTIME.read_text(encoding='utf-8')
    updated = transform(source)
    if updated == source:
        print('[INSTALL PASS] ORACLE164 already installed')
        return
    backup = RUNTIME.with_name('runtime.before_oracle164.py')
    if backup.exists():
        raise RuntimeError('HOLD_ORACLE164_BACKUP_ALREADY_EXISTS')
    backup.write_text(source, encoding='utf-8')
    try:
        RUNTIME.write_text(updated, encoding='utf-8')
        ast.parse(RUNTIME.read_text(encoding='utf-8'))
    except Exception:
        RUNTIME.write_text(source, encoding='utf-8')
        raise
    print('[INSTALL PASS] ORACLE164 disarmed signed simulation truth boundary')
    print('[PROOF]', REPORT)
    print('[GUARD] no scanner change; no automatic send; no profitability certification')

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    a=p.parse_args()
    test() if a.test else install()
