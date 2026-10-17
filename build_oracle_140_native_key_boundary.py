"""ORACLE-140 full installer: preserve native-only signer identity; isolate discovery; deny sends."""
from __future__ import annotations
import ast, os, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path.cwd()
OUT=ROOT/'oracle140_native_simulation_machine.py'
BOOT=r'''"""ORACLE-140 canonical native simulation launcher. No broadcast authority."""
from __future__ import annotations
import argparse, ast, os, subprocess, sys, threading
from pathlib import Path
ROOT=Path(__file__).resolve().parent
N=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
W=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/oracle105_sdk_worker/oracle129_replenish.py'
DENIED={'sendtransaction','sendrawtransaction','sendencodedtransaction','requestairdrop'}
SECRET_HINTS=('PRIVATE_KEY','SECRET_KEY','MNEMONIC','SEED_PHRASE','KEYPAIR')

def config():
    if not N.is_file():raise RuntimeError('HOLD_NATIVE_RUNTIME_MISSING')
    t=ast.parse(N.read_text(encoding='utf8'))
    values={}
    for x in t.body:
        if isinstance(x,ast.Assign):
            for y in x.targets:
                if isinstance(y,ast.Name):
                    try:values[y.id]=ast.literal_eval(x.value)
                    except (ValueError,TypeError,KeyError):pass
    expected={'EXECUTION_AUTHORITY':False,'PAPER_ONLY':True,'REAL_MONEY_MOVED':False,'FAST_SIZES':(.05,),'EXPAND_SIZES':()}
    for k,v in expected.items():
        if values.get(k)!=v:raise RuntimeError('HOLD_NATIVE_CONFIG_'+k)
    f={x.name for x in t.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))}
    if not {'attack','serve_canonical','canonical_price','run'}<=f:raise RuntimeError('HOLD_NATIVE_PATH_INCOMPLETE')
    if not W.is_file() or 'time.sleep(max(0,180-' not in W.read_text(encoding='utf8'):
        raise RuntimeError('HOLD_DISCOVERY_CADENCE')
    # Direct non-core transaction transport is not certified.
    for x in ast.walk(t):
        if isinstance(x,ast.Call):
            f=x.func
            name=f.id if isinstance(f,ast.Name) else f.attr if isinstance(f,ast.Attribute) else ''
            if name.lower() in ('sendtransaction','sendrawtransaction','sendencodedtransaction','send_transaction','send_raw_transaction'):
                raise RuntimeError('HOLD_DIRECT_SEND_CALL')
    return True

def discovery_env():
    env={k:v for k,v in os.environ.items() if not any(h in k.upper() for h in SECRET_HINTS)}
    env['ORACLE_EXECUTION_AUTHORITY']='FALSE'
    env['QSB_PAPER_ONLY']='TRUE'
    return env

def deny_sends():
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    rpc,send,http=core.rpc,core.send,core.http
    def restricted_rpc(method,*args,**kw):
        if str(method).replace('_','').lower() in DENIED:raise RuntimeError('ORACLE140_BROADCAST_DENIED')
        return rpc(method,*args,**kw)
    def restricted_send(*args,**kw):raise RuntimeError('ORACLE140_BROADCAST_DENIED')
    def restricted_http(*args,**kw):
        # Reject JSON-RPC sends even if caller bypasses core.rpc and directly invokes core.http.
        body=args[2] if len(args)>2 else kw.get('data',kw.get('body'))
        if isinstance(body,dict) and str(body.get('method','')).replace('_','').lower() in DENIED:
            raise RuntimeError('ORACLE140_BROADCAST_DENIED')
        return http(*args,**kw)
    core.rpc=restricted_rpc
    core.send=restricted_send
    core.http=restricted_http
    return core

def test():
    config()
    env=discovery_env()
    assert not any(any(h in k.upper() for h in SECRET_HINTS) for k in env)
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core
    deny_sends()
    for fn in (lambda:core.rpc('sendTransaction',[]),lambda:core.send(b''),lambda:core.http('https://unused','POST',{'method':'sendTransaction'})):
        try:fn()
        except RuntimeError as e:assert str(e)=='ORACLE140_BROADCAST_DENIED'
        else:raise RuntimeError('HOLD_SEND_GATE_TEST')
    print('[TEST PASS] ORACLE140 size=0.050 native_secret_preserved broadcast=DENIED auxiliary_secrets=SCRUBBED',flush=True)

def run(seconds):
    config()
    # IMPORTANT: do not pop or mutate the user's private-key variable.
    # The local native runtime physically requires it to sign simulation packets.
    if not os.environ.get('QSB_SOLANA_PRIVATE_KEY','').strip():
        raise RuntimeError('HOLD_NATIVE_SIGNER_ENV_MISSING: QSB_SOLANA_PRIVATE_KEY must be available through the existing secure credential setup; value not logged')
    os.environ['ORACLE_EXECUTION_AUTHORITY']='FALSE'
    os.environ['QSB_PAPER_ONLY']='TRUE'
    os.environ['QARB_HOT_PAIRS']='12'
    os.environ['QARB_MAX_ACCOUNTS']='384'
    deny_sends()
    from qseries_v2.oracle_execution.solana_atomic_executor import runtime as native
    # Secondary confirmation that the native module uses the guarded core object.
    if native.q87.c.rpc.__name__!='restricted_rpc':raise RuntimeError('HOLD_RPC_INTERPOSITION')
    stop=threading.Event();children=[];env=discovery_env()
    def aux():
        # Start live native hydration first, avoiding immediate Mriya getTransaction backfill.
        if stop.wait(90):return
        try:
            p=subprocess.Popen([sys.executable,'-m','qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_043b_paced_mriya_token_discovery'],cwd=str(ROOT),env=env)
            children.append(p)
            if stop.wait(90):return
            p=subprocess.Popen([sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.oracle105_sdk_worker.oracle129_replenish'],cwd=str(ROOT),env=env)
            children.append(p)
        except Exception as exc:print('[ORACLE140_AUX_HOLD] '+type(exc).__name__,flush=True)
    threading.Thread(target=aux,name='oracle140-aux',daemon=True).start()
    print('[ORACLE140] NATIVE_SIMULATION_ENGINE 0.050_SOL',flush=True)
    print('[STARTUP] native-first; Mriya delay=90s; replenish delay=180s; replenish cadence=180s',flush=True)
    print('[MODE] no transactions broadcast; private-key available to local native simulation only',flush=True)
    try:return native.run(float(seconds))
    finally:
        stop.set()
        for p in list(children):
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=4)
                except subprocess.TimeoutExpired:p.kill();p.wait()

def main(argv=None):
    a=argparse.ArgumentParser();a.add_argument('--test',action='store_true');a.add_argument('--seconds',type=int,default=3600)
    v=a.parse_args(argv)
    if v.test:test();return 0
    if not 30<=v.seconds<=86400:raise SystemExit('HOLD_DURATION')
    return run(v.seconds)
if __name__=='__main__':raise SystemExit(main())
'''

def main():
    ast.parse(BOOT)
    old=OUT.read_bytes() if OUT.exists() else None
    with tempfile.NamedTemporaryFile('w',encoding='utf8',dir=ROOT,delete=False,suffix='.tmp') as f:
        f.write(BOOT);tmp=Path(f.name)
    try:
        os.replace(tmp,OUT)
        p=subprocess.run([sys.executable,str(OUT),'--test'],cwd=ROOT,capture_output=True,text=True,timeout=30)
        if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-1600:])
    except BaseException as exc:
        if old is None:OUT.unlink(missing_ok=True)
        else:OUT.write_bytes(old)
        raise SystemExit('[HOLD] ORACLE140 rolled back: '+str(exc))
    print(p.stdout.strip(),flush=True)
    print('[INSTALL PASS] ORACLE140 native key-boundary and startup-isolation launcher',flush=True)
    print('[RUN] python oracle140_native_simulation_machine.py --seconds 3600',flush=True)
if __name__=='__main__':main()
