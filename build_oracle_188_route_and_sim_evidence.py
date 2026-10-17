
"""ORACLE188 complete diagnostic installer; never alters live executor."""
import argparse, ast
from pathlib import Path
ROOT=Path('qseries_v2/oracle_execution/solana_atomic_executor')
DEST=ROOT/'oracle188_route_and_sim_evidence.py'
CODE=r'''"""Disarmed ORACLE187 diagnostic with safe route and simulation evidence."""
import argparse, re, traceback
from . import runtime as r
from . import oracle187_isolated_rpc_cooldown as q187

ALLOWED=('DIRECTION','NOT','CERTIFIED','TO','REVERSE','METEORA','PUMP','ROUTE',
         'TEMPLATE','MISSING','TOKEN','POOL','SNAPSHOT','BOUND',
         'SLIPPAGE','INSUFFICIENT','BALANCE','AMOUNT','INVALID',
         'ACCOUNT','SIGNER','WALLET','QUOTE','START','LENGTH',
         'UNSUPPORTED','NO','ATA','ALT','BIN','ARRAY','SIM','HOT')

def label(exc):
    parts=re.findall(r'[A-Z][A-Z0-9_]{2,70}',str(exc))
    good=[]
    for word in parts:
        if all(x in ALLOWED for x in word.split('_')):
            good.append(word)
    return '|'.join(good[:5]) or 'UNCLASSIFIED_RUNTIME_ERROR'

def trace_route(fn):
    def wrapped(*args,**kwargs):
        direction='UNKNOWN'
        if len(args)>2 and isinstance(args[2],dict):
            direction=str(args[2].get('direction','UNKNOWN'))
        try:return fn(*args,**kwargs)
        except Exception as exc:
            tb=traceback.extract_tb(exc.__traceback__)
            funcs=[x.name for x in tb if x.name.isidentifier()]
            print('[ORACLE188_REVERSE_CAUSE] direction=%s category=%s type=%s function=%s broadcast=FALSE' %
                  (direction,label(exc),type(exc).__name__,funcs[-1] if funcs else 'UNKNOWN'),flush=True)
            raise
    return wrapped

def trace_sim(fn):
    def wrapped(*args,**kwargs):
        result=fn(*args,**kwargs)
        if not isinstance(result,dict):
            print('[ORACLE188_SIM_EVIDENCE] INVALID_RESULT broadcast=FALSE',flush=True)
            return result
        err=result.get('err');logs=result.get('logs') or []
        if err is not None:
            # Only program-originated diagnostic tags; never print arbitrary log content.
            tags=[]
            for line in logs:
                t=str(line).lower()
                if 'instruction:' in t:
                    name=re.search(r'instruction:\s*([a-z0-9_]+)',t)
                    if name:tags.append('IX_'+name.group(1).upper()[:35])
                if 'insufficient funds' in t:tags.append('INSUFFICIENT_FUNDS')
                if 'slippage' in t:tags.append('SLIPPAGE')
                if 'custom program error' in t:tags.append('CUSTOM_PROGRAM_ERROR')
                if 'owner mismatch' in t:tags.append('OWNER_MISMATCH')
                if 'anchorerror' in t:
                    code=re.search(r'error code:\s*([a-z0-9_]+)',t)
                    tags.append('ANCHOR_'+code.group(1).upper()[:35] if code else 'ANCHOR_ERROR')
                if 'transfer' in t and 'failed' in t:tags.append('TOKEN_TRANSFER_FAILED')
            unique=list(dict.fromkeys(tags))[-20:]
            print('[ORACLE188_SIM_EVIDENCE] error=%s instruction=%s custom=%s units=%s program_tags=%s broadcast=FALSE' %
                  ('InstructionError' if isinstance(err,dict) and 'InstructionError' in err else type(err).__name__,
                   (err.get('InstructionError') or ['NA'])[0] if isinstance(err,dict) and isinstance(err.get('InstructionError'),list) else 'NA',
                   (err.get('InstructionError') or [None,{}])[1].get('Custom','NA') if isinstance(err,dict) and isinstance(err.get('InstructionError'),list) and len(err['InstructionError'])>1 and isinstance(err['InstructionError'][1],dict) else 'NA',
                   result.get('units'),','.join(unique) or 'NO_CLASSIFIABLE_LOGS'),flush=True)
        return result
    return wrapped

def run():
    old_route=r.same_snapshot_route;old_sim=r.simulate_current
    r.same_snapshot_route=trace_route(old_route)
    r.simulate_current=trace_sim(old_sim)
    try:q187.run()
    finally:
        r.same_snapshot_route=old_route
        r.simulate_current=old_sim

def test():
    try:trace_route(lambda *a: (_ for _ in ()).throw(RuntimeError('DIRECTION_NOT_CERTIFIED:METEORA_TO_PUMP')))(None,None,{'direction':'METEORA_TO_PUMP'})
    except RuntimeError:pass
    else:raise AssertionError('route exception swallowed')
    assert label(RuntimeError('DIRECTION_NOT_CERTIFIED:METEORA_TO_PUMP'))=='DIRECTION_NOT_CERTIFIED|METEORA_TO_PUMP'
    assert label(RuntimeError('api-key=SECRET123'))=='UNCLASSIFIED_RUNTIME_ERROR'
    trace_sim(lambda *a:{'err':{'InstructionError':[2,{'Custom':1}]},'units':100,'logs':['Program log: Instruction: Swap2','Program failed: custom program error']})()
    print('[TEST PASS] ORACLE188 reverse reason and sanitized simulation tags; no broadcast')

if __name__=='__main__':
    p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
    g.add_argument('--test',action='store_true');g.add_argument('--run',action='store_true')
    a=p.parse_args();test() if a.test else run()
'''
def test():
    ast.parse(CODE)
    assert 'q187.run()' in CODE and 'ORACLE188_REVERSE_CAUSE' in CODE
    print('[INSTALLER TEST PASS] ORACLE188 parses; 187 cooldown retained')
def install():
    for f in ('runtime.py','oracle187_isolated_rpc_cooldown.py'):
        if not (ROOT/f).is_file():raise RuntimeError('HOLD_ORACLE188_MISSING_'+f)
    if DEST.exists() and DEST.read_text(encoding='utf-8')!=CODE:
        raise RuntimeError('HOLD_ORACLE188_EXISTING_MODULE_DIFFERS')
    DEST.write_text(CODE,encoding='utf-8');ast.parse(DEST.read_text(encoding='utf-8'))
    print('[INSTALL PASS] ORACLE188 stage evidence; production runtime and scanner untouched')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--test',action='store_true')
    a=p.parse_args();test() if a.test else install()
