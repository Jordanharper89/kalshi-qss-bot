"""ORACLE169 full installer: real compiler-boundary packet and ATA evidence.
No RPC, wallet access, signing or broadcast during install/test. Scanner untouched.
"""
import argparse
import ast
import json
from pathlib import Path

TARGET=Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE169_NATIVE_COMPILE_EVIDENCE.jsonl')
MARK='# ORACLE169_NATIVE_COMPILE_EVIDENCE:'
INSERT='''        # ORACLE169_NATIVE_COMPILE_EVIDENCE: never persist bytes, wallet, or secrets.
        try:
            _c169=route.get('original_candidates') if isinstance(route,dict) else None
            _out169=[]
            if isinstance(_c169,(list,tuple)):
                for _entry169 in _c169:
                    if not isinstance(_entry169,(list,tuple)) or len(_entry169)<2:
                        continue
                    _name169,_ixs169=_entry169[0],_entry169[1]
                    if not isinstance(_ixs169,(list,tuple)):
                        continue
                    _programs169=[_ix169.get('programId') for _ix169 in _ixs169 if isinstance(_ix169,dict)]
                    _ata169='ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'
                    _pump169='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
                    _meteora169=route.get('meteora_ix',{}).get('programId') if isinstance(route.get('meteora_ix'),dict) else None
                    _out169.append({'candidate':str(_name169)[:64],
                        'instruction_count':len(_ixs169),
                        'ata_first_two':len(_programs169)>=2 and _programs169[:2]==[_ata169,_ata169],
                        'pump_legs':_programs169.count(_pump169),
                        'meteora_legs':_programs169.count(_meteora169) if _meteora169 else 0,
                        'swap_order':('PUMP_TO_METEORA' if _meteora169 and _pump169 in _programs169 and _meteora169 in _programs169 and _programs169.index(_pump169)<_programs169.index(_meteora169) else 'METEORA_TO_PUMP' if _meteora169 and _pump169 in _programs169 and _meteora169 in _programs169 else 'UNRESOLVED')})
            _ok169=isinstance(result,dict) and result.get('ok') is True
            _bytes169=len(result.get('raw')) if _ok169 and isinstance(result.get('raw'),(bytes,bytearray)) else None
            _record169={'build':'ORACLE169','compiler_pass':_ok169,
                'packet_bytes':_bytes169,'fits_1232':_bytes169 is not None and 100<=_bytes169<=1232,
                'direction':str(route.get('direction','UNKNOWN')) if isinstance(route,dict) else 'UNKNOWN',
                'amount_050_sol':isinstance(route,dict) and route.get('start_lamports')==50000000,
                'candidates':_out169,'signed_simulation_certified':False,
                'profit_certified':False,'broadcast':False}
            _report169=Path('runtime_state/oracle/oracle_live_execution/ORACLE169_NATIVE_COMPILE_EVIDENCE.jsonl')
            _report169.parent.mkdir(parents=True,exist_ok=True)
            with _report169.open('a',encoding='utf-8') as _f169:
                _f169.write(json.dumps(_record169,sort_keys=True)+'\\n')
            print('[ORACLE169_PACKET] pass=%s bytes=%s ata=%s two_legs=%s broadcast=FALSE' % (
                _ok169,_bytes169,any(x['ata_first_two'] for x in _out169),
                any(x['pump_legs']==1 and x['meteora_legs']==1 for x in _out169)),flush=True)
        except Exception as _err169:
            # Telemetry failure never enables a transaction or modifies trade gates.
            print('[ORACLE169_EVIDENCE_HOLD] type=%s broadcast=FALSE' % type(_err169).__name__,flush=True)
'''

def transform(src):
    tree=ast.parse(src)
    if src.count(MARK)==1:
        return src
    if MARK in src:
        raise RuntimeError('HOLD_ORACLE169_PARTIAL_INSTALL')
    funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='compile_current']
    if len(funcs)<2:
        raise RuntimeError('HOLD_ORACLE169_COMPILE_WRAPPER_MISSING')
    node=funcs[-1]
    body=ast.get_source_segment(src,node) or ''
    if '_ORACLE159_ORIGINAL_COMPILE(user,route)' not in body or '_oracle159_record' not in body:
        raise RuntimeError('HOLD_ORACLE169_WRAPPER_NOT_RECOGNIZED')
    anchor='        return result\n'
    if body.count(anchor)!=1:
        raise RuntimeError('HOLD_ORACLE169_RETURN_NOT_UNIQUE')
    start=src.splitlines(keepends=True)
    segment=''.join(start[node.lineno-1:node.end_lineno])
    if segment.count(anchor)!=1:
        raise RuntimeError('HOLD_ORACLE169_BOUNDARY_DRIFT')
    start[node.lineno-1:node.end_lineno]=[segment.replace(anchor,INSERT+anchor,1)]
    out=''.join(start)
    ast.parse(out)
    return out

def test():
    fixture='''def compile_current(user,route):\n    return {}\ndef compile_current(user,route):\n    _oracle159_record('compile_entry')\n    try:\n        result=_ORACLE159_ORIGINAL_COMPILE(user,route)\n        return result\n    except Exception:\n        raise\n'''
    patched=transform(fixture)
    assert MARK in patched and transform(patched)==patched
    assert patched.index(MARK)<patched.rindex('return result')
    try:
        transform('def compile_current(user,route):\n    return {}\n')
        raise AssertionError('missing wrapper accepted')
    except RuntimeError as e:
        assert str(e).startswith('HOLD_ORACLE169')
    print('[TEST PASS] ORACLE169 real compiler hook, idempotency, missing-wrapper HOLD')

def install():
    if not TARGET.is_file():
        raise RuntimeError('HOLD_ORACLE169_RUNTIME_NOT_FOUND')
    before=TARGET.read_text(encoding='utf-8')
    after=transform(before)
    if after==before:
        print('[INSTALL PASS] ORACLE169 already installed')
        return
    backup=TARGET.with_name('runtime.before_oracle169.py')
    if backup.exists() and backup.read_text(encoding='utf-8')!=before:
        raise RuntimeError('HOLD_ORACLE169_BACKUP_CONFLICT')
    if not backup.exists():
        backup.write_text(before,encoding='utf-8')
    TARGET.write_text(after,encoding='utf-8')
    if TARGET.read_text(encoding='utf-8')!=after:
        raise RuntimeError('HOLD_ORACLE169_WRITE_VERIFY_FAILED')
    print('[INSTALL PASS] ORACLE169 native compilation evidence attached; no saved-route file needed')
    print('[SCOPE] capture only on genuine compile attempts; scanner untouched; no live broadcast authority')
    print('[REPORT]',REPORT)

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--test',action='store_true')
    args=ap.parse_args()
    test() if args.test else install()
