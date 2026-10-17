"""ORACLE-166C full installer: existing idempotent ATA readiness for both swap directions.
No RPC, signing, credentials, scanner changes, or broadcasting during installation.
"""
import argparse
import ast
import json
from pathlib import Path

ROOT = Path('qseries_v2/oracle_execution/solana_atomic_executor')
TARGET = ROOT / 'runtime.py'
PROOF = Path('runtime_state/oracle/oracle_live_execution/ORACLE166C_FORWARD_ATA.json')
MARKER = '# ORACLE166C_FORWARD_ATA_READINESS'
OLD = '''    if direction=="METEORA_TO_PUMP":
        out=_reverse_prepend_ata_readiness(
            USER,str(out.get("token") or ""),out)

    return out,old_bound,new_bound'''
NEW = '''    # ORACLE166C_FORWARD_ATA_READINESS
    # Reuse existing idempotent token+WSOL ATA initialization before both swaps.
    if direction in ("PUMP_TO_METEORA", "METEORA_TO_PUMP"):
        out=_reverse_prepend_ata_readiness(
            USER,str(out.get("token") or ""),out)
        if out.get("reverse_ata_ready") is not True:
            raise RuntimeError("ORACLE166C_ATA_NOT_CERTIFIED")
        candidates=out.get("original_candidates")
        if not isinstance(candidates,list) or not candidates:
            raise RuntimeError("ORACLE166C_NO_ATA_CANDIDATES")
        for name,ixs in candidates:
            if not str(name).startswith("ATA_READY_") or len(ixs)<4:
                raise RuntimeError("ORACLE166C_BAD_ATA_CANDIDATE")
            if any(ix.get("programId") !=
                   "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
                   for ix in ixs[:2]):
                raise RuntimeError("ORACLE166C_ATA_PREFIX_MISSING")

    return out,old_bound,new_bound'''

def function(tree, name):
    return [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]

def transform(source):
    tree=ast.parse(source)
    if len(function(tree,'_fast_010_profit_lock_route'))!=1:
        raise RuntimeError('HOLD_ORACLE166C_PROFIT_LOCK_NOT_UNIQUE')
    if len(function(tree,'_reverse_prepend_ata_readiness'))!=1:
        raise RuntimeError('HOLD_ORACLE166C_ATA_HELPER_NOT_UNIQUE')
    helper=ast.get_source_segment(source,function(tree,'_reverse_prepend_ata_readiness')[0]) or ''
    for term in ('_ata_create_idempotent_ix(', '"original_candidates"', '"reverse_ata_ready"'):
        if term not in helper:
            raise RuntimeError('HOLD_ORACLE166C_HELPER_CONTRACT_'+term[:24])
    if 'CANARY_TRADE_LAMPORTS=50_000_000' not in source:
        raise RuntimeError('HOLD_ORACLE166C_AMOUNT_CONTRACT')
    if 'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED' not in source:
        raise RuntimeError('HOLD_ORACLE166C_SEND_GUARD_MISSING')
    if source.count(MARKER)==1:
        if OLD in source or NEW not in source:
            raise RuntimeError('HOLD_ORACLE166C_PARTIAL_INSTALL')
        return source
    if source.count(OLD)!=1 or MARKER in source:
        raise RuntimeError('HOLD_ORACLE166C_UNEXPECTED_PROFIT_LOCK_SOURCE')
    result=source.replace(OLD,NEW,1)
    ast.parse(result)
    return result

def fixture():
    return '''CANARY_TRADE_LAMPORTS=50_000_000
ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED=True
def _reverse_prepend_ata_readiness(user,token,route):
    a=_ata_create_idempotent_ix(user,user,token,'TOKEN')
    out=dict(route)
    out["original_candidates"]=[('ATA_READY', [a,a,1,2])]
    out["reverse_ata_ready"]=True
    return out
def _fast_010_profit_lock_route(route,direction,required_final_out):
    out=dict(route)
    if direction=="PUMP_TO_METEORA":
        pass
    elif direction=="METEORA_TO_PUMP":
        pass
    else:
        raise RuntimeError('BAD_DIRECTION')
    out=_mry019_align_meteora_programs(out)
    if direction=="METEORA_TO_PUMP":
        out=_reverse_prepend_ata_readiness(
            USER,str(out.get("token") or ""),out)

    return out,old_bound,new_bound
'''

def test():
    src=fixture()
    patched=transform(src)
    assert transform(patched)==patched
    assert patched.count(MARKER)==1
    assert 'direction in ("PUMP_TO_METEORA", "METEORA_TO_PUMP")' in patched
    assert patched.index(MARKER)>patched.index('_mry019_align_meteora_programs(out)')
    for broken in (src.replace('50_000_000','10_000_000'),
                   src.replace('ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED','UNSAFE'),
                   src.replace('"reverse_ata_ready"','"not_ready"')):
        try:
            transform(broken)
            raise AssertionError('fail-closed test did not hold')
        except RuntimeError as exc:
            assert str(exc).startswith('HOLD_ORACLE166C_')
    print('[TEST PASS] ORACLE166C both-direction ATA prefix; source contract; idempotency; fail-closed')

def install():
    if not TARGET.is_file():
        raise RuntimeError('HOLD_ORACLE166C_RUNTIME_NOT_FOUND')
    before=TARGET.read_text(encoding='utf-8')
    after=transform(before)
    if after==before:
        print('[INSTALL PASS] ORACLE166C already installed')
        return
    backup=TARGET.with_name('runtime.before_oracle166c.py')
    if backup.exists() and backup.read_text(encoding='utf-8')!=before:
        raise RuntimeError('HOLD_ORACLE166C_BACKUP_CONFLICT')
    if not backup.exists():
        backup.write_text(before,encoding='utf-8')
    TARGET.write_text(after,encoding='utf-8')
    if TARGET.read_text(encoding='utf-8')!=after:
        raise RuntimeError('HOLD_ORACLE166C_WRITE_VERIFICATION_FAILED')
    PROOF.parent.mkdir(parents=True,exist_ok=True)
    PROOF.write_text(json.dumps({'build':'ORACLE166C','ata_directions':['PUMP_TO_METEORA','METEORA_TO_PUMP'],
        'size_lamports':50000000,'broadcast_authorized':False,'signed_simulation_pass':False},indent=2),encoding='utf-8')
    print('[INSTALL PASS] ORACLE166C both-direction ATA readiness')
    print('[PROOF]',PROOF)
    print('[GUARD] scanner untouched; secure launcher only; no signing/broadcast from installer')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--test',action='store_true')
    args=parser.parse_args()
    test() if args.test else install()
