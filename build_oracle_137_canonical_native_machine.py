"""ORACLE-137 full installer: single canonical native simulation machine.
No wallet signing or broadcast, no claim of risk-free or live-money execution.
"""
from __future__ import annotations
import ast, os, sys, subprocess, tempfile, textwrap, unittest
from pathlib import Path
R=Path.cwd()
P=R/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker'
N=R/'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
Q=R/'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'
H=R/'qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/live_account_stream.py'
M=R/'qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/qarb_043b_paced_mriya_token_discovery.py'
TARGET=R/'oracle137_canonical_native_machine.py'
BODY=r'''"""ORACLE-137 canonical WS+native v0 atomic simulation machine; never broadcasts."""
from __future__ import annotations
import argparse, ast, os, subprocess, sys, time, threading
from pathlib import Path
ROOT=Path(__file__).resolve().parent
NATIVE='qseries_v2.oracle_execution.solana_atomic_executor.runtime'
MRIYA='qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_043b_paced_mriya_token_discovery'
REPL='qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker.oracle129_replenish'

def guard():
    path=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
    t=ast.parse(path.read_text(encoding='utf8'))
    flags={}
    for node in t.body:
        if isinstance(node,ast.Assign):
            for x in node.targets:
                if isinstance(x,ast.Name) and x.id in ('EXECUTION_AUTHORITY','PAPER_ONLY','REAL_MONEY_MOVED','FAST_SIZES','EXPAND_SIZES'):
                    try:flags[x.id]=ast.literal_eval(node.value)
                    except Exception:flags[x.id]='DYNAMIC'
    expected={'EXECUTION_AUTHORITY':False,'PAPER_ONLY':True,'REAL_MONEY_MOVED':False,'FAST_SIZES':(0.05,), 'EXPAND_SIZES':()}
    for k,v in expected.items():
        if flags.get(k)!=v:raise RuntimeError('HOLD_CANONICAL_GUARD_'+k+':'+str(flags.get(k)))
    src=path.read_text(encoding='utf8')
    if 'def attack(' not in src or 'def serve_canonical(' not in src or 'def run(' not in src:
        raise RuntimeError('HOLD_NATIVE_CHAIN_NOT_FOUND')
    if 'CANONICAL_POSITIVE_HOLD' not in src:
        raise RuntimeError('HOLD_REVERSE_BEHAVIOR_CHANGED')
    return flags

def env():
    e=os.environ.copy()
    for k in list(e):
        if any(w in k.upper() for w in ('PRIVATE_KEY','MNEMONIC','SECRET_KEY','SEED_PHRASE')):
            e.pop(k,None)
    e['ORACLE_EXECUTION_AUTHORITY']='FALSE'
    e['QSB_PAPER_ONLY']='TRUE'
    e['QARB_HOT_PAIRS']='12'
    e['QARB_MAX_ACCOUNTS']='384'
    return e

def test():
    f=guard()
    e=env()
    assert e['QARB_HOT_PAIRS']=='12'
    assert 'QSB_SOLANA_PRIVATE_KEY' not in e
    assert f['FAST_SIZES']==(0.05,)
    print('[TEST PASS] native executor guards 0.050, no signer, no second pricing scanner',flush=True)

def run(seconds):
    guard()
    e=env()
    print('[ORACLE137] CANONICAL_NATIVE_WS_PRICE_COMPILE_SIM',flush=True)
    print('[SOURCE] existing repository native runtime.run / serve_canonical / attack',flush=True)
    print('[PATH] startup hydration -> one WS pricing engine -> native v0 compile -> signed simulation gate',flush=True)
    print('[SIZE] 0.050_SOL_ONLY; reverse direction scan allowed but native reverse attack remains HOLD',flush=True)
    print('[DISCOVERY] 180s auxiliary worker; continuous Mriya WS; no duplicate legacy QARB price runtime',flush=True)
    print('[SAFETY] READ_ONLY no signing with wallet, no broadcast, no financial outcome guaranteed',flush=True)
    tasks=[]
    def launch(mod,extra=()):
        p=subprocess.Popen([sys.executable,'-m',mod,*extra],cwd=str(ROOT),env=e)
        tasks.append(p)
        return p
    mriya=launch(MRIYA)
    # Start background 180s discovery only after native templates have time to hydrate.
    stop=threading.Event()
    def auxiliary():
        if not stop.wait(45):
            launch(REPL)
    th=threading.Thread(target=auxiliary,daemon=True)
    th.start()
    try:
        native=launch(NATIVE,('--seconds',str(seconds)))
        return native.wait()
    finally:
        stop.set()
        for p in tasks:
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=3)
                except subprocess.TimeoutExpired:p.kill();p.wait()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--test',action='store_true')
    p.add_argument('--seconds',type=int,default=3600)
    a=p.parse_args()
    if not 30<=a.seconds<=86400:raise SystemExit('HOLD_INVALID_DURATION')
    if a.test:test();return 0
    return run(a.seconds)
if __name__=='__main__':raise SystemExit(main())
'''
def values(src):
    out={}
    for node in ast.parse(src).body:
        if isinstance(node,ast.Assign):
            for t in node.targets:
                if isinstance(t,ast.Name) and t.id in ('FAST_SIZES','EXPAND_SIZES','EXECUTION_AUTHORITY','PAPER_ONLY','REAL_MONEY_MOVED'):
                    try:out[t.id]=ast.literal_eval(node.value)
                    except Exception:out[t.id]='DYNAMIC'
    return out

def main():
    required=(P,N,Q,H,M,P/'oracle129_replenish.py')
    for p in required:
        if not p.exists():raise SystemExit('[HOLD] Missing '+str(p))
    for p in (N,Q):
        v=values(p.read_text(encoding='utf8'))
        for k,x in {'FAST_SIZES':(.05,),'EXPAND_SIZES':(),'EXECUTION_AUTHORITY':False,'PAPER_ONLY':True}.items():
            if v.get(k)!=x:raise SystemExit('[HOLD] '+p.name+' mismatch '+k+'='+str(v.get(k)))
    n=N.read_text(encoding='utf8')
    for seam in ('def attack(', 'def serve_canonical(', 'def canonical_price(', 'def run('):
        if seam not in n:raise SystemExit('[HOLD] Missing native seam '+seam)
    if 'CANONICAL_POSITIVE_HOLD' not in n:raise SystemExit('[HOLD] Reverse boundary changed')
    rep=(P/'oracle129_replenish.py').read_text(encoding='utf8')
    if 'time.sleep(max(0,180-' not in rep:raise SystemExit('[HOLD] 180s auxiliary cadence missing')
    ast.parse(BODY)
    backup=TARGET.read_bytes() if TARGET.exists() else None
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=R,delete=False,suffix='.tmp') as f:
        f.write(BODY);tmp=Path(f.name)
    try:
        os.replace(tmp,TARGET)
        c=subprocess.run([sys.executable,str(TARGET),'--test'],cwd=str(R),capture_output=True,text=True,timeout=20)
        if c.returncode:raise RuntimeError('ORACLE137_TEST_FAILED '+(c.stdout+c.stderr)[-1200:])
        print(c.stdout.strip())
    except BaseException:
        if backup is not None:TARGET.write_bytes(backup)
        else:TARGET.unlink(missing_ok=True)
        raise
    print('[INSTALL PASS] ORACLE-137 single canonical native machine',flush=True)
    print('[PRESERVED] original price math, native assembly and unsigned/simulation chain',flush=True)
    print('[GATE] no live sending, no wallet key, reverse execution not certified',flush=True)
    print('[RUN] python oracle137_canonical_native_machine.py --seconds 3600',flush=True)
if __name__=='__main__':main()
