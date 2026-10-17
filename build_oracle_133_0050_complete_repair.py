"""ORACLE-133: full 0.050-SOL scanner / positive-handoff / native preflight repair.
Windows CMD only: python build_oracle_133_0050_complete_repair.py
No private keys, no signing, no broadcast. Scanner and 180-second replenishment untouched.
"""
from __future__ import annotations
import ast
import os
import pathlib
import shutil
import tempfile

ROOT = pathlib.Path.cwd()
Q20 = ROOT/'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'
EX = ROOT/'qseries_v2/oracle_execution/solana_atomic_executor/runtime.py'
RUNNER = ROOT/'oracle131_native_executor_preflight.py'
TARGET = 0.05

RUNNER_CODE = '''"""ORACLE-133 existing native atomic runtime preflight, watch/simulate ONLY."""
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
'''

def top_assignments(source):
    found={}
    for n in ast.parse(source).body:
        if isinstance(n,ast.Assign):
            for t in n.targets:
                if isinstance(t,ast.Name) and t.id in ('FAST_SIZES','EXPAND_SIZES','PREFERRED_SIZE_SOL','EXECUTION_AUTHORITY','PAPER_ONLY'):
                    found[t.id]=(ast.literal_eval(n.value),n)
    return found

def patch_size(source, preferred):
    entries=top_assignments(source)
    needed=['FAST_SIZES','EXPAND_SIZES']+(['PREFERRED_SIZE_SOL'] if preferred else [])
    for k in needed:
        if k not in entries:raise RuntimeError('HOLD_MISSING_'+k)
    if entries.get('EXECUTION_AUTHORITY',(None,))[0] is not False:raise RuntimeError('HOLD_EXECUTION_AUTHORITY')
    if entries.get('PAPER_ONLY',(None,))[0] is not True:raise RuntimeError('HOLD_PAPER_ONLY')
    if not isinstance(entries['FAST_SIZES'][0],tuple):raise RuntimeError('HOLD_SIZE_CURVE')
    if not isinstance(entries['EXPAND_SIZES'][0],tuple):raise RuntimeError('HOLD_EXPAND_CURVE')
    values={'FAST_SIZES':'(0.050,)','EXPAND_SIZES':'()','PREFERRED_SIZE_SOL':'0.050'}
    lines=source.splitlines(keepends=True)
    for k in sorted(needed,key=lambda x:entries[x][1].lineno,reverse=True):
        n=entries[k][1]
        lines[n.lineno-1:n.end_lineno]=[k+'='+values[k]+'\n']
    return ''.join(lines)

def patch_q20(source):
    source=patch_size(source,True)
    old="if abs(row['size_sol'] - 0.010) > 1e-10:"
    new="if abs(row['size_sol'] - 0.050) > 1e-10:"
    if old in source:
        if source.count(old)!=1:raise RuntimeError('HOLD_AMBIGUOUS_129_FILTER')
        source=source.replace(old,new)
    if new not in source or source.count('def _o129_offer(')!=1:
        raise RuntimeError('HOLD_MISSING_CANDIDATE_HANDOFF')
    if '_o129_offer(token,snap,slot,received_ns,best)' not in source:
        raise RuntimeError('HOLD_MISSING_HOT_POSITIVE_FORWARD')
    return source

def verify(q,e,r):
    a,b=top_assignments(q),top_assignments(e)
    for values in (a,b):
        if values['FAST_SIZES'][0]!=(TARGET,) or values['EXPAND_SIZES'][0]!=():raise RuntimeError('HOLD_SIZE_NOT_0050')
        if values['EXECUTION_AUTHORITY'][0] is not False or values['PAPER_ONLY'][0] is not True:raise RuntimeError('HOLD_UNSAFE_FLAGS')
    if a['PREFERRED_SIZE_SOL'][0]!=TARGET:raise RuntimeError('HOLD_PREFERRED_SIZE')
    if "if abs(row['size_sol'] - 0.050) > 1e-10:" not in q:raise RuntimeError('HOLD_HANDOFF_SIZE')
    if "found.get('FAST_SIZES')==(0.05,)" not in r:raise RuntimeError('HOLD_PREFLIGHT_SIZE')
    for s in (q,e,r):ast.parse(s)

def atomic_write(p,s):
    with tempfile.NamedTemporaryFile('w',dir=p.parent,encoding='utf-8',delete=False,prefix='.oracle133_',suffix='.tmp') as f:
        f.write(s);temporary=pathlib.Path(f.name)
    try:os.replace(temporary,p)
    finally:temporary.unlink(missing_ok=True)

def tests():
    q="EXECUTION_AUTHORITY=False\nPAPER_ONLY=True\nPREFERRED_SIZE_SOL=0.010\nFAST_SIZES=(0.010,)\nEXPAND_SIZES=()\ndef _o129_offer():pass\n# _o129_offer(token,snap,slot,received_ns,best)\nif abs(row['size_sol'] - 0.010) > 1e-10:pass\n"
    e="EXECUTION_AUTHORITY=False\nPAPER_ONLY=True\nFAST_SIZES=(0.010,)\nEXPAND_SIZES=()\n"
    assert patch_q20(patch_q20(q))==patch_q20(q)
    assert patch_size(patch_size(e,False),False)==patch_size(e,False)
    verify(patch_q20(q),patch_size(e,False),RUNNER_CODE)
    for unsafe in ['EXECUTION_AUTHORITY=True','PAPER_ONLY=False']:
        try:patch_size(e.replace('EXECUTION_AUTHORITY=False' if 'AUTHORITY' in unsafe else 'PAPER_ONLY=True',unsafe),False)
        except RuntimeError:pass
        else:raise AssertionError('unsafe accepted')
    print('[TEST PASS] ORACLE-133 exact size, candidate gate, idempotence, safety')

def main():
    tests()
    for p in (Q20,EX):
        if not p.is_file():raise SystemExit('[HOLD] Missing required source: '+str(p))
    original={p:p.read_text(encoding='utf-8') for p in (Q20,EX)}
    # Create the missing preflight without needing an earlier installer.
    runner_old=RUNNER.read_text(encoding='utf-8') if RUNNER.exists() else None
    updated={Q20:patch_q20(original[Q20]),EX:patch_size(original[EX],False),RUNNER:RUNNER_CODE}
    verify(updated[Q20],updated[EX],updated[RUNNER])
    old={**original,RUNNER:runner_old}
    for p,s in old.items():
        if s is not None and s!=updated[p]:
            backup=p.with_name(p.name+'.oracle133.bak')
            if not backup.exists():shutil.copy2(p,backup)
    written=[]
    try:
        for p,s in updated.items():
            if old[p]!=s:atomic_write(p,s);written.append(p)
        verify(Q20.read_text(encoding='utf-8'),EX.read_text(encoding='utf-8'),RUNNER.read_text(encoding='utf-8'))
    except BaseException:
        for p in reversed(written):
            if old[p] is None:p.unlink(missing_ok=True)
            else:atomic_write(p,old[p])
        raise
    print('[INSTALL PASS] ORACLE-133 installed AND verified on disk')
    print('[SCANNER] Q25/Q20 original WebSocket; FAST_SIZES=(0.050,); no expansion')
    print('[HANDOFF] Positive candidate filter=0.050 SOL; original positive journal intact')
    print('[EXECUTOR] Canonical native simulator fixed 0.050 SOL; runner installed')
    print('[PRESERVED] Existing Mriya/universal 180s discovery; no scanner or lifecycle replacement')
    print('[GUARD] WATCH ONLY; NO LIVE SIGNING; NO BROADCAST')
    print('[NEXT] python oracle131_native_executor_preflight.py --verify-only')
    print('[RUN] python oracle120_credentials.py --run')
if __name__=='__main__':main()
