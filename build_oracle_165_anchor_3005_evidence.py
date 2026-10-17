"""ORACLE-165 full installer: capture actual Anchor-3005 failure lineage; simulation only."""
from __future__ import annotations
import argparse
import ast
from pathlib import Path

RUNTIME = Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
PROOF = Path('runtime_state/oracle/oracle_live_execution/ORACLE165_ANCHOR_FAILURE.jsonl')
BEGIN = '    if not _live_010_armed():\n'
END = '    with LIVE_010_LOCK:\n'
MARKER = '# ORACLE165_ANCHOR_FAILURE_LINEAGE'

# ORACLE-164 stays the complete disarmed simulation implementation; insert
# targeted failure lineage immediately before its existing unconditional return.
EXTRA = '''        # ORACLE165_ANCHOR_FAILURE_LINEAGE
        # Only public Solana program logs and sanitized structured failure info.
        if _verdict164 == 'EXECUTION_REJECTED':
            _index165 = None
            _code165 = None
            if isinstance(_rpcerr164, dict):
                _pair165 = _rpcerr164.get('InstructionError')
                if isinstance(_pair165, list) and len(_pair165) == 2:
                    _index165 = _pair165[0] if isinstance(_pair165[0], int) else None
                    _custom165 = _pair165[1]
                    if isinstance(_custom165, dict):
                        _code165 = _custom165.get('Custom')
            _rows165 = _logrows164 if isinstance(_logrows164, list) else []
            _keep165 = []
            for _line165 in _rows165:
                if not isinstance(_line165, str):
                    continue
                _low165 = _line165.lower()
                if ('invoke [' in _low165 or 'failed:' in _low165 or
                    'anchorerror' in _low165 or 'error code:' in _low165 or
                    'error number:' in _low165 or 'error message:' in _low165 or
                    'instruction:' in _low165 or 'program log: left:' in _low165 or
                    'program log: right:' in _low165 or 'not enough account' in _low165):
                    _keep165.append(_line165[:300])
            _evidence165 = dict(build='ORACLE165',direction=str(direction),
                token=str(token)[:12],slot=int(slot),instruction_index=_index165,
                custom_code=_code165,raw_error=str(_rpcerr164)[:180],
                log_count=len(_rows165),important_logs=_keep165[-60:],
                packet_bytes=len(_raw164),amount_lamports=50000000,
                broadcast=False,certified_profit=False)
            try:
                _fpath165 = Path('runtime_state/oracle/oracle_live_execution/ORACLE165_ANCHOR_FAILURE.jsonl')
                _fpath165.parent.mkdir(parents=True, exist_ok=True)
                with _fpath165.open('a',encoding='utf-8') as _out165:
                    _out165.write(json.dumps(_evidence165,sort_keys=True)+'\\n')
            except (OSError,TypeError,ValueError):
                print('[ORACLE165_EVIDENCE_WRITE_HOLD]',flush=True)
            print('[ORACLE165_ANCHOR_FAILURE] ix=%s code=%s captured=%d/%d broadcast=FALSE' %
                  (str(_index165),str(_code165),len(_keep165),len(_rows165)),flush=True)
            for _line165 in _keep165[-16:]:
                print('[ORACLE165_PROGRAM_LOG] %s' % _line165,flush=True)
'''

def transform(src):
    if src.count(MARKER) == 1:
        ast.parse(src)
        return src
    if MARKER in src or src.count(BEGIN)!=1:
        raise RuntimeError('HOLD_165_BRANCH_NOT_UNIQUE')
    a=src.index(BEGIN)
    b=src.find(END,a)
    if b<0 or b-a>5500:
        raise RuntimeError('HOLD_165_ARMED_BOUNDARY_NOT_FOUND')
    branch=src[a:b]
    for needed in ('ORACLE164_SIMULATION_TRUTH_BOUNDARY','_verdict164',
                   '_logrows164','_rpcerr164','[ORACLE164_SIM_VERDICT]'):
        if needed not in branch:
            raise RuntimeError('HOLD_165_164_CONTRACT_MISSING:'+needed)
    for needed in ('ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED',
                   '_oracle162_verify_and_sign',
                   'CANARY_TRADE_LAMPORTS=50_000_000'):
        if needed not in src:
            raise RuntimeError('HOLD_165_GUARD_MISSING:'+needed)
    # Strict final return of disarmed block only; never enter armed branch.
    if not branch.endswith('        return\n'):
        raise RuntimeError('HOLD_165_UNEXPECTED_FINAL_RETURN')
    changed=src[:b-len('        return\n')]+EXTRA+'        return\n'+src[b:]
    ast.parse(changed)
    return changed

def test():
    fixture='''from pathlib import Path
import json
CANARY_TRADE_LAMPORTS=50_000_000
ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED=True
_oracle162_verify_and_sign=True
def f():
    if not _live_010_armed():
        # ORACLE164_SIMULATION_TRUTH_BOUNDARY
        _verdict164='EXECUTION_REJECTED'
        _logrows164=[]
        _rpcerr164={'InstructionError':[3,{'Custom':3005}]}
        print('[ORACLE164_SIM_VERDICT]')
        return
    with LIVE_010_LOCK:
        raise AssertionError('send')
'''
    changed=transform(fixture)
    assert transform(changed)==changed
    assert changed.count(MARKER)==1
    assert changed.index(MARKER)<changed.index('    with LIVE_010_LOCK:')
    assert 'sendTransaction' not in EXTRA
    for bad in (fixture.replace('ORACLE164_SIMULATION_TRUTH_BOUNDARY','OLD'),
                fixture.replace('ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED','OLD')):
        try: transform(bad)
        except RuntimeError: pass
        else: raise AssertionError('HOLD gate missing')
    print('[TEST PASS] ORACLE165 Anchor account error logs, fail-closed, disarmed boundary')

def install():
    if not RUNTIME.is_file():
        raise RuntimeError('HOLD_165_RUNTIME_MISSING')
    source=RUNTIME.read_text(encoding='utf-8')
    changed=transform(source)
    if changed==source:
        print('[INSTALL PASS] ORACLE165 already installed')
        return
    backup=RUNTIME.with_name('runtime.before_oracle165.py')
    if backup.exists():
        raise RuntimeError('HOLD_165_BACKUP_EXISTS')
    backup.write_text(source,encoding='utf-8')
    try:
        RUNTIME.write_text(changed,encoding='utf-8')
        ast.parse(RUNTIME.read_text(encoding='utf-8'))
    except Exception:
        RUNTIME.write_text(source,encoding='utf-8')
        raise
    print('[INSTALL PASS] ORACLE165 Anchor 3005 evidence lineage')
    print('[PROOF]',PROOF)
    print('[GUARD] disarmed signed simulation only; no scanner or transaction edits; no broadcast')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--test',action='store_true')
    args=parser.parse_args()
    test() if args.test else install()
