"""ORACLE159 full installer: persistent read-only native execution boundary telemetry.
Windows CMD, venv active: python build_oracle_159_execution_boundary_proof.py --test
then python build_oracle_159_execution_boundary_proof.py
"""
import argparse
import ast
import json
import py_compile
import re
from pathlib import Path

RUNTIME=Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
LAUNCHER=Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle156_secure_native_sim_launcher.py')
BEGIN='# ORACLE159_EXECUTION_BOUNDARY_BEGIN'
END='# ORACLE159_EXECUTION_BOUNDARY_END'
TRACE=r'''# ORACLE159_EXECUTION_BOUNDARY_BEGIN
# Nonsecret stage counters and event evidence; no wallet, raw tx, or RPC parameters.
_ORACLE159_REPORT = Path('runtime_state/oracle/oracle_live_execution/ORACLE159_EXECUTION_BOUNDARY.jsonl')
_ORACLE159_COUNTS = {'attack_entry':0,'refresh_accept':0,'refresh_hold':0,
    'compile_entry':0,'compile_pass':0,'compile_hold':0,
    'sim_entry':0,'sim_success':0,'sim_error':0}

def _oracle159_record(stage, **fields):
    import json as _json
    import time as _time
    if stage in _ORACLE159_COUNTS:
        _ORACLE159_COUNTS[stage]+=1
    row={'stage':stage,'monotonic_ns':_time.monotonic_ns(),
         'counts':dict(_ORACLE159_COUNTS)}
    row.update(fields)
    try:
        _ORACLE159_REPORT.parent.mkdir(parents=True,exist_ok=True)
        with _ORACLE159_REPORT.open('a',encoding='utf-8') as f:
            f.write(_json.dumps(row,sort_keys=True)+'\n')
    except OSError:
        print('[ORACLE159_REPORT_WRITE_HOLD]',flush=True)
    if stage in ('attack_entry','refresh_accept','refresh_hold','compile_pass','compile_hold','sim_success','sim_error'):
        print('[ORACLE159_BOUNDARY] stage=%s counts=%s' %
              (stage,_ORACLE159_COUNTS),flush=True)

_ORACLE159_ORIGINAL_ATTACK=fast_live_attack
_ORACLE159_ORIGINAL_REFRESH=_fast_010_refresh_latest
_ORACLE159_ORIGINAL_COMPILE=compile_current
_ORACLE159_ORIGINAL_SIM=simulate_current

def fast_live_attack(lane,token,snap,opportunity,slot,received_ns,generation):
    _oracle159_record('attack_entry',direction=str(opportunity.get('direction','UNKNOWN')),
                      size_lamports=int(opportunity.get('start',0)),slot=int(slot))
    return _ORACLE159_ORIGINAL_ATTACK(lane,token,snap,opportunity,slot,received_ns,generation)

def _fast_010_refresh_latest(*args,**kwargs):
    result=_ORACLE159_ORIGINAL_REFRESH(*args,**kwargs)
    if result is None:
        _oracle159_record('refresh_hold')
    else:
        opp=result[1]
        _oracle159_record('refresh_accept',direction=str(opp.get('direction','UNKNOWN')),
                          start_lamports=int(opp.get('start',0)),
                          net_lamports=int(opp.get('local_net',0)))
    return result

def compile_current(user,route):
    _oracle159_record('compile_entry',direction=str(route.get('direction','UNKNOWN')))
    try:
        result=_ORACLE159_ORIGINAL_COMPILE(user,route)
        if not isinstance(result,dict) or not result.get('ok'):
            _oracle159_record('compile_hold',reason=str(result.get('reason','UNKNOWN'))[:100]
                if isinstance(result,dict) else 'NON_DICTIONARY_RESULT')
        else:
            _oracle159_record('compile_pass',tx_bytes=len(result.get('raw') or b''),
                              within_1232=(len(result.get('raw') or b'')<=1232))
        return result
    except Exception as exc:
        _oracle159_record('compile_hold',reason=type(exc).__name__)
        raise

def simulate_current(compiled,user):
    _oracle159_record('sim_entry',tx_bytes=len(compiled.get('raw') or b''))
    try:
        result=_ORACLE159_ORIGINAL_SIM(compiled,user)
        if isinstance(result,dict) and result.get('err') is None:
            _oracle159_record('sim_success')
        else:
            _oracle159_record('sim_error',reason='RPC_SIMULATION_ERROR')
        return result
    except Exception as exc:
        _oracle159_record('sim_error',reason=type(exc).__name__)
        raise
# ORACLE159_EXECUTION_BOUNDARY_END

'''

def transform(source):
    if BEGIN in source or END in source:
        raise RuntimeError('HOLD_ORACLE159_ALREADY_INSTALLED')
    for name in ('fast_live_attack','_fast_010_refresh_latest','compile_current','simulate_current','run'):
        if len(re.findall(r'(?m)^def '+re.escape(name)+r'\s*\(',source))!=1:
            raise RuntimeError('HOLD_FUNCTION_ANCHOR_'+name)
    if 'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED' not in source:
        raise RuntimeError('HOLD_ORACLE158_DIRECT_SEND_GUARD_NOT_INSTALLED')
    if 'CANARY_TRADE_SOL=0.050' not in source:
        raise RuntimeError('HOLD_050_SOL_CONFIGURATION_NOT_INSTALLED')
    anchor=re.search(r'(?m)^def run\s*\(',source)
    updated=source[:anchor.start()]+TRACE+source[anchor.start():]
    ast.parse(updated)
    return updated

def safety_check(launcher):
    for token in ('ORACLE158_Q96_BROADCAST_PROHIBITED','block_broadcast(core)',
                  'runtime.run(float(seconds))'):
        if token not in launcher:
            raise RuntimeError('HOLD_LAUNCHER_GUARD_MISSING_'+token)

def test():
    fixture=('from pathlib import Path\nCANARY_TRADE_SOL=0.050\n'
             'def _live_010_send_once(raw):\n    raise RuntimeError("ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED")\n'
             'def fast_live_attack(lane,token,snap,opportunity,slot,received_ns,generation):\n    return 1\n'
             'def _fast_010_refresh_latest(*args,**kwargs):\n    return None\n'
             'def compile_current(user,route):\n    return {"ok":False,"reason":"SIZE_HOLD"}\n'
             'def simulate_current(compiled,user):\n    return {"err":None}\n'
             'def run(seconds=90):\n    return 0\n')
    updated=transform(fixture)
    assert updated.count(BEGIN)==1 and updated.count(END)==1
    assert updated.index(BEGIN)<updated.index('def run(')
    assert 'HOLD_ORACLE159_ALREADY_INSTALLED' in _expected_repeat(updated)
    ast.parse(updated)
    print('[TEST PASS] ORACLE159 stage trace insertion and fail-closed guards')

def _expected_repeat(s):
    try:transform(s)
    except RuntimeError as e:return str(e)
    raise AssertionError('Repeated install was allowed')

def install():
    if not RUNTIME.is_file() or not LAUNCHER.is_file():
        raise RuntimeError('HOLD_NATIVE_RUNTIME_OR_LAUNCHER_MISSING')
    orig=RUNTIME.read_text(encoding='utf-8')
    safety_check(LAUNCHER.read_text(encoding='utf-8'))
    updated=transform(orig)
    backup=RUNTIME.with_suffix('.pre_oracle159.bak')
    if backup.exists():raise RuntimeError('HOLD_ORACLE159_BACKUP_EXISTS')
    backup.write_text(orig,encoding='utf-8')
    try:
        RUNTIME.write_text(updated,encoding='utf-8')
        py_compile.compile(str(RUNTIME),doraise=True)
    except Exception:
        RUNTIME.write_text(orig,encoding='utf-8')
        raise
    print('[INSTALL PASS] ORACLE159 execution boundary telemetry')
    print('[PROOF] runtime_state\\oracle\\oracle_live_execution\\ORACLE159_EXECUTION_BOUNDARY.jsonl')
    print('[GUARD] existing ORACLE158 simulation-only transport unchanged')
    print('[SIZE] 0.050 SOL; no scanner changes, no transaction broadcast')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--test',action='store_true')
    options=parser.parse_args()
    test() if options.test else install()
