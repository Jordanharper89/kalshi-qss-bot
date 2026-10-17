
"""ORACLE179 complete installer: replace ORACLE177 normalized simulation verdict contract."""
import argparse
import ast
import os
import tempfile
from pathlib import Path

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
START = '# ORACLE177_SIGNED_SIM_TRUTH'
STOP = '# ORACLE178_NET_ECONOMICS_BOUNDARY'
NEW_MARK = '# ORACLE179_NORMALIZED_SIM_VERDICT'

REPLACEMENT = '''# ORACLE177_SIGNED_SIM_TRUTH
# ORACLE179_NORMALIZED_SIM_VERDICT
_ORACLE177_PREVIOUS_SIM=simulate_current

def simulate_current(compiled,user):
    import json as _json
    from pathlib import Path as _Path
    if not isinstance(compiled,dict) or compiled.get('oracle176_packet_verified') is not True:
        raise RuntimeError('ORACLE179_PACKET_NOT_CERTIFIED')
    digest=compiled.get('oracle176_packet_hash')
    if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest.lower()):
        raise RuntimeError('ORACLE179_PACKET_DIGEST_INVALID')
    if compiled.get('oracle162_signature_verified') is not True:
        raise RuntimeError('ORACLE179_SIGNATURE_UNVERIFIED')
    result=_ORACLE177_PREVIOUS_SIM(compiled,user)
    if not isinstance(result,dict):
        raise RuntimeError('ORACLE179_SIM_RESPONSE_NOT_MAPPING')
    # Canonical simulate_current() returns normalized {err, units, logs, accounts, context}.
    sentinel=object()
    error=result.get('err',sentinel)
    units=result.get('units',sentinel)
    success=(error is None and type(units) is int and units>=0)
    if error is sentinel:
        reason='MISSING_SIM_ERROR_FIELD'
    elif error is not None:
        reason='SIM_TRANSACTION_ERROR'
    elif type(units) is not int or units<0:
        reason='MISSING_OR_INVALID_COMPUTE_UNITS'
    else:
        reason='SIGNED_SIM_PASS'
    error_short=(repr(error)[:180] if error is not sentinel and error is not None else None)
    row={'build':'ORACLE179','message_sha256':digest,'signed_sim_success':success,
         'reason':reason,'units_consumed':units if type(units) is int else None,
         'simulation_error':error_short,'broadcast':False,'execution_authorized':False}
    dest=_Path('runtime_state/oracle/oracle_live_execution/ORACLE179_SIM_VERDICTS.jsonl')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('a',encoding='utf-8') as handle:
        handle.write(_json.dumps(row,sort_keys=True)+'\\n')
    print('[ORACLE179_SIM_%s] reason=%s units=%s err=%s digest=%s broadcast=FALSE' %
          ('PASS' if success else 'HOLD',reason,
           str(units) if type(units) is int else 'MISSING',
           error_short or 'NONE',digest[:16]),flush=True)
    out=dict(result)
    out['oracle177_signed_sim_pass']=success
    out['oracle177_message_sha256']=digest
    out['oracle177_sim_units']=units if type(units) is int else None
    out['oracle179_sim_reason']=reason
    return out
'''
def transform(source):
    if source.count(NEW_MARK) == 1:
        ast.parse(source)
        return source, False
    if NEW_MARK in source:
        raise RuntimeError('HOLD_ORACLE179_DUPLICATE_MARKER')
    if source.count(START) != 1 or source.count(STOP) != 1:
        raise RuntimeError('HOLD_ORACLE179_SIM_BOUNDARIES_NOT_UNIQUE')
    a, b = source.index(START), source.index(STOP)
    if a >= b:
        raise RuntimeError('HOLD_ORACLE179_BOUNDARY_ORDER')
    old = source[a:b]
    for required in ('_ORACLE177_PREVIOUS_SIM=simulate_current',
                     "units=result.get('unitsConsumed')", "result.get('err','MISSING_ERR')",
                     'oracle177_signed_sim_pass'):
        if required not in old:
            raise RuntimeError('HOLD_ORACLE179_UNRECOGNIZED_177_CONTRACT')
    for required in ('# ORACLE176_COMPILED_V0_IDENTITY',
                     'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED'):
        if required not in source:
            raise RuntimeError('HOLD_ORACLE179_MISSING_PROTECTION')
    updated = source[:a] + REPLACEMENT + '\n' + source[b:]
    ast.parse(updated)
    return updated, True
def test():
    ast.parse(REPLACEMENT)
    old = """# ORACLE177_SIGNED_SIM_TRUTH
_ORACLE177_PREVIOUS_SIM=simulate_current

def simulate_current(compiled,user):
    result=_ORACLE177_PREVIOUS_SIM(compiled,user)
    err=result.get('err','MISSING_ERR')
    units=result.get('unitsConsumed')
    result['oracle177_signed_sim_pass']=(err is None and type(units) is int)
    return result
"""
    fixture = ('ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED\n'
               '# ORACLE176_COMPILED_V0_IDENTITY\n'+old+STOP+'\n')
    updated, changed = transform(fixture)
    assert changed and not transform(updated)[1]
    assert "result.get('units',sentinel)" in updated
    with tempfile.TemporaryDirectory() as td:
        oldcwd=os.getcwd()
        try:
            os.chdir(td)
            state={'v':{'err':None,'units':230000}}
            env={'simulate_current':lambda c,u:dict(state['v'])}
            exec(REPLACEMENT,env)
            packet={'oracle176_packet_verified':True,'oracle176_packet_hash':'a'*64,
                    'oracle162_signature_verified':True}
            assert env['simulate_current'](packet,'user')['oracle177_signed_sim_pass']
            for bad in ({'err':{'InstructionError':[3,{'Custom':3005}]},'units':110000},
                        {'err':None,'unitsConsumed':230000},{'err':None}):
                state['v']=bad
                assert not env['simulate_current'](packet,'user')['oracle177_signed_sim_pass']
        finally:os.chdir(oldcwd)
    print('[TEST PASS] ORACLE179 normalized units, explicit error, packet binding, fail-closed')
def install():
    if not TARGET.is_file():
        raise RuntimeError('HOLD_ORACLE179_RUNTIME_MISSING')
    original = TARGET.read_text(encoding='utf-8')
    updated, changed = transform(original)
    if not changed:
        print('[INSTALL PASS] ORACLE179 already installed')
        return
    backup = TARGET.with_name('runtime.before_oracle179.py')
    if backup.exists() and backup.read_text(encoding='utf-8') != original:
        raise RuntimeError('HOLD_ORACLE179_BACKUP_COLLISION')
    if not backup.exists():
        backup.write_text(original, encoding='utf-8')
    pending = TARGET.with_name('runtime.oracle179.pending')
    if pending.exists():
        raise RuntimeError('HOLD_ORACLE179_PENDING_COLLISION')
    try:
        pending.write_text(updated, encoding='utf-8')
        ast.parse(pending.read_text(encoding='utf-8'))
        os.replace(pending, TARGET)
    finally:
        if pending.exists(): pending.unlink()
    print('[INSTALL PASS] ORACLE179 normalized simulation verdict; scanner untouched; broadcast blocked')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true')
    args = parser.parse_args()
    test() if args.test else install()
