
"""ORACLE176 complete installer: certify the selected serialized signed v0 packet."""
import argparse, ast
from build_oracle_173_rpc_backoff_boundary import install_block, TARGET

MARK='# ORACLE176_COMPILED_V0_IDENTITY'
BLOCK='''# ORACLE176_COMPILED_V0_IDENTITY
_ORACLE176_PREVIOUS_COMPILE=compile_current

def _oracle176_verify_packet(tx,route,user,raw_length):
    if not hasattr(tx.message,'address_table_lookups'):
        raise RuntimeError('ORACLE176_NOT_V0')
    if len(tx.signatures)!=1 or list(tx.verify_with_results())!=[True]:
        raise RuntimeError('ORACLE176_SIGNATURE_NOT_VERIFIED')
    msg=tx.message
    keys=[str(x) for x in msg.account_keys]
    if not keys or keys[0]!=str(user):
        raise RuntimeError('ORACLE176_PAYER_MISMATCH')
    if type(raw_length) is not int or not 100<=raw_length<=1232:
        raise RuntimeError('ORACLE176_PACKET_SIZE_INVALID')
    if route.get('start_lamports')!=50_000_000:
        raise RuntimeError('ORACLE176_AMOUNT_MISMATCH')
    programs=[]
    swap_bytes=[]
    for ix in msg.instructions:
        index=int(ix.program_id_index)
        if index>=len(keys):
            raise RuntimeError('ORACLE176_UNRESOLVED_ALT_PROGRAM_ID')
        programs.append(keys[index])
        swap_bytes.append(bytes(ix.data))
    ata='ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL'
    pump='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
    meteora_ix=route.get('meteora_ix')
    meteora=(meteora_ix or {}).get('programId') if isinstance(meteora_ix,dict) else None
    if not meteora or programs[:2]!=[ata,ata]:
        raise RuntimeError('ORACLE176_NATIVE_ATA_PREFIX_MISSING')
    if programs.count(pump)!=1 or programs.count(meteora)!=1:
        raise RuntimeError('ORACLE176_NATIVE_SWAP_LEGS_MISSING')
    direction=route.get('direction')
    actual=('PUMP_TO_METEORA' if programs.index(pump)<programs.index(meteora)
            else 'METEORA_TO_PUMP')
    if actual!=direction:
        raise RuntimeError('ORACLE176_DIRECTION_MISMATCH')
    if direction=='PUMP_TO_METEORA':
        raw=swap_bytes[programs.index(pump)]
        disc=bytes([198,46,21,82,180,217,232,112])
        if len(raw)<24 or raw[:8]!=disc:
            raise RuntimeError('ORACLE176_NATIVE_PUMP_BUY_UNKNOWN')
        spend=int.from_bytes(raw[8:16],'little')
        if not 45_000_000<=spend<=50_000_000:
            raise RuntimeError('ORACLE176_NATIVE_BUY_AMOUNT_INVALID')
    return {'direction':direction,'packet_bytes':raw_length,
            'ata_prefix':True,'native_both_legs':True,'signature_verified':True}

def compile_current(user,route):
    compiled=_ORACLE176_PREVIOUS_COMPILE(user,route)
    if not isinstance(compiled,dict) or compiled.get('ok') is not True:
        return compiled
    raw=compiled.get('raw')
    if not isinstance(raw,(bytes,bytearray)) or compiled.get('oracle162_signature_verified') is not True:
        raise RuntimeError('ORACLE176_SIGNED_NATIVE_PACKET_REQUIRED')
    from solders.transaction import VersionedTransaction as _V176
    from solders.message import to_bytes_versioned as _mbytes176
    tx=_V176.from_bytes(bytes(raw))
    evidence=_oracle176_verify_packet(tx,route,user,len(raw))
    digest=__import__('hashlib').sha256(_mbytes176(tx.message)).hexdigest()
    compiled=dict(compiled)
    compiled['oracle176_packet_hash']=digest
    compiled['oracle176_packet_verified']=True
    compiled['oracle176_route_net']=route.get('pre_sim_net_lamports')
    import json as _json
    from pathlib import Path as _Path
    proof=dict(evidence,build='ORACLE176',message_sha256=digest,
               signed_simulation_pass=False,broadcast=False)
    path=_Path('runtime_state/oracle/oracle_live_execution/ORACLE176_NATIVE_PACKET.jsonl')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('a',encoding='utf-8') as f:
        f.write(_json.dumps(proof,sort_keys=True)+'\\n')
    print('[ORACLE176_PACKET_PASS] bytes=%d direction=%s digest=%s broadcast=FALSE' %
          (len(raw),route['direction'],digest[:16]),flush=True)
    return compiled
'''

def test():
    ast.parse(BLOCK)
    class Object:pass
    class FakeTx:
        signatures=[1]
        def verify_with_results(self):return [True]
    class Ix:
        def __init__(self,p,d=b''):
            self.program_id_index=p
            self.data=d
    env={'compile_current':lambda u,r:{'ok':False}}
    exec(BLOCK,env)
    tx=FakeTx()
    msg=Object()
    tx.message=msg
    msg.account_keys=['wallet','ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL',
                      'pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA','meteora']
    msg.address_table_lookups=[]
    data=(bytes([198,46,21,82,180,217,232,112])
          +(50_000_000).to_bytes(8,'little')+b'\x00'*8)
    msg.instructions=[Ix(1),Ix(1),Ix(2,data),Ix(3)]
    route={'start_lamports':50_000_000,'direction':'PUMP_TO_METEORA',
           'meteora_ix':{'programId':'meteora'}}
    assert env['_oracle176_verify_packet'](tx,route,'wallet',1100)['native_both_legs']
    msg.instructions[1]=Ix(2)
    try:
        env['_oracle176_verify_packet'](tx,route,'wallet',1100)
    except RuntimeError:pass
    else:raise AssertionError('missing ATA accepted')
    print('[TEST PASS] ORACLE176 signed v0 payer, selected instructions, bytes, directions')

def install():
    install_block('ORACLE176',MARK,BLOCK,
        ('ORACLE175_ATA_ACCOUNT_IDENTITY','ORACLE162_SIGNATURE_BOUNDARY_IMPORT'))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    a=p.parse_args()
    test() if a.test else install()
