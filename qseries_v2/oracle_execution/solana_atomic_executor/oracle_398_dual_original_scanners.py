from __future__ import annotations
import argparse, collections, contextlib, hashlib, json, os, re, runpy, subprocess, sys, threading, time
from pathlib import Path

ROOT=Path.cwd().resolve()
STATE=ROOT/'runtime_state/oracle/final_boss_dual'
ORIGINAL='qseries_v2.oracle_execution.oracle_025_single_hydration_exact_live_reuse'
CANONICAL=ROOT/'build_oracle_322_scanner_isolated_discovery.py'
Q18=ROOT/'qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py'
Q20=ROOT/'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'
Q25=ROOT/'qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py'
MODULE='qseries_v2.oracle_execution.solana_atomic_executor.oracle_398_dual_original_scanners'
GRID=tuple(i/1000 for i in range(10,101,5))
LAMPORTS=tuple(range(10_000_000,100_000_001,5_000_000))
PAIRS=28

def hashfile(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def source_manifest():
    rows={'canonical_launcher':hashfile(CANONICAL),'q18':hashfile(Q18),
          'q20':hashfile(Q20),'q25':hashfile(Q25)}
    package=ROOT/'qseries_v2/oracle_execution/solana_atomic_executor'
    optional=list(ROOT.glob('build_oracle_388*.py'))+list(package.glob('oracle_388_*.py'))+list(package.glob('oracle_322_*.py'))
    for path in sorted(optional):rows[str(path.relative_to(ROOT))]=hashfile(path)
    return rows

def check_sources(mode):
    paths=[Q18,Q20,Q25]+([CANONICAL] if mode=='canonical' else [])
    absent=[str(p.relative_to(ROOT)) for p in paths if not p.is_file()]
    if absent: raise RuntimeError('HOLD_MISSING_ORIGINAL_FILES:'+','.join(absent))
    frozen=STATE/'oracle_398_frozen_scanners.json'
    if frozen.is_file():
        expected=json.loads(frozen.read_text(encoding='utf-8'))['source_hashes']
        actual=source_manifest()
        if any(v and actual.get(k)!=v for k,v in expected.items()):
            raise RuntimeError('HOLD_FROZEN_SOURCE_DRIFT')

def safe_env():
    env=os.environ.copy()
    for key in list(env):
        if any(word in key.upper() for word in (
            'PRIVATE_KEY','PRIVATEKEY','MNEMONIC','KEYPAIR','SEED_PHRASE','SOLANA_SECRET','SIGNER_SECRET')):
            env.pop(key,None)
    env['QSB_LIVE_ARM']='NO'
    env['PYTHONUNBUFFERED']='1'
    return env

class QuietOutput:
    def __init__(self,out):
        self.out,self.buffer,self.lock=out,'',threading.RLock()
        self.suppressed=0
    def write(self,text):
        with self.lock:
            self.buffer+=str(text)
            while '\n' in self.buffer:
                line,self.buffer=self.buffer.split('\n',1)
                if line.startswith('[SAE007B_ACCOUNT]'):
                    self.suppressed+=1
                else:
                    self.out.write(line+'\n')
    def flush(self):
        with self.lock:self.out.flush()

class CurveWitness:
    def __init__(self,code,output=None):
        self.code,self.output=code,output or sys.stdout
        self.lock=threading.RLock()
        self.sizes=collections.Counter()
        self.groups={}
        self.completed=0
        self.printed=0
        self.candidates=0
        self.last_complete={}
    def profile(self,frame,event,result):
        if event!='return' or frame.f_code is not self.code:return
        size=frame.f_locals.get('size_sol')
        snap=frame.f_locals.get('snap')
        if not isinstance(snap,dict) or not isinstance(size,(int,float)) or not isinstance(result,list):return
        ls=int(round(size*1_000_000_000))
        if ls not in LAMPORTS:return
        token=snap.get('token')
        if not isinstance(token,str):return
        if {x.get('direction') for x in result if isinstance(x,dict)} != {'PUMP_TO_METEORA','METEORA_TO_PUMP'}:return
        with self.lock:
            self.sizes[ls]+=1
            key=(threading.get_ident(),token,id(snap))
            entry=self.groups.setdefault(key,{'snapshot':snap,'rows':{}})
            group=entry['rows']
            group[ls]=result
            if len(self.groups)>100:
                self.groups.pop(next(iter(self.groups)))
            if len(group)==len(LAMPORTS):
                self.completed+=1
                self.candidates+=sum(1 for x in group.values() for r in x if r.get('local_net',0)>0)
                winners={}
                for direction in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):
                    rows=[r for rs in group.values() for r in rs if r['direction']==direction]
                    best=max(rows,key=lambda r:int(r['local_net']))
                    winners[direction]={'size_sol':best['size_sol'],'gross_net_lamports':int(best['local_net'])}
                self.last_complete=winners
                self.printed+=1
                size_line=' '.join('%0.3f'%s for s in GRID)
                print('[ORACLE398_ORIGINAL_GRID] token=%s sizes=%s'%(token[:12],size_line),file=self.output,flush=True)
                for direction,best in winners.items():
                    print('[ORACLE398_ORIGINAL_BEST] dir=%s size=%.3f gross=%+d (NOT FEE_CERTIFIED)'%(
                        direction,best['size_sol'],best['gross_net_lamports']),file=self.output,flush=True)
                del self.groups[key]
    def result(self):
        return {'size_count':len(self.sizes),'sizes_seen_lamports':sorted(self.sizes),
                'full_19_size_snapshots':self.completed,'selected_gross_by_direction':self.last_complete,
                'gross_positive_rows':self.candidates,'source':'ORIGINAL_Q18_RETURN_EVENTS_NOT_CONFIG_LABELS'}

def run_original(seconds):
    from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
    return q25.run(seconds=float(seconds))

def run_canonical(seconds):
    old=list(sys.argv)
    try:
        sys.argv=[str(CANONICAL),'--launch','--seconds',str(int(seconds)),'--pairs',str(PAIRS)]
        return runpy.run_path(str(CANONICAL),run_name='__main__')
    finally:sys.argv=old

def child(mode,seconds):
    check_sources(mode)
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
    from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
    original=(q20.FAST_SIZES,q20.FULL_SIZE_CURVE,q20.EXPAND_SIZES)
    if not callable(q18.exact_snapshot_opportunities):raise RuntimeError('HOLD_ORIGINAL_SDK_PRICER_MISSING')
    witness=CurveWitness(q18.exact_snapshot_opportunities.__code__)
    stdout=sys.stdout
    quiet=QuietOutput(stdout)
    prior_profile,prior_thread= sys.getprofile(),threading.getprofile()
    rc=0
    try:
        q20.FAST_SIZES=GRID
        q20.FULL_SIZE_CURVE=GRID
        q20.EXPAND_SIZES=()
        with contextlib.redirect_stdout(quiet):
            sys.setprofile(witness.profile)
            threading.setprofile(witness.profile)
            try:
                if mode=='original':run_original(seconds)
                else:run_canonical(seconds)
            except SystemExit as ex:
                rc=ex.code if isinstance(ex.code,int) else (0 if ex.code is None else 2)
            except Exception as ex:
                rc=2
                print('[ORACLE398_HOLD] type=%s'%type(ex).__name__,flush=True)
            finally:
                sys.setprofile(prior_profile)
                threading.setprofile(prior_thread)
    finally:
        q20.FAST_SIZES,q20.FULL_SIZE_CURVE,q20.EXPAND_SIZES=original
    result=witness.result()
    result.update({'mode':mode,'exit_code':rc,'account_lines_suppressed':quiet.suppressed,
       'source_hashes':source_manifest(),'read_only':True,'signing':False,'broadcast':False,
       'size_grid_sol':list(GRID),'target_pairs':PAIRS})
    result['status']='FULL_GRID_PHYSICALLY_SEEN' if result['full_19_size_snapshots'] and rc==0 else 'HOLD_UNCERTIFIED'
    target=STATE/('oracle_398_'+mode+'_scanner.json')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('[ORACLE398_RESULT]',json.dumps({k:v for k,v in result.items() if k!='source_hashes'},sort_keys=True),flush=True)
    print('[REPORT]',target.relative_to(ROOT),flush=True)
    return 0 if result['status']=='FULL_GRID_PHYSICALLY_SEEN' else 2

def test():
    assert len(GRID)==19 and GRID[0]==0.01 and GRID[-1]==0.1
    assert tuple(int(round(s*1e9)) for s in GRID)==LAMPORTS
    def fake(snap,size_sol):
        return [{'direction':d,'size_sol':size_sol,'local_net':int(size_sol*1e9)-10000}
                for d in ('PUMP_TO_METEORA','METEORA_TO_PUMP')]
    import io
    output=io.StringIO()
    w=CurveWitness(fake.__code__,output)
    prior=sys.getprofile()
    sys.setprofile(w.profile)
    try:
        for s in GRID:fake({'token':'fixture_token'},s)
    finally:sys.setprofile(prior)
    assert w.result()['size_count']==19 and w.result()['full_19_size_snapshots']==0
    # One immutable snapshot is required for a true complete curve.
    snap={'token':'fixture_token'}
    w=CurveWitness(fake.__code__,output)
    sys.setprofile(w.profile)
    try:
        for s in GRID:fake(snap,s)
    finally:sys.setprofile(prior)
    assert w.result()['full_19_size_snapshots']==1
    assert w.result()['selected_gross_by_direction']['PUMP_TO_METEORA']['size_sol']==0.1
    assert '0.100' in output.getvalue()
    env=safe_env()
    assert 'QSB_SOLANA_PRIVATE_KEY' not in env
    quiet=QuietOutput(io.StringIO())
    quiet.write('[SAE007B_ACCOUNT] noisy\n[ORACLE398] PASS\n')
    assert quiet.suppressed==1
    print('[PASS] ORACLE398 19 exact sizes, same-snapshot dual direction, unchanged pricing, output filter, key scrubbing')
    print('[SCOPE] Deterministic fixtures only; live scanner qualification remains unclaimed')

def freeze():
    records=[]
    for mode in ('original','canonical'):
        f=STATE/('oracle_398_'+mode+'_scanner.json')
        if not f.is_file():raise RuntimeError('HOLD_MISSING_'+mode.upper()+'_CERTIFICATION')
        data=json.loads(f.read_text(encoding='utf-8'))
        if data.get('status')!='FULL_GRID_PHYSICALLY_SEEN':raise RuntimeError('HOLD_'+mode.upper()+'_NOT_CERTIFIED')
        if data.get('source_hashes')!=source_manifest():raise RuntimeError('HOLD_SOURCE_DRIFT_SINCE_'+mode.upper())
        records.append(mode)
    target=STATE/'oracle_398_frozen_scanners.json'
    if target.exists():raise RuntimeError('HOLD_ALREADY_FROZEN')
    target.write_text(json.dumps({'source_hashes':source_manifest(),'verified_modes':records,
         'grid_lamports':list(LAMPORTS),'signing':False,'broadcast':False},indent=2),encoding='utf-8')
    print('[FROZEN] SHA256 source manifests locked after both full live grid witnesses')

def main():
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    for flag in ('test','audit','original','canonical','child','freeze'):g.add_argument('--'+flag,action='store_true')
    p.add_argument('--mode',choices=('original','canonical'))
    p.add_argument('--seconds',type=int,default=90)
    a=p.parse_args()
    if a.test:test();return 0
    if a.audit:
        for mode in ('original','canonical'):
            check_sources(mode)
            print('[AUDIT]',mode,'PRESENT_SHA256',json.dumps(source_manifest(),sort_keys=True))
        print('[GRID]',' '.join('%.3f'%s for s in GRID))
        return 0
    if a.freeze:freeze();return 0
    if not 1<=a.seconds<=43200:raise RuntimeError('HOLD_DURATION_OUT_OF_RANGE')
    if a.child:
        if not a.mode:raise RuntimeError('HOLD_CHILD_MODE_REQUIRED')
        return child(a.mode,a.seconds)
    mode='original' if a.original else 'canonical'
    check_sources(mode)
    # Never modify a second active WS producer or scanner lock.
    lock=STATE/'scanner.lock'
    if lock.exists():
        raise RuntimeError('HOLD_SCANNER_LOCK_PRESENT_STOP_EXISTING_SCANNER_FIRST')
    print('[ORACLE398_START] mode=%s source=ORIGINAL size_curve=19 websocket_single_producer=True'%(mode),flush=True)
    cmd=[sys.executable,'-m',MODULE,'--child','--mode',mode,'--seconds',str(a.seconds)]
    with subprocess.Popen(cmd,env=safe_env(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
        text=True,encoding='utf-8',errors='replace',bufsize=1) as proc:
        for line in proc.stdout:
            line=re.sub(r'(?i)(api-key=)[^&\s]+',r'\1[REDACTED]',line)
            print(line,end='',flush=True)
        return proc.wait()

if __name__=='__main__':sys.exit(main())
