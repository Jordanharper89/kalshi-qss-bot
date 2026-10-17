"""ORACLE-133 existing native atomic runtime preflight, watch/simulate ONLY."""
import argparse,ast,os,subprocess,sys
from pathlib import Path
P=Path('qseries_v2/oracle_execution/solana_atomic_executor/runtime.py')
def verify():
    if not P.is_file():raise SystemExit('[HOLD] canonical executor missing')
    found={}
    for node in ast.parse(P.read_text(encoding='utf-8')).body:
        if isinstance(node,ast.Assign):
            for t in node.targets:
                if isinstance(t,ast.Name) and t.id in ('EXECUTION_AUTHORITY','PAPER_ONLY','FAST_SIZES','EXPAND_SIZES'):
                    found[t.id]=ast.literal_eval(node.value)
    if not(found.get('EXECUTION_AUTHORITY') is False and found.get('PAPER_ONLY') is True and found.get('FAST_SIZES')==(0.05,) and found.get('EXPAND_SIZES')==()):
        raise SystemExit('[HOLD] executable size/authority mismatch: '+repr(found))
    print('[PASS] Native executor preflight configured for 0.050 SOL ONLY; broadcast disabled')
    print('[LIMIT] Native runtime reverse attack and signed transaction certification remain unverified')
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seconds',type=float,default=90.)
    ap.add_argument('--verify-only',action='store_true')
    a=ap.parse_args()
    verify()
    if a.verify_only:return 0
    if not 1<=a.seconds<=600:raise SystemExit('[HOLD] preflight seconds must be 1..600')
    env=os.environ.copy()
    for k in list(env):
        if any(x in k.upper() for x in ('PRIVATE_KEY','SECRET_KEY','MNEMONIC','SEED_PHRASE')):
            env.pop(k,None)
    env['ORACLE_EXECUTION_AUTHORITY']='FALSE'
    env['QSB_PAPER_ONLY']='TRUE'
    print('[PREFLIGHT] Native simulation path only; no live broadcast',flush=True)
    return subprocess.call([sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.runtime','--seconds',str(a.seconds)],env=env)
if __name__=='__main__':raise SystemExit(main())
