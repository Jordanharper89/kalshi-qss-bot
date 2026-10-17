"""Independent two-leg native transaction compiler. Fail-closed, unsigned only.
Input: complete native instruction JSON, not public-account-only capture.
Usage: python -m qseries_v2.oracle_execution.solana_atomic_executor.oracle_104_independent_atomic_executor --route route.json --blockhash HASH [--alt-snapshot alt.json]
"""
import argparse
import base64
import binascii
import json
from pathlib import Path

PUMP = 'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwCZZ3a6Zk7L'
DLMM = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
WIRE_LIMIT = 1232
ALLOWED_SIZES = {10_000_000, 15_000_000, 20_000_000, 25_000_000, 30_000_000}

class Hold(ValueError):
    pass

def validate(doc):
    if not isinstance(doc, dict) or doc.get('direction') not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):
        raise Hold('INVALID_DIRECTION')
    if type(doc.get('start_lamports')) is not int or doc['start_lamports'] not in ALLOWED_SIZES:
        raise Hold('UNAUTHORIZED_TRADE_SIZE')
    if doc.get('data_included') is False:
        raise Hold('PUBLIC_METADATA_NOT_EXECUTABLE')
    payer = doc.get('payer')
    if not isinstance(payer, str) or not 32 <= len(payer) <= 44:
        raise Hold('PAYER_MISSING')
    ixs = doc.get('instructions')
    if not isinstance(ixs, list) or not 2 <= len(ixs) <= 32:
        raise Hold('FULL_INSTRUCTIONS_REQUIRED')
    programs = []
    for ix in ixs:
        if not isinstance(ix, dict) or not isinstance(ix.get('accounts'), list):
            raise Hold('INVALID_INSTRUCTION')
        if len(ix['accounts']) > 128:
            raise Hold('ACCOUNT_LIMIT')
        program = ix.get('programId')
        if not isinstance(program, str):
            raise Hold('PROGRAM_MISSING')
        programs.append(program)
        try:
            raw = base64.b64decode(ix['data'], validate=True)
        except (KeyError, TypeError, ValueError, binascii.Error):
            raise Hold('NATIVE_INSTRUCTION_DATA_REQUIRED') from None
        if not raw:
            raise Hold('EMPTY_INSTRUCTION_DATA')
        for a in ix['accounts']:
            if not isinstance(a, dict) or not isinstance(a.get('pubkey'), str):
                raise Hold('INVALID_ACCOUNT_META')
            if type(a.get('isSigner')) is not bool or type(a.get('isWritable')) is not bool:
                raise Hold('ACCOUNT_FLAGS_REQUIRED')
    if programs.count(PUMP) != 1 or programs.count(DLMM) != 1:
        raise Hold('EXACTLY_ONE_PUMP_AND_ONE_DLMM_LEG_REQUIRED')
    if (programs.index(PUMP) < programs.index(DLMM)) != (doc['direction']=='PUMP_TO_METEORA'):
        raise Hold('LEG_ORDER_MISMATCH')
    return payer, ixs

def compile_packet(doc, blockhash, alt_snapshot=None):
    payer, ixs = validate(doc)
    try:
        from solders.pubkey import Pubkey
        from solders.hash import Hash
        from solders.instruction import Instruction, AccountMeta
        from solders.message import MessageV0
        from solders.transaction import VersionedTransaction
        from solders.address_lookup_table_account import AddressLookupTableAccount
    except ImportError:
        raise Hold('SOLDERS_DEPENDENCY_REQUIRED') from None
    try:
        p = Pubkey.from_string(payer)
        bh = Hash.from_string(blockhash)
        instructions = [Instruction(Pubkey.from_string(ix['programId']),
            base64.b64decode(ix['data'], validate=True),
            [AccountMeta(Pubkey.from_string(a['pubkey']),a['isSigner'],a['isWritable']) for a in ix['accounts']])
            for ix in ixs]
        alts=[]
        if alt_snapshot is not None:
            if not isinstance(alt_snapshot,dict) or alt_snapshot.get('onchain_verified') is not True:
                raise Hold('ALT_SNAPSHOT_NOT_ONCHAIN_VERIFIED')
            key=alt_snapshot.get('address')
            addresses=alt_snapshot.get('addresses')
            if not isinstance(addresses,list) or not addresses:
                raise Hold('ALT_ADDRESSES_MISSING')
            alts=[AddressLookupTableAccount(Pubkey.from_string(key),[Pubkey.from_string(x) for x in addresses])]
        msg=MessageV0.try_compile(p,instructions,alts,bh)
        # NullSigner creates a canonical unsigned packet; cannot authorize a live send.
        from solders.null_signer import NullSigner
        packet=bytes(VersionedTransaction(msg,[NullSigner(x) for x in msg.account_keys[:msg.header.num_required_signatures]]))
    except Hold:
        raise
    except Exception as exc:
        raise Hold('NATIVE_V0_COMPILE_'+type(exc).__name__) from None
    if len(packet)>WIRE_LIMIT:
        raise Hold('ATOMIC_PACKET_TOO_LARGE_'+str(len(packet)))
    if len(packet)<70 or packet[0] == 0:
        raise Hold('INVALID_UNSIGNED_PACKET')
    return {'status':'UNSIGNED_V0_COMPILED','packet_bytes':len(packet),
            'direction':doc['direction'],'start_lamports':doc['start_lamports'],
            'instructions':len(ixs),'alt_count':len(alts),
            'simulation_passed':False,'net_profit_certified':False,
            'signing':False,'broadcast':False}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--route',required=True)
    ap.add_argument('--blockhash',required=True)
    ap.add_argument('--alt-snapshot')
    args=ap.parse_args()
    try:
        doc=json.loads(Path(args.route).read_text(encoding='utf-8'))
        alt=json.loads(Path(args.alt_snapshot).read_text(encoding='utf-8')) if args.alt_snapshot else None
        print('[ORACLE104]',json.dumps(compile_packet(doc,args.blockhash,alt),sort_keys=True))
    except (Hold,OSError,ValueError) as exc:
        print('[ORACLE104_HOLD]',str(exc).splitlines()[0][:160])
        raise SystemExit(2)

if __name__=='__main__':
    main()
