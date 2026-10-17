"""Disarmed Oracle wallet balance and reverse-route source diagnostic."""
import argparse, ast, hashlib, inspect, os, re, subprocess, sys, urllib.error
from pathlib import Path

def test():
    assert classify('DIRECTION_NOT_CERTIFIED:METEORA_TO_PUMP')=='DIRECTION_NOT_CERTIFIED'
    assert classify('api-key=SECRET')=='REDACTED_NON_CODE'
    assert classify('INSUFFICIENT_QUOTE_ACCOUNT:abc123')=='INSUFFICIENT_QUOTE_ACCOUNT'
    print('[TEST PASS] ORACLE189 reason classifier, no credentials in report')

def classify(message):
    first=str(message).split(':',1)[0].strip()
    if re.fullmatch(r'[A-Z][A-Z0-9_]{3,70}',first):return first
    return 'REDACTED_NON_CODE'

def worker():
    from . import runtime as r
    from . import oracle188_route_and_sim_evidence as diag
    if os.environ.get('QSB_LIVE_ARM','').upper()=='YES':
        raise RuntimeError('ORACLE189_LIVE_ARM_REFUSED')
    if not os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('ORACLE189_KEY_NOT_LOADED')
    if not callable(getattr(r,'_live_010_armed',None)) or r._live_010_armed():
        raise RuntimeError('ORACLE189_DISARM_UNCERTIFIED')
    _,wallet=r.q87.c.sim_identity()
    result=r.q87.c.rpc('getBalance',[wallet,{'commitment':'processed'}])
    if not isinstance(result,dict) or not isinstance(result.get('value'),int):
        raise RuntimeError('ORACLE189_BALANCE_RPC_INVALID')
    available=result['value']
    required=50_000_000
    headroom=available-required
    print('[ORACLE189_BALANCE] lamports=%d target_lamports=%d headroom_lamports=%d target_covered=%s' %
          (available,required,headroom,str(headroom>0).upper()),flush=True)
    if headroom<=0:
        print('[ORACLE189_FUNDS_HOLD] INSUFFICIENT_SOL_FOR_050_PLUS_FEES_AND_RENT',flush=True)
    else:
        print('[ORACLE189_FUNDS_NOTE] HEADROOM_UNVERIFIED_FOR_ATA_RENT_AND_FEES',flush=True)
    fn=getattr(r,'same_snapshot_reverse_route',None)
    if not callable(fn):
        print('[ORACLE189_REVERSE_SOURCE] top_level_function=NOT_EXPORTED',flush=True)
    else:
        try:
            lines,start=inspect.getsourcelines(fn)
            tree=ast.parse(''.join(lines))
            raises=[start+n.lineno-1 for n in ast.walk(tree) if isinstance(n,ast.Raise)]
            print('[ORACLE189_REVERSE_SOURCE] line=%d raises=%s' % (start,','.join(map(str,sorted(raises))) or 'NONE'),flush=True)
        except (OSError,TypeError,IndentationError,SyntaxError):
            print('[ORACLE189_REVERSE_SOURCE] UNAVAILABLE',flush=True)
    original=r.same_snapshot_route
    def tagged(*args,**kw):
        try:return original(*args,**kw)
        except RuntimeError as exc:
            import traceback
            frames=traceback.extract_tb(exc.__traceback__)
            frame=next((f for f in reversed(frames) if f.name=='same_snapshot_reverse_route'),None)
            lineno=frame.lineno if frame else 0
            code=classify(exc)
            print('[ORACLE189_REVERSE_HOLD] code=%s source_line=%d exception_type=RuntimeError broadcast=FALSE' %
                  (code,lineno),flush=True)
            raise
    r.same_snapshot_route=tagged
    try:diag.run()
    finally:r.same_snapshot_route=original

def run():
    import build_oracle_182_secure_windows_credentials as vault
    db=vault.api();h=vault.load(db,vault.HELIUS);s=vault.load(db,vault.SOLANA)
    if not h or not s:raise RuntimeError('ORACLE189_VAULT_MISSING')
    env=os.environ.copy();env['QSB_SOLANA_PRIVATE_KEY']=s
    env['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+vault.quote(h,safe='')
    env['SOLANA_WS_URL']='wss://mainnet.helius-rpc.com/?api-key='+vault.quote(h,safe='')
    env['QSB_LIVE_ARM']='NO'
    return subprocess.call([sys.executable,'-m',
        'qseries_v2.oracle_execution.solana_atomic_executor.oracle189_balance_reverse_evidence','--worker'],env=env)

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--run',action='store_true');g.add_argument('--worker',action='store_true')
    a=p.parse_args()
    if a.test:test()
    elif a.run:sys.exit(run())
    else:worker()
