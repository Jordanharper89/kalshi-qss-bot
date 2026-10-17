"""ORACLE-161 complete installer: 0.050 SOL native compile contract and evidence.
Windows CMD / venv. No credentials, signing, network calls or broadcast in installer.
"""
from __future__ import annotations
import argparse, ast, json, re
from pathlib import Path

ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
RUNTIME=ROOT/'runtime.py'
COMPILER=ROOT/'oracle105_sdk_worker/oracle149_atomic_alt_compiler.py'
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE161_NATIVE_COMPILE_CONTRACT.json')
BEGIN='# ORACLE161_COMPILE_CONTRACT_BEGIN'
END='# ORACLE161_COMPILE_CONTRACT_END'
AMOUNT=50_000_000

REPLACEMENT='''# ORACLE161_COMPILE_CONTRACT_BEGIN
def compile_current(user,route):
    # Fail closed before the native ALT compiler or any simulation call.
    from qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker import oracle149_atomic_alt_compiler as _o149
    if not isinstance(route,dict):
        raise RuntimeError('ORACLE161_ROUTE_NOT_DICT')
    start=route.get('start_lamports')
    if type(start) is not int or start != CANARY_TRADE_LAMPORTS or start != 50_000_000:
        raise RuntimeError('ORACLE161_NATIVE_AMOUNT_MISMATCH')
    candidates=route.get('original_candidates')
    if not isinstance(candidates,(tuple,list)) or not candidates:
        raise RuntimeError('ORACLE161_NO_NATIVE_CANDIDATES')
    # A valid source route must contain genuine candidate instruction lists;
    # never synthesize a profitable quote or omit a required swap leg.
    for candidate in candidates:
        if not isinstance(candidate,(tuple,list)) or len(candidate)<2 or not isinstance(candidate[1],(tuple,list)) or len(candidate[1])<2:
            raise RuntimeError('ORACLE161_INVALID_NATIVE_CANDIDATE')
    print('[ORACLE161_COMPILE_ENTER] amount_lamports=50000000 candidates=%d' % len(candidates),flush=True)
    try:
        built=_o149.compile_route(user,route,BLOCKHASH.get())
    except Exception as exc:
        print('[ORACLE161_COMPILE_EXCEPTION] type=%s' % type(exc).__name__,flush=True)
        raise
    if not isinstance(built,dict):
        raise RuntimeError('ORACLE161_BAD_COMPILER_RESULT')
    if not built.get('ok'):
        print('[ORACLE161_COMPILE_HOLD] reason=%s' % str(built.get('reason','UNKNOWN'))[:140],flush=True)
        return built
    raw=built.get('raw')
    if not isinstance(raw,(bytes,bytearray)):
        raise RuntimeError('ORACLE161_NO_SERIALIZED_PACKET')
    size=len(raw)
    if size>1232 or size<100:
        raise RuntimeError('ORACLE161_SERIALIZED_PACKET_INVALID_SIZE')
    print('[ORACLE161_NATIVE_PACKET] bytes=%d amount_lamports=50000000 broadcast=FALSE' % size,flush=True)
    return built
# ORACLE161_COMPILE_CONTRACT_END

'''

def transform(source):
    if BEGIN in source:
        if source.count(BEGIN)!=1 or source.count(END)!=1:
            raise RuntimeError('HOLD_ORACLE161_MARKER_CORRUPT')
        return source
    anchor=re.search(r'(?m)^def compile_current\(user,route\):\n',source)
    finish=re.search(r'(?m)^def simulate_current\(',source)
    if not anchor or not finish or finish.start()<=anchor.start():
        raise RuntimeError('HOLD_ORACLE161_COMPILER_BOUNDARY_CHANGED')
    old=source[anchor.start():finish.start()]
    if old.strip()!='def compile_current(user,route):\n    from qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker import oracle149_atomic_alt_compiler as _o149\n    return _o149.compile_route(user,route,BLOCKHASH.get())':
        raise RuntimeError('HOLD_ORACLE161_UNEXPECTED_COMPILER_BODY')
    updated=source[:anchor.start()]+REPLACEMENT+source[finish.start():]
    ast.parse(updated)
    return updated

def test():
    sample=('CANARY_TRADE_LAMPORTS=50_000_000\n'
        'def compile_current(user,route):\n'
        '    from qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker import oracle149_atomic_alt_compiler as _o149\n'
        '    return _o149.compile_route(user,route,BLOCKHASH.get())\n\n'
        'def simulate_current(built,user):\n    return None\n')
    converted=transform(sample)
    assert transform(converted)==converted
    assert 'ORACLE161_NATIVE_AMOUNT_MISMATCH' in converted
    assert 'ORACLE161_NATIVE_PACKET' in converted
    assert converted.count('def compile_current(')==1
    for invalid in (sample.replace('return _o149.compile_route(user,route,BLOCKHASH.get())','return None'),
                    sample.replace('def simulate_current','def old_simulate')):
        try: transform(invalid)
        except RuntimeError: pass
        else: raise AssertionError('unrecognized compile boundary accepted')
    print('[TEST PASS] ORACLE161 native amount guard, measured signed packet, fail-closed compiler holds')

def install():
    src=RUNTIME.read_text(encoding='utf-8')
    compiler=COMPILER.read_text(encoding='utf-8')
    if 'def compile_route(user,route,blockhash):' not in compiler:
        raise RuntimeError('HOLD_ORACLE149_COMPILER_INTERFACE_CHANGED')
    prerequisites=('CANARY_TRADE_SOL=0.050','CANARY_TRADE_LAMPORTS=50_000_000',
                   'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED',
                   'ORACLE158_VERIFIED_ALT_PRELOAD_BEGIN',
                   'ORACLE159_EXECUTION_BOUNDARY_BEGIN',
                   'ORACLE160_EXACT_AMOUNT_CONTRACT')
    missing=[p for p in prerequisites if p not in src]
    if missing: raise RuntimeError('HOLD_ORACLE161_PREREQUISITES_MISSING: '+','.join(missing))
    updated=transform(src)
    if updated==src:
        print('[INSTALL PASS] ORACLE161 already installed');return
    backup=RUNTIME.with_suffix('.pre_oracle161.bak')
    if backup.exists(): raise RuntimeError('HOLD_ORACLE161_BACKUP_ALREADY_EXISTS')
    backup.write_text(src,encoding='utf-8')
    try:
        RUNTIME.write_text(updated,encoding='utf-8')
        ast.parse(RUNTIME.read_text(encoding='utf-8'))
    except Exception:
        RUNTIME.write_text(src,encoding='utf-8')
        raise
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps({'build':'ORACLE161','amount_sol':0.05,
        'native_lamports':AMOUNT,'max_serialized_bytes':1232,
        'signed_simulation_proven':False,'broadcast_authorized':False,
        'native_compiler':'oracle149_atomic_alt_compiler.compile_route',
        'scanner_modified':False},indent=2)+'\n',encoding='utf-8')
    print('[INSTALL PASS] ORACLE161 native compiler contract')
    print('[PROOF]',REPORT)
    print('[SCOPE] no credentials, signing, RPC or broadcast from installer; simulation-only launcher required')

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');a=p.parse_args()
    test() if a.test else install()
if __name__=='__main__': main()
