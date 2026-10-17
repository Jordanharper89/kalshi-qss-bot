"""ORACLE-158 complete, fail-closed native ALT preload + simulation-only installer.

Run from the repository root with venv active. Never writes credential values.
"""
from __future__ import annotations
import argparse
import ast
import json
import py_compile
import re
from pathlib import Path

RUNTIME = Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
LAUNCHER = Path('qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle156_secure_native_sim_launcher.py')
REGISTRY = Path('runtime_state/oracle/solana_atomic_executor/canonical_alt.json')
PROOF = Path('runtime_state/oracle/oracle_live_execution/ORACLE_151_CANONICAL_ALT_LIVE_PROOF.json')
ALT_PROGRAM = 'AddressLookupTab1e1111111111111111111111111'
START = '# ORACLE158_VERIFIED_ALT_PRELOAD_BEGIN'
END = '# ORACLE158_VERIFIED_ALT_PRELOAD_END'

INJECT = '''# ORACLE158_VERIFIED_ALT_PRELOAD_BEGIN
# Preload the canonical public on-chain ALT at startup, not per hot quote.
_ORACLE158_ORIGINAL_PRELOAD = preload_canary_saved_alts

def _oracle158_preload_canonical_alt():
    import base64 as _b64
    import json as _json
    from pathlib import Path as _Path
    _r = _Path('runtime_state/oracle/solana_atomic_executor/canonical_alt.json')
    _p = _Path('runtime_state/oracle/oracle_live_execution/ORACLE_151_CANONICAL_ALT_LIVE_PROOF.json')
    if not (_r.is_file() and _p.is_file()):
        raise RuntimeError('ORACLE158_CANONICAL_ALT_EVIDENCE_MISSING')
    reg = _json.loads(_r.read_text(encoding='utf-8'))
    proof = _json.loads(_p.read_text(encoding='utf-8'))
    key = reg.get('address')
    if not (isinstance(key,str) and proof.get('ok') is True
            and proof.get('active') is True and proof.get('address') == key):
        raise RuntimeError('ORACLE158_CANONICAL_ALT_PROOF_MISMATCH')
    resp = q87.c.rpc('getAccountInfo',[key,{'encoding':'base64','commitment':'confirmed'}])
    account = (resp or {}).get('value')
    if not isinstance(account,dict) or account.get('owner') != 'AddressLookupTab1e1111111111111111111111111':
        raise RuntimeError('ORACLE158_CANONICAL_ALT_OWNER_INVALID')
    data = account.get('data')
    if not isinstance(data,list) or not data:
        raise RuntimeError('ORACLE158_CANONICAL_ALT_DATA_MISSING')
    raw = _b64.b64decode(data[0],validate=True)
    if (len(raw) < 56 or (len(raw)-56)%32 or
            int.from_bytes(raw[:4],'little') != 1 or
            int.from_bytes(raw[4:12],'little') != (1<<64)-1):
        raise RuntimeError('ORACLE158_CANONICAL_ALT_INVALID_OR_INACTIVE')
    entries = [raw[j:j+32] for j in range(56,len(raw),32)]
    if not entries or len(entries)>256:
        raise RuntimeError('ORACLE158_CANONICAL_ALT_ENTRY_COUNT_INVALID')
    mapping=globals().get('PRELOADED_ALT_TABLES')
    if not isinstance(mapping,dict):
        raise RuntimeError('ORACLE158_PRELOADED_ALT_CACHE_ABSENT')
    mapping[key]=entries
    print('[ORACLE158_VERIFIED_ALT_PRELOADED] entries=%d key=%s' % (len(entries),key),flush=True)

def preload_canary_saved_alts(root):
    result = _ORACLE158_ORIGINAL_PRELOAD(root)
    _oracle158_preload_canonical_alt()
    return result
# ORACLE158_VERIFIED_ALT_PRELOAD_END

'''

# Deliberately replace the *whole* direct send function, not merely its print label.
SEND_BLOCK = '''def _live_010_send_once(raw):
    raise RuntimeError('ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED')

'''


def replace_runtime(source):
    # Bounded edits anchored on functions observed in user's current runtime.
    if START in source:
        source = source[:source.index(START)] + source[source.index(END)+len(END):]
    match = re.search(r'(?m)^def _live_010_send_once\(raw\):\n', source)
    finish = re.search(r'(?m)^def _live_010_certify_or_send\(', source)
    if not match or not finish or finish.start()<=match.start():
        raise RuntimeError('HOLD_DIRECT_SEND_FUNCTION_BOUNDARY_CHANGED')
    body=source[match.start():finish.start()]
    if 'sendTransaction' not in body and 'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED' not in body:
        raise RuntimeError('HOLD_EXPECTED_DIRECT_SEND_BODY_NOT_FOUND')
    source = source[:match.start()] + SEND_BLOCK + source[finish.start():]
    if source.count('def preload_canary_saved_alts(')!=1:
        raise RuntimeError('HOLD_ALT_PRELOAD_FUNCTION_COUNT')
    run=re.search(r'(?m)^def run\(\s*$',source)
    if not run:
        # Some later runtime versions have a one-line signature.
        run=re.search(r'(?m)^def run\(',source)
    if not run:
        raise RuntimeError('HOLD_NATIVE_RUN_ANCHOR_NOT_FOUND')
    source=source[:run.start()]+INJECT+source[run.start():]
    # Hard fail-closed if the canary variable is not precisely identifiable.
    count=source.count('CANARY_TRADE_SOL=0.010')
    if count!=1:
        raise RuntimeError('HOLD_CANARY_SIZE_BOUNDARY_CHANGED count=%d'%count)
    source=source.replace('CANARY_TRADE_SOL=0.010','CANARY_TRADE_SOL=0.050',1)
    # Replace misleading labels, without touching any transaction instruction literal.
    source=source.replace('"armed=%s exact_size=0.010 "','"armed=%s exact_size=0.050 "')
    ast.parse(source)
    return source


def replace_launcher(source):
    # Source is the ORACLE-157 full launcher; preserve Credential Manager integration.
    if 'def block_broadcast(core):' not in source or 'runtime.run(float(seconds))' not in source:
        raise RuntimeError('HOLD_LAUNCHER_ORACLE157_INTERFACE_CHANGED')
    # Existing core RPC guard alone was incomplete: q96._rpc is the direct send path.
    old='    block_broadcast(core)\n'
    new='    block_broadcast(core)\n'
    anchor="        runtime = importlib.import_module('qseries_v2.oracle_execution.solana_atomic_executor.runtime')\n"
    if source.count(old)!=1 or source.count(anchor)!=1:
        raise RuntimeError('HOLD_LAUNCHER_GUARD_OR_IMPORT_ANCHOR_CHANGED')
    guard="""        # Guard the runtime's direct q96 transport in addition to core.rpc.
        if not hasattr(runtime, 'q96') or not callable(getattr(runtime.q96, '_rpc', None)):
            raise RuntimeError('HOLD_Q96_DIRECT_TRANSPORT_NOT_GUARDABLE')
        original_q96_rpc = runtime.q96._rpc
        def guarded_q96_rpc(method, params):
            if str(method).lower() in {m.lower() for m in BLOCKED}:
                raise RuntimeError('ORACLE158_Q96_BROADCAST_PROHIBITED')
            return original_q96_rpc(method, params)
        runtime.q96._rpc = guarded_q96_rpc
"""
    source=source.replace(old,new,1)
    source=source.replace(anchor,anchor+guard,1)
    if 'runtime.q96._rpc = guarded_q96_rpc' not in source:
        raise RuntimeError('HOLD_Q96_GUARD_NOT_INSTALLED')
    ast.parse(source)
    return source


def check_state():
    if not REGISTRY.is_file() or not PROOF.is_file():
        raise RuntimeError('HOLD_VERIFIED_CANONICAL_ALT_FILES_MISSING')
    reg=json.loads(REGISTRY.read_text(encoding='utf-8'))
    proof=json.loads(PROOF.read_text(encoding='utf-8'))
    if not (isinstance(reg,dict) and isinstance(proof,dict)
            and proof.get('ok') is True and proof.get('active') is True
            and proof.get('address')==reg.get('address')):
        raise RuntimeError('HOLD_CANONICAL_ALT_PROOF_INVALID')
    return reg['address']


def test():
    # Test against representative source shapes; no network, signing, or trading.
    fixture=('CANARY_TRADE_SOL=0.010\n'
             'def preload_canary_saved_alts(root):\n    return 2\n\n'
             'def _live_010_send_once(raw):\n    return q96._rpc("sendTransaction",[raw])\n\n'
             'def _live_010_certify_or_send(*args):\n    return False\n\n'
             'def run(\n    seconds=90\n):\n    return 0\n')
    updated=replace_runtime(fixture)
    assert 'CANARY_TRADE_SOL=0.050' in updated
    assert 'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED' in updated
    assert 'ORACLE158_VERIFIED_ALT_PRELOAD_BEGIN' in updated
    assert updated.index('ORACLE158_VERIFIED_ALT_PRELOAD_BEGIN') < updated.index('def run(')
    assert updated.count('def _live_010_send_once(')==1
    try:
        replace_runtime('def run():\n    pass\n')
    except RuntimeError:
        pass
    else: raise AssertionError('unrecognized source was allowed')
    print('[TEST PASS] ORACLE158 exact ALT startup cache, fail-closed send, 0.050 simulation variable')


def install():
    alt=check_state()
    src=RUNTIME.read_text(encoding='utf-8')
    launcher=LAUNCHER.read_text(encoding='utf-8')
    if START in src:
        raise RuntimeError('HOLD_ORACLE158_ALREADY_INSTALLED_DO_NOT_DOUBLE_WRAP')
    updated=replace_runtime(src)
    updated_launcher=replace_launcher(launcher)
    # Validate both before writing any file. Never write secrets to disk.
    ast.parse(updated);ast.parse(updated_launcher)
    bak=RUNTIME.with_suffix('.pre_oracle158.bak')
    lbak=LAUNCHER.with_suffix('.pre_oracle158.bak')
    if bak.exists() or lbak.exists():
        raise RuntimeError('HOLD_EXISTING_ORACLE158_BACKUP_REQUIRES_REVIEW')
    bak.write_text(src,encoding='utf-8')
    lbak.write_text(launcher,encoding='utf-8')
    try:
        RUNTIME.write_text(updated,encoding='utf-8')
        LAUNCHER.write_text(updated_launcher,encoding='utf-8')
        py_compile.compile(str(RUNTIME),doraise=True)
        py_compile.compile(str(LAUNCHER),doraise=True)
    except Exception:
        RUNTIME.write_text(src,encoding='utf-8')
        LAUNCHER.write_text(launcher,encoding='utf-8')
        raise
    print('[INSTALL PASS] ORACLE158 native ALT startup binding and simulation-only boundary')
    print('[CANONICAL_ALT]',alt)
    print('[SIZE] CANARY_TRADE_SOL=0.050 (runtime variable; native size requires live proof)')
    print('[GUARD] direct-send source BLOCKED; q96 RPC BLOCKED; existing core RPC BLOCKED')
    print('[SCOPE] no scanner edits; no private-key storage; no broadcast')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--test',action='store_true')
    args=ap.parse_args()
    if args.test:test()
    else: install()
if __name__=='__main__':main()
