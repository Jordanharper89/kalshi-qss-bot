"""ORACLE-166 full installer: forward ATA readiness before atomic swaps.
Simulation-only; no scanner, key, RPC or send operations in this installer.
"""
import argparse
import ast
import json
from pathlib import Path

TARGET = Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
REPORT = Path('runtime_state/oracle/oracle_live_execution/ORACLE166_FORWARD_ATA_READINESS.json')
OLD = '''    if direction=="METEORA_TO_PUMP":
        out=_reverse_prepend_ata_readiness(
            USER,str(out.get("token") or ""),out)

    return out,old_bound,new_bound'''
NEW = '''    # ORACLE166_FORWARD_ATA_READINESS: both directions need initialized token ATAs.
    # The existing helper constructs two idempotent ATA instructions and prepends
    # them to every original candidate without changing either swap leg.
    if direction in ("PUMP_TO_METEORA", "METEORA_TO_PUMP"):
        out=_reverse_prepend_ata_readiness(
            USER,str(out.get("token") or ""),out)
        if not out.get("reverse_ata_ready"):
            raise RuntimeError("ORACLE166_ATA_PREPEND_NOT_CERTIFIED")
        rows=out.get("original_candidates")
        if not isinstance(rows,list) or not rows:
            raise RuntimeError("ORACLE166_NO_ATA_CANDIDATES")
        for name,ixs in rows:
            if not str(name).startswith("ATA_READY_") or len(ixs)<4:
                raise RuntimeError("ORACLE166_ATA_CANDIDATE_INVALID")
            if any(str(ix.get("programId")) !=
                   "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
                   for ix in ixs[:2]):
                raise RuntimeError("ORACLE166_ATA_INSTRUCTION_MISSING")

    return out,old_bound,new_bound'''

def swap(source):
    if source.count('ORACLE166_FORWARD_ATA_READINESS:') == 1:
        assert OLD not in source, 'ORACLE166_PARTIAL_INSTALL'
        return source
    if source.count(OLD) != 1:
        raise RuntimeError('HOLD_ORACLE166_PROFIT_LOCK_ANCHOR_NOT_UNIQUE')
    if source.count('def _reverse_prepend_ata_readiness(') != 1:
        raise RuntimeError('HOLD_ORACLE166_ATA_HELPER_NOT_UNIQUE')
    for term in ('def _fast_010_profit_lock_route(',
                 'def _ata_create_idempotent_ix(',
                 'ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED',
                 'ORACLE162_SIGNATURE_VALID',
                 'CANARY_TRADE_LAMPORTS=50_000_000'):
        if term not in source:
            raise RuntimeError('HOLD_ORACLE166_MISSING_' + term[:40])
    result=source.replace(OLD,NEW,1)
    ast.parse(result)
    return result

def test():
    fixture='''CANARY_TRADE_LAMPORTS=50_000_000
ORACLE158_SIMULATION_ONLY_DIRECT_SEND_BLOCKED = True
ORACLE162_SIGNATURE_VALID = True
def _ata_create_idempotent_ix(): pass
def _reverse_prepend_ata_readiness(user,token,route): pass
def _fast_010_profit_lock_route(route,direction,required_final_out):
    if direction=="METEORA_TO_PUMP":
        out=_reverse_prepend_ata_readiness(
            USER,str(out.get("token") or ""),out)

    return out,old_bound,new_bound
'''
    out=swap(fixture)
    assert swap(out)==out
    assert 'direction in ("PUMP_TO_METEORA", "METEORA_TO_PUMP")' in out
    assert out.count('ORACLE166_FORWARD_ATA_READINESS:')==1
    try:
        swap(fixture.replace('return out,old_bound,new_bound','return out'))
        raise AssertionError('expected fail closed')
    except RuntimeError as e:
        assert str(e).startswith('HOLD_ORACLE166_')
    print('[TEST PASS] ORACLE166 forward and reverse ATA readiness; idempotent; fail closed')

def install():
    if not TARGET.is_file():
        raise RuntimeError('HOLD_ORACLE166_RUNTIME_NOT_FOUND')
    before=TARGET.read_text(encoding='utf-8')
    after=swap(before)
    if before==after:
        print('[INSTALL PASS] ORACLE166 already installed')
        return
    backup=TARGET.with_name('runtime.before_oracle166.py')
    if backup.exists():
        if backup.read_text(encoding='utf-8')!=before:
            raise RuntimeError('HOLD_ORACLE166_BACKUP_CONFLICT')
    else:
        backup.write_text(before,encoding='utf-8')
    TARGET.write_text(after,encoding='utf-8')
    if TARGET.read_text(encoding='utf-8')!=after:
        raise RuntimeError('HOLD_ORACLE166_WRITE_MISMATCH')
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps({'build':'ORACLE166',
        'readiness_directions':['PUMP_TO_METEORA','METEORA_TO_PUMP'],
        'trade_amount_lamports':50000000,'broadcast_authorized':False,
        'native_compiler_byte_limit':1232,'live_simulation_certified':False},indent=2),
        encoding='utf-8')
    print('[INSTALL PASS] ORACLE166 forward ATA readiness; simulator only')
    print('[PROOF]',REPORT)
    print('[GUARD] no wallet credential access; no signing or broadcast in installer')
    print('[NEXT] native compiler must fit 1232 bytes; otherwise HOLD, never omit ATA')

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--test',action='store_true')
    args=parser.parse_args()
    test() if args.test else install()
