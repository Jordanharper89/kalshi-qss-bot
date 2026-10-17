
"""ORACLE174 complete installer: enforce 0.050 SOL native-route quote admission."""
import argparse, ast, base64
from pathlib import Path
from build_oracle_173_rpc_backoff_boundary import install_block, TARGET

MARK='# ORACLE174_EXACT_QUOTE_GATE'
BLOCK='''# ORACLE174_EXACT_QUOTE_GATE
_ORACLE174_ORIGINAL_LOCK=_fast_010_profit_lock_route

def _oracle174_decode_data(value):
    import base64 as _base64
    if isinstance(value,(bytes,bytearray)):return bytes(value)
    if isinstance(value,(list,tuple)) and all(type(v) is int and 0<=v<=255 for v in value):
        return bytes(value)
    if isinstance(value,str):
        if value.startswith('0x'):
            try:return bytes.fromhex(value[2:])
            except ValueError:return None
        try:return _base64.b64decode(value,validate=True)
        except (ValueError,TypeError):return None
    return None

def _oracle174_validate(route,direction):
    if not isinstance(route,dict) or type(route.get('start_lamports')) is not int:
        raise RuntimeError('ORACLE174_ROUTE_AMOUNT_ABSENT')
    if route['start_lamports']!=50_000_000:
        raise RuntimeError('ORACLE174_ROUTE_NOT_EXACT_050')
    if str(direction) not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):
        raise RuntimeError('ORACLE174_UNKNOWN_DIRECTION')
    candidates=route.get('original_candidates')
    if not isinstance(candidates,(list,tuple)) or not candidates:
        raise RuntimeError('ORACLE174_NATIVE_CANDIDATES_ABSENT')
    disc=bytes([198,46,21,82,180,217,232,112])
    checked=0
    for _,ixs in candidates:
        if not isinstance(ixs,(list,tuple)):
            raise RuntimeError('ORACLE174_BAD_CANDIDATE')
        for ix in ixs:
            if not isinstance(ix,dict):
                raise RuntimeError('ORACLE174_BAD_INSTRUCTION')
            if ix.get('programId')!='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA':
                continue
            raw=_oracle174_decode_data(ix.get('data'))
            if not raw or len(raw)<8:
                raise RuntimeError('ORACLE174_UNKNOWN_PUMP_DATA')
            if raw[:8]!=disc:continue
            if len(raw)<24:raise RuntimeError('ORACLE174_SHORT_BUY_DATA')
            amount=int.from_bytes(raw[8:16],'little')
            if not 45_000_000<=amount<=50_000_000:
                raise RuntimeError('ORACLE174_BUY_SPEND_NOT_050_BOUND')
            checked+=1
    if direction=='PUMP_TO_METEORA' and checked<1:
        raise RuntimeError('ORACLE174_FORWARD_BUY_NOT_VERIFIED')
    return checked

def _fast_010_profit_lock_route(route,direction,required_final_out):
    result=_ORACLE174_ORIGINAL_LOCK(route,direction,required_final_out)
    if not isinstance(result,tuple) or len(result)!=3:
        raise RuntimeError('ORACLE174_LOCK_RESULT_CHANGED')
    _oracle174_validate(result[0],direction)
    return result
'''

def test():
    ast.parse(BLOCK)
    env={'_fast_010_profit_lock_route':lambda r,d,m:(r,0,m)}
    exec(BLOCK,env)
    disc=bytes([198,46,21,82,180,217,232,112])
    buy=base64.b64encode(disc+(50_000_000).to_bytes(8,'little')+b'\x01'*8).decode()
    pump='pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA'
    route={'start_lamports':50_000_000,'original_candidates':[
        ('ATA_READY',[{'programId':pump,'data':buy}])]}
    assert env['_fast_010_profit_lock_route'](route,'PUMP_TO_METEORA',2)[0]==route
    for amount in (10_000_000,50_000_001):
        data=base64.b64encode(disc+amount.to_bytes(8,'little')+b'\x01'*8).decode()
        broken={'start_lamports':50_000_000,'original_candidates':[
            ('X',[{'programId':pump,'data':data}])]}
        try:
            env['_oracle174_validate'](broken,'PUMP_TO_METEORA')
        except RuntimeError:pass
        else:raise AssertionError('mismatched amount passed')
    print('[TEST PASS] ORACLE174 exact-size route, native Pump amount, 10m rejected')

def install():
    if not TARGET.is_file():raise RuntimeError('HOLD_ORACLE174_RUNTIME_NOT_FOUND')
    if 'def _fast_010_profit_lock_route(' not in TARGET.read_text(encoding='utf-8'):
        raise RuntimeError('HOLD_ORACLE174_REAL_PROFIT_LOCK_MISSING')
    install_block('ORACLE174',MARK,BLOCK,('ORACLE166C_FORWARD_ATA_READINESS',))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    args=p.parse_args()
    test() if args.test else install()
