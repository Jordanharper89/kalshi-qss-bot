"""ORACLE-160 complete installer: repair native amount agreement, fail closed.

Windows CMD: python build_oracle_160_exact_amount_boundary.py --test
             python build_oracle_160_exact_amount_boundary.py
This installer never loads credentials, signs, simulates or broadcasts.
"""
from __future__ import annotations
import argparse
import ast
import json
import re
from pathlib import Path

ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
RUNTIME=ROOT/'runtime.py'
COMPILER=ROOT/'oracle105_sdk_worker/oracle149_atomic_alt_compiler.py'
REPORT=Path('runtime_state/oracle/oracle_live_execution/ORACLE160_AMOUNT_CONTRACT.json')
SIZE_SOL='0.050'
SIZE_LAMPORTS=50_000_000
MARKER='# ORACLE160_EXACT_AMOUNT_CONTRACT'

def transform(src):
    for symbol,new in [('CANARY_TRADE_SOL',SIZE_SOL),('CANARY_TRADE_LAMPORTS',f'{SIZE_LAMPORTS:_}')]:
        pattern=r'(?m)^'+symbol+r'\s*=\s*([^\n#]+)([^\n]*)$'
        matches=list(re.finditer(pattern,src))
        if len(matches)!=1:
            raise RuntimeError('HOLD_'+symbol+'_DECLARATION_COUNT_'+str(len(matches)))
        old=matches[0].group(1).strip()
        if not re.fullmatch(r'[0-9_.]+',old):
            raise RuntimeError('HOLD_'+symbol+'_DYNAMIC_OR_UNKNOWN_VALUE')
        if symbol=='CANARY_TRADE_SOL' and float(old)!=float(SIZE_SOL):
            raise RuntimeError('HOLD_SIZE_SOL_NOT_AT_REQUESTED_0_050')
        if symbol=='CANARY_TRADE_LAMPORTS' and int(old.replace('_','')) not in (10_000_000,SIZE_LAMPORTS):
            raise RuntimeError('HOLD_UNEXPECTED_LAMPORTS_VALUE_'+old)
        src=src[:matches[0].start()]+symbol+'='+new+matches[0].group(2)+src[matches[0].end():]
    if src.count(MARKER)>1:
        raise RuntimeError('HOLD_DUPLICATE_ORACLE160_MARKER')
    if MARKER not in src:
        anchor='CANARY_TRADE_LAMPORTS=50_000_000'
        if src.count(anchor)!=1:
            raise RuntimeError('HOLD_AMOUNT_ANCHOR_CHANGED')
        src=src.replace(anchor, anchor+'\n'+MARKER+'\nif int(round(CANARY_TRADE_SOL * 1_000_000_000)) != CANARY_TRADE_LAMPORTS:\n    raise RuntimeError("ORACLE160_CANARY_AMOUNT_MISMATCH")',1)
    ast.parse(src)
    return src

def inspect(src):
    tree=ast.parse(src)
    vals={}
    for n in tree.body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
            if n.targets[0].id in ('CANARY_TRADE_SOL','CANARY_TRADE_LAMPORTS'):
                vals[n.targets[0].id]=ast.literal_eval(n.value)
    if set(vals)!={'CANARY_TRADE_SOL','CANARY_TRADE_LAMPORTS'}:
        raise RuntimeError('HOLD_NOT_TOP_LEVEL_STATIC_AMOUNTS')
    if vals['CANARY_TRADE_SOL']!=0.050 or vals['CANARY_TRADE_LAMPORTS']!=SIZE_LAMPORTS:
        raise RuntimeError('HOLD_AMOUNT_MISMATCH')
    mandatory=('def compile_current(user,route):','def simulate_current(',
               'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED',
               'ORACLE158_VERIFIED_ALT_PRELOAD_BEGIN',
               'ORACLE159_EXECUTION_BOUNDARY_BEGIN')
    missing=[s for s in mandatory if s not in src]
    if missing: raise RuntimeError('HOLD_MISSING_PRIOR_RUNTIME_CONTRACT_'+','.join(missing))
    if 'return _o149.compile_route(user,route,BLOCKHASH.get())' not in src:
        raise RuntimeError('HOLD_COMPILER_DELEGATION_CHANGED')
    return vals

def test():
    fixture='CANARY_TRADE_SOL=0.050\nCANARY_TRADE_LAMPORTS=10_000_000\n'
    fixed=transform(fixture)
    assert 'CANARY_TRADE_LAMPORTS=50_000_000' in fixed
    assert 'ORACLE160_CANARY_AMOUNT_MISMATCH' in fixed
    assert transform(fixed)==fixed
    for bad in ('CANARY_TRADE_SOL=0.010\nCANARY_TRADE_LAMPORTS=10_000_000\n',
                'CANARY_TRADE_SOL=0.050\nCANARY_TRADE_LAMPORTS=os.getenv("SIZE")\n',
                'CANARY_TRADE_SOL=0.050\nCANARY_TRADE_LAMPORTS=12_000_000\n'):
        try: transform(bad)
        except RuntimeError: pass
        else: raise AssertionError('unsafe candidate accepted')
    assert int(round(0.050 * 1_000_000_000))==SIZE_LAMPORTS
    print('[TEST PASS] ORACLE160 exact amount 0.050 SOL = 50000000 lamports, idempotency, fail-closed mismatches')

def install():
    if not RUNTIME.is_file() or not COMPILER.is_file():
        raise RuntimeError('HOLD_NATIVE_RUNTIME_OR_COMPILER_MISSING')
    original=RUNTIME.read_text(encoding='utf-8')
    compiler=COMPILER.read_text(encoding='utf-8')
    if 'def compile_route(user,route,blockhash):' not in compiler:
        raise RuntimeError('HOLD_COMPILER_CONTRACT_CHANGED')
    # Audit active source before modifying it; existing guards are non-negotiable.
    inspect(original.replace('CANARY_TRADE_LAMPORTS=10_000_000','CANARY_TRADE_LAMPORTS=50_000_000',1))
    updated=transform(original)
    inspect(updated)
    backup=RUNTIME.with_suffix('.pre_oracle160.bak')
    if updated!=original:
        if backup.exists(): raise RuntimeError('HOLD_ORACLE160_BACKUP_ALREADY_EXISTS')
        backup.write_text(original,encoding='utf-8')
        try:
            RUNTIME.write_text(updated,encoding='utf-8')
            if RUNTIME.read_text(encoding='utf-8')!=updated: raise RuntimeError('HOLD_WRITE_READBACK_MISMATCH')
            inspect(updated)
        except Exception:
            RUNTIME.write_text(original,encoding='utf-8')
            raise
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps({'build':'ORACLE160','sim_only':True,
        'target_sol':0.05,'target_lamports':SIZE_LAMPORTS,
        'native_compiler':'oracle149_atomic_alt_compiler.compile_route',
        'native_simulation_proven':False,'broadcast_authorized':False,
        'source_updated':updated!=original},indent=2)+'\n',encoding='utf-8')
    print('[INSTALL PASS] ORACLE160 native amount boundary')
    print('[AMOUNT] 0.050 SOL = 50000000 lamports; quotation, canary guard and template now share constant')
    print('[PROOF]',REPORT)
    print('[GUARD] original scanner unchanged; no secret access; no signing; no broadcast')
    print('[NEXT] guarded simulation must still prove actual packet size and net economics')

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');a=p.parse_args()
    test() if a.test else install()
if __name__=='__main__':main()
