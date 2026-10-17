"""ORACLE-139 complete installer. Native executor simulation, deny broadcast RPC."""
from __future__ import annotations
import ast, os, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path.cwd()
N=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
Q=ROOT/'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'
W=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle129_replenish.py'
OUT=ROOT/'oracle139_guarded_native_machine.py'
BOOT=r'''"""ORACLE-139. Mainnet native simulation, always deny broadcasting."""
from __future__ import annotations
import argparse, ast, os, subprocess, sys, threading
from pathlib import Path
ROOT=Path(__file__).resolve().parent
N=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
W=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle129_replenish.py'
DENY={'sendtransaction','sendrawtransaction','sendencodedtransaction','requestairdrop'}

def assignments(src):
    result={}
    for node in ast.parse(src).body:
        if isinstance(node,ast.Assign):
            for key in node.targets:
                if isinstance(key,ast.Name):
                    try:result[key.id]=ast.literal_eval(node.value)
                    except (ValueError,TypeError,KeyError):pass
    return result

def check():
    if not N.is_file():raise RuntimeError('HOLD_NO_NATIVE_RUNTIME')
    src=N.read_text(encoding='utf8'); tree=ast.parse(src)
    v=assignments(src)
    for k,expected in {'EXECUTION_AUTHORITY':False,'PAPER_ONLY':True,'REAL_MONEY_MOVED':False,'FAST_SIZES':(.05,),'EXPAND_SIZES':()}.items():
        if v.get(k)!=expected:raise RuntimeError('HOLD_NATIVE_CONFIG_'+k+':'+str(v.get(k)))
    funcs={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    if not {'attack','serve_canonical','canonical_price','run'}<=funcs:raise RuntimeError('HOLD_NATIVE_CHAIN_INCOMPLETE')
    if not W.exists() or 'time.sleep(max(0,180-' not in W.read_text(encoding='utf8'):
        raise RuntimeError('HOLD_180_SECOND_CADENCE')
    # Detect opaque direct broadcast transports rather than hiding them behind a keyword check.
    # The supported native path uses q87.c.rpc(method, ...), which is denied at runtime.
    unknown=[]
    for n in ast.walk(tree):
        if not isinstance(n,ast.Call):continue
        f=n.func
        name=f.id if isinstance(f,ast.Name) else f.attr if isinstance(f,ast.Attribute) else ''
        if name.lower() in {'sendtransaction','sendrawtransaction','sendencodedtransaction','send_transaction','send_raw_transaction'}:
            unknown.append(name)
    if unknown:raise RuntimeError('HOLD_UNGUARDED_SEND_CALL:'+','.join(sorted(set(unknown))))
    return v

def scrub():
    for k in tuple(os.environ):
        if any(x in k.upper() for x in ('PRIVATE_KEY','SECRET_KEY','MNEMONIC','SEED_PHRASE','KEYPAIR')):
            os.environ.pop(k,None)
    os.environ['ORACLE_EXECUTION_AUTHORITY']='FALSE'
    os.environ['QSB_PAPER_ONLY']='TRUE'
    os.environ['QARB_HOT_PAIRS']='12'
    os.environ['QARB_MAX_ACCOUNTS']='384'

def deny_rpc():
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    original=core.rpc
    def restricted(method,*args,**kwargs):
        if str(method).replace('_','').lower() in DENY:
            raise RuntimeError('ORACLE139_BLOCK_BROADCAST_RPC')
        return original(method,*args,**kwargs)
    core.rpc=restricted
    return core

def test():
    v=check();scrub();core=deny_rpc()
    try:
        core.rpc('sendTransaction',[])
    except RuntimeError as exc:
        assert str(exc)=='ORACLE139_BLOCK_BROADCAST_RPC'
    else:raise AssertionError('SEND_NOT_BLOCKED')
    assert v['FAST_SIZES']==(.05,)
    print('[TEST PASS] ORACLE139 size=0.050 rpc_send=DENIED native_chain=READY secrets=SCRUBBED',flush=True)

def run(seconds):
    check();scrub();deny_rpc()
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as native
    # All q87.c RPC references share the already patched core module.
    assert native.q87.c.rpc.__name__=='restricted','HOLD_RPC_PATCH_NOT_ATTACHED'
    env=os.environ.copy()
    proc=subprocess.Popen([sys.executable,'-m','qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_043b_paced_mriya_token_discovery'],cwd=str(ROOT),env=env)
    stop=threading.Event();worker=[]
    def auxiliary():
        if not stop.wait(45):
            p=subprocess.Popen([sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker.oracle129_replenish'],cwd=str(ROOT),env=env)
            worker.append(p)
    threading.Thread(target=auxiliary,daemon=True).start()
    print('[ORACLE139] CANONICAL_NATIVE_WS_PRICE_COMPILE_SIM',flush=True)
    print('[SCOPE] one native pricing engine; 0.050 SOL; 180s discovery; RPC broadcasts denied',flush=True)
    try:return native.run(float(seconds))
    finally:
        stop.set()
        for p in [proc,*worker]:
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=3)
                except subprocess.TimeoutExpired:p.kill();p.wait()

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true');p.add_argument('--seconds',type=int,default=3600)
    a=p.parse_args()
    if not 30<=a.seconds<=86400:raise SystemExit('HOLD_DURATION')
    if a.test:test();return 0
    return run(a.seconds)
if __name__=='__main__':raise SystemExit(main())
'''
def main():
    for p in (N,Q,W):
        if not p.exists():raise SystemExit('[HOLD] Missing '+str(p))
    ast.parse(BOOT)
    original=OUT.read_bytes() if OUT.exists() else None
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=ROOT,delete=False,suffix='.tmp') as f:
        f.write(BOOT);temp=Path(f.name)
    try:
        os.replace(temp,OUT)
        r=subprocess.run([sys.executable,str(OUT),'--test'],cwd=ROOT,capture_output=True,text=True,timeout=30)
        if r.returncode:raise RuntimeError((r.stdout+r.stderr)[-1600:])
        print(r.stdout.strip(),flush=True)
    except BaseException as exc:
        if original is None:OUT.unlink(missing_ok=True)
        else:OUT.write_bytes(original)
        raise SystemExit('[HOLD] ORACLE139 installation rolled back: '+str(exc))
    print('[INSTALL PASS] ORACLE139 guarded canonical native machine',flush=True)
    print('[RUN] python oracle139_guarded_native_machine.py --seconds 3600',flush=True)
if __name__=='__main__':main()
