"""Reuse production sell preloader in isolated simulation, without scanner."""
import argparse, inspect, os, subprocess, sys
from . import runtime as r
from . import oracle188_route_and_sim_evidence as q188

def load_stored():
    import build_oracle_182_secure_windows_credentials as vault
    db=vault.api(); helius=vault.load(db,vault.HELIUS)
    wallet=vault.load(db,vault.SOLANA)
    if not helius or not wallet:raise RuntimeError('ORACLE190_CREDENTIALS_MISSING')
    env=os.environ.copy()
    env['QSB_SOLANA_PRIVATE_KEY']=wallet
    env['SOLANA_RPC_URL']='https://mainnet.helius-rpc.com/?api-key='+vault.quote(helius,safe='')
    env['SOLANA_WS_URL']='wss://mainnet.helius-rpc.com/?api-key='+vault.quote(helius,safe='')
    env['QSB_LIVE_ARM']='NO'
    return subprocess.call([sys.executable,'-m',
        'qseries_v2.oracle_execution.solana_atomic_executor.oracle190_reverse_preload_balance',
        '--worker'],env=env)

def call_existing(fn,state,user,warmed):
    signature=inspect.signature(fn)
    resolved=[]; kw={}
    values={'state':state,'user':user,'wallet':user,'payer':user,
            'warmed_rows':warmed,'token_warm':warmed,'warmed':warmed,
            'warm_rows':warmed,'programs':warmed}
    for p in signature.parameters.values():
        if p.kind in (p.VAR_POSITIONAL,p.VAR_KEYWORD):
            raise RuntimeError('ORACLE190_UNSUPPORTED_PRELOADER_SIGNATURE')
        if p.name not in values:
            if p.default is not p.empty:continue
            raise RuntimeError('ORACLE190_UNKNOWN_PRELOADER_PARAMETER')
        if p.kind in (p.POSITIONAL_ONLY,p.POSITIONAL_OR_KEYWORD):
            resolved.append(values[p.name])
        elif p.kind==p.KEYWORD_ONLY:kw[p.name]=values[p.name]
    return fn(*resolved,**kw)

def worker():
    if os.environ.get('QSB_LIVE_ARM','').upper()=='YES':
        raise RuntimeError('ORACLE190_LIVE_ARM_REFUSED')
    if not callable(getattr(r,'_live_010_armed',None)) or r._live_010_armed():
        raise RuntimeError('ORACLE190_DISARM_NOT_CERTIFIED')
    preloader=getattr(r,'prebuild_sell_templates',None)
    if not callable(preloader):raise RuntimeError('ORACLE190_SELL_PRELOADER_MISSING')
    old_meteora=r.prebuild_meteora_templates
    old_refresh=r.BLOCKHASH.refresh
    context={}; invoked=[False]
    def capture(state,user,warmed,*a,**kw):
        result=old_meteora(state,user,warmed,*a,**kw)
        context.update(state=state,user=user,warmed=warmed)
        return result
    def finish_warm():
        if not invoked[0]:
            if len(context)!=3:raise RuntimeError('ORACLE190_WARM_CONTEXT_MISSING')
            invoked[0]=True
            call_existing(preloader,context['state'],context['user'],context['warmed'])
            ready=getattr(r,'SELL_TEMPLATES',None)
            if not isinstance(ready,dict) or not ready:
                raise RuntimeError('ORACLE190_REVERSE_PRELOAD_EMPTY')
            eligible=set(ready).intersection(getattr(r,'READY_TOKENS',set()))
            print('[ORACLE190_REVERSE_PRELOAD] total=%d ready=%d broadcast=FALSE' %
                  (len(ready),len(eligible)),flush=True)
            if not eligible:raise RuntimeError('ORACLE190_NO_READY_SELL_TEMPLATES')
            try:
                result=r.q87.c.rpc('getBalance',[context['user'],{'commitment':'processed'}])
                lamports=result.get('value') if isinstance(result,dict) else None
                if not isinstance(lamports,int):raise ValueError('invalid balance')
                spare=lamports-50_000_000
                print('[ORACLE190_SOL_HEADROOM] balance_lamports=%d trade_lamports=50000000 spare_lamports=%d additional_rent_fees_unverified=TRUE' %
                      (lamports,spare),flush=True)
                if spare<=0:print('[ORACLE190_SOL_HOLD] NEEDS_TRADE_PLUS_RENT_AND_FEES',flush=True)
            except Exception as exc:
                print('[ORACLE190_BALANCE_HOLD] type=%s' % type(exc).__name__,flush=True)
        return old_refresh()
    r.prebuild_meteora_templates=capture
    r.BLOCKHASH.refresh=finish_warm
    try:q188.run()
    finally:
        r.prebuild_meteora_templates=old_meteora
        r.BLOCKHASH.refresh=old_refresh
    if not invoked[0]:raise RuntimeError('ORACLE190_PRELOADER_NOT_INVOKED')

def test():
    calls=[]
    def example(state,user,warmed_rows):calls.append((state,user,warmed_rows))
    call_existing(example,'S','U','W')
    assert calls==[('S','U','W')]
    def invalid(state,unrecognized):pass
    try:call_existing(invalid,1,2,3)
    except RuntimeError as exc:assert str(exc)=='ORACLE190_UNKNOWN_PRELOADER_PARAMETER'
    else:raise AssertionError('unknown argument accepted')
    print('[TEST PASS] ORACLE190 existing sell-preloader binding and fail-closed',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser();g=a.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--run',action='store_true')
    g.add_argument('--worker',action='store_true');v=a.parse_args()
    test() if v.test else sys.exit(load_stored()) if v.run else worker()
