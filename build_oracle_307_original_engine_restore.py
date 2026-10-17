"""ORACLE-307: restore ORIGINAL Oracle-025/020/018 exact live quote engine.
One complete read-only installer/launcher. No production module modifications.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import os
import queue
import re
import sqlite3
import subprocess
import threading
import time
import uuid
from collections import Counter
from pathlib import Path

ROOT=Path('runtime_state/oracle/oracle_live_execution')
DB=ROOT/'ORACLE307_ORIGINAL_EXACT_EVIDENCE.sqlite3'
REPORT=ROOT/'ORACLE307_RESTORE_REPORT.json'
MODS={
 'q18':Path('qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py'),
 'q20':Path('qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py'),
 'q23':Path('qseries_v2/oracle_execution/oracle_023_persistent_token_net_worker.py'),
 'q25':Path('qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py'),
 'pump_js':Path('qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native/sae003_pump_exact_quote_worker.mjs'),
 'net_js':Path('qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native/oracle023_token_net_worker.mjs'),
}
GRID=tuple(round(.010+.005*i,3) for i in range(19))
DIRECTIONS=frozenset(('METEORA_TO_PUMP','PUMP_TO_METEORA'))


def disarm():
    if os.environ.get('QSB_SOLANA_PRIVATE_KEY'):
        raise RuntimeError('OBSERVATION_CHILD_MUST_NOT_RECEIVE_PRIVATE_KEY')
    if os.environ.get('QSB_LIVE_ARM','NO').upper()!='NO':
        raise RuntimeError('LIVE_ARM_MUST_BE_NO')


def source_audit():
    manifest={}; contracts={
      'q18':{'exact_snapshot_opportunities','PumpSdkWorker'},
      'q20':{'LatestStateLane','run'},
      'q23':{'install_hot_token_net'},
      'q25':{'prepare_once','bind_cached_state','run'},
    }
    for name,path in MODS.items():
        if not path.is_file():raise RuntimeError('MISSING_ORIGINAL_MODULE:'+str(path))
        raw=path.read_bytes()
        manifest[name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'path':str(path)}
        if name in contracts:
            nodes=ast.parse(raw.decode('utf-8-sig'),str(path)).body
            found={x.name for x in nodes if isinstance(x,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef))}
            if not contracts[name]<=found:raise RuntimeError('ORIGINAL_MODULE_INTERFACE_CHANGED:'+name)
    # No dynamic changes to original worker: verify warm->buy/sell contract exists.
    js=MODS['pump_js'].read_text(encoding='utf-8')
    if 'SAE003_POOL_NOT_WARM' not in js or 'swapSolanaState' not in js:
        raise RuntimeError('PUMP_SDK_WARM_CONTRACT_CHANGED')
    q20=MODS['q20'].read_text(encoding='utf-8')
    if 'q18.worker().warm(pool)' not in q20 or 'self._warm(snap)' not in q20:
        raise RuntimeError('ORIGINAL_LATEST_STATE_WARMUP_MISSING')
    return manifest


def redact(s):
    s=re.sub(r'(?i)(api-key=)[^\s&"\']+',r'\1[REDACTED]',str(s))
    s=re.sub(r'(?i)(authorization|private.?key|secret)\s*[=:]\s*[^\s,}\]]+',r'\1=[REDACTED]',s)
    return s[:300]


def open_db(path=DB):
    path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(path,timeout=25)
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA busy_timeout=25000')
    db.execute('''CREATE TABLE IF NOT EXISTS runs(
       id TEXT PRIMARY KEY,started REAL,ended REAL,original_sha TEXT,
       grid TEXT,status TEXT,feed TEXT,notes TEXT)''')
    db.execute('''CREATE TABLE IF NOT EXISTS quotes(
       run_id TEXT, epoch REAL, token TEXT,pool TEXT,slot INTEGER,
       direction TEXT,size_sol REAL,input_lamports INTEGER,output_lamports INTEGER,
       gross_bps REAL,status TEXT,reason TEXT,source TEXT,
       PRIMARY KEY(run_id,epoch,token,direction,size_sol,status))''')
    db.execute('''CREATE TABLE IF NOT EXISTS events(
       run_id TEXT,epoch REAL,kind TEXT,detail TEXT)''')
    db.execute('CREATE INDEX IF NOT EXISTS quotes_time ON quotes(epoch DESC)')
    db.commit()
    return db


class Evidence:
    """Non-blocking recorder; does not change the scanner's data path."""
    def __init__(self,run_id,path=DB):
        self.id=run_id;self.path=path;self.q=queue.Queue(maxsize=40000)
        self.stop=threading.Event();self.drops=0;self.counts=Counter()
        self.thread=threading.Thread(target=self.writer,name='oracle307-ledger',daemon=True)
        self.thread.start()
    def emit(self,kind,data):
        try:self.q.put_nowait((kind,data))
        except queue.Full:self.drops+=1
    def writer(self):
        con=open_db(self.path);pending=0;last=time.monotonic()
        try:
            while not self.stop.is_set() or not self.q.empty():
                try:kind,data=self.q.get(timeout=.1)
                except queue.Empty:kind=None
                if kind=='quote':
                    con.execute('INSERT OR REPLACE INTO quotes VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                        (self.id,*data));pending+=1
                elif kind=='event':
                    con.execute('INSERT INTO events VALUES(?,?,?,?)',(self.id,*data));pending+=1
                if pending and (pending>=100 or time.monotonic()-last>=.5 or self.stop.is_set()):
                    con.commit();pending=0;last=time.monotonic()
        finally:
            con.commit();con.close()
    def close(self):
        self.stop.set();self.thread.join(timeout=15)
        if self.thread.is_alive():raise RuntimeError('LEDGER_FLUSH_TIMEOUT')


CTX=threading.local()

def passive_tap(original,evidence):
    """Exact pass-through: no pricing or fill logic changes."""
    def wrapped(snap,size):
        token=str(snap.get('token',''));pool=str(snap.get('pump_pool',''))
        slot=getattr(CTX,'slot',None);epoch=time.time();amount=round(float(size)*1e9)
        try:
            rows=original(snap,size)
            if not isinstance(rows,list) or {r.get('direction') for r in rows}!=DIRECTIONS:
                raise RuntimeError('EXACT_PRICER_RETURN_CONTRACT_INVALID')
            for r in rows:
                end=int(r['local_end']);direction=r['direction']
                if end<=0 or amount<=0:raise RuntimeError('NONPOSITIVE_QUOTE_OUT')
                gross=(end-amount)*10000/amount
                status='GROSS_POSITIVE_CANDIDATE' if end>amount else 'GROSS_NONPOSITIVE'
                evidence.counts[status]+=1
                evidence.emit('quote',(epoch,token,pool,slot,direction,float(size),amount,end,gross,status,'','ORIGINAL_ORACLE018'))
                if end>amount:
                    print('[ORACLE307_CANDIDATE]',json.dumps({'token':token,'direction':direction,
                        'size_sol':float(size),'gross_bps':round(gross,3),'slot':slot,
                        'execution_admission':False,'net_certified':False}),flush=True)
            return rows
        except Exception as exc:
            reason=redact(type(exc).__name__+':'+str(exc))
            evidence.counts['QUOTE_HOLD']+=1
            evidence.emit('quote',(epoch,token,pool,slot,'UNRESOLVED',float(size),amount,None,None,
                                   'QUOTE_HOLD',reason,'ORIGINAL_ORACLE018'))
            raise
    return wrapped


def passive_slot_tap(original):
    def wrapped(self,token,row):
        try:CTX.slot=int(row[1]);CTX.token=token
        except Exception:CTX.slot=None;CTX.token=token
        try:return original(self,token,row)
        finally:CTX.slot=None;CTX.token=None
    return wrapped


def save_report(data):
    ROOT.mkdir(parents=True,exist_ok=True)
    tmp=REPORT.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2,sort_keys=True,default=str),encoding='utf-8')
    tmp.replace(REPORT)


def verify_components(q18,q20,q23,q25):
    if not callable(q18.exact_snapshot_opportunities):raise RuntimeError('EXACT_PRICER_MISSING')
    if not callable(q25.run):raise RuntimeError('ORIGINAL_LAUNCHER_MISSING')
    if not callable(q23.install_hot_token_net):raise RuntimeError('TOKEN_NET_MODULE_MISSING')
    if not callable(q20.LatestStateLane._warm):raise RuntimeError('POOL_WARMUP_MISSING')
    if not callable(q18.PumpSdkWorker.warm):raise RuntimeError('PUMP_WARM_MISSING')
    if not Path(q18.WORKER_JS).is_file():raise RuntimeError('PUMP_JS_WORKER_MISSING')
    if not Path(q18.NODEDIR,'node_modules').is_dir():raise RuntimeError('NATIVE_NODE_DEPENDENCIES_MISSING')
    r=subprocess.run(['node','--version'],capture_output=True,text=True,timeout=8)
    if r.returncode:raise RuntimeError('NODE_UNAVAILABLE')
    return {'pump_sdk_warm':True,'single_hydration':True,'latest_state':True,'token_net_worker':True}


def run(seconds,grid='native',max_warms=28):
    disarm();manifest=source_audit()
    if not os.getenv('SOLANA_RPC_URL','').startswith('https://'):
        raise RuntimeError('SOLANA_RPC_URL_REQUIRED_IN_CHILD')
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
    from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
    from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23
    from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
    contracts=verify_components(q18,q20,q23,q25)
    # Keep the original scanner and event lane; only configure the requested size policy.
    if grid=='19':q20.FAST_SIZES=GRID;q20.EXPAND_SIZES=()
    elif grid!='native':raise RuntimeError('UNKNOWN_SIZE_GRID')
    run_id=uuid.uuid4().hex[:16];con=open_db()
    con.execute('INSERT INTO runs VALUES(?,?,?,?,?,?,?,?)',
        (run_id,time.time(),None,manifest['q18']['sha256'],grid,'RUNNING','ORACLE025_ORACLE020_ORACLE018','read-only'))
    con.commit();con.close()
    ev=Evidence(run_id)
    # A runtime tap that records both authentic outputs, never replaces quoting math.
    orig_quote=q18.exact_snapshot_opportunities
    orig_price=q20.LatestStateLane._price
    orig_warm=q18.PumpSdkWorker.warm
    warm_set=set();warm_attempts=set();warm_fail={}
    def warm_bounded(self,pool):
        now=time.monotonic()
        if pool in warm_fail and now<warm_fail[pool][0]:
            raise RuntimeError('ORACLE307_POOL_WARM_COOLDOWN')
        if pool not in warm_attempts and len(warm_attempts)>=max_warms:
            raise RuntimeError('ORACLE307_WARM_CAP_REACHED')
        warm_attempts.add(pool)
        try:
            res=orig_warm(self,pool)
        except Exception:
            n=warm_fail.get(pool,(0,0))[1]+1
            warm_fail[pool]=(now+min(15*(2**min(n-1,5)),300),n)
            ev.emit('event',(time.time(),'PUMP_WARM_FAILED_COOLDOWN',str(pool)[:48]))
            raise
        warm_fail.pop(pool,None)
        warm_set.add(pool)
        ev.emit('event',(time.time(),'PUMP_POOL_WARMED',str(pool)[:48]))
        return res
    q18.exact_snapshot_opportunities=passive_tap(orig_quote,ev)
    q20.LatestStateLane._price=passive_slot_tap(orig_price)
    q18.PumpSdkWorker.warm=warm_bounded
    print('[ORACLE307_START]',json.dumps({'run_id':run_id,'original_modules_verified':True,
       'pipeline':'ORACLE025->ORACLE020->ORACLE018','sizes':list(q20.FAST_SIZES),
       'max_warm_pools':max_warms,'execution':False,'signing':False,'broadcast':False}),flush=True)
    state='COMPLETED';exception=''
    try:
        q25.run(seconds=float(seconds))
    except KeyboardInterrupt:
        state='STOPPED_BY_USER'
    except Exception as exc:
        state='FAILED';exception=redact(type(exc).__name__+':'+str(exc))
        print('[ORACLE307_FAILURE]',exception,flush=True)
    finally:
        q18.exact_snapshot_opportunities=orig_quote
        q20.LatestStateLane._price=orig_price
        q18.PumpSdkWorker.warm=orig_warm
        ev.close()
        con=open_db();con.execute('UPDATE runs SET ended=?, status=?,notes=? WHERE id=?',
             (time.time(),state,exception,run_id));con.commit()
        totals=dict(con.execute('SELECT status,COUNT(*) FROM quotes WHERE run_id=? GROUP BY status',(run_id,)).fetchall())
        con.close()
        report={'build':'ORACLE307','run_id':run_id,'status':state,'original_pipeline':True,
                'original_code_modified':False,'contracts':contracts,'module_sha256':manifest,
                'size_policy':grid,'observed_quote_counts':totals,'dropped_evidence_events':ev.drops,
                'warm_pools':len(warm_set),'warm_attempted_pools':len(warm_attempts),'gross_positive_not_net':True,
                'fee_adjusted_net_certified':False,'atomic_simulation_certified':False,
                'execution_admission':False,'signing':False,'broadcast':False,'error':exception}
        save_report(report)
        print('[ORACLE307_RESULT]',json.dumps({k:v for k,v in report.items() if k!='module_sha256'},sort_keys=True),flush=True)
        print('[REPORT]',REPORT,flush=True)
        for name,worker in (("pump",getattr(q18,'_worker',None)),("token",getattr(q23,'_worker',None))):
            if worker is not None:
                try:worker.close()
                except Exception:pass
    if state=='FAILED':raise SystemExit(2)


def table(n=25):
    if not DB.exists():print('[ORACLE307] NO_ORIGINAL_QUOTE_EVIDENCE_YET');return
    con=open_db();last=con.execute('SELECT id,status,grid,started FROM runs ORDER BY started DESC LIMIT 1').fetchone()
    if not last:print('[ORACLE307] NO_RUNS');return
    print('ORACLE-307 | ORIGINAL EXACT P2M / M2P | GROSS CANDIDATES (NOT EXECUTABLE NET)')
    print('RUN',last[0],'STATUS',last[1],'GRID',last[2])
    totals=con.execute('SELECT direction,status,COUNT(*) FROM quotes WHERE run_id=? GROUP BY direction,status',(last[0],)).fetchall()
    print('[SUMMARY]',json.dumps([{'direction':a,'status':b,'count':c} for a,b,c in totals]))
    print('TOKEN         SLOT       DIRECTION          SIZE   GROSS BPS  STATUS')
    rows=con.execute('SELECT token,slot,direction,size_sol,gross_bps,status FROM quotes WHERE run_id=? ORDER BY epoch DESC LIMIT ?',
                     (last[0],max(1,min(500,n)))).fetchall()
    for token,slot,direction,size,bps,status in rows:
        print(f'{token[:12]:12} {str(slot or "-"):10} {direction:18} {size:.3f} {bps if bps is not None else "-":>10} {status}')
    print('[GATE] Gross-positive == indicative only; no signed simulation, fee-adjusted net or execution authority.')
    con.close()


def gate():
    base={'build':'ORACLE307','execution_authority':False,'signing':False,'broadcast':False,
          'first_canary_sol':0.010,'fee_adjusted_net_certified':False,
          'atomic_signed_simulation_certified':False,'freshness_revalidation_certified':False,
          'canary_admitted':False}
    if DB.exists():
        c=open_db();base['gross_positive_quotes_observed']=c.execute(
            'SELECT COUNT(*) FROM quotes WHERE status="GROSS_POSITIVE_CANDIDATE"').fetchone()[0];c.close()
    print('[ORACLE307_LIVE_READINESS]',json.dumps(base,sort_keys=True))
    print('[HOLD] Never equate historical/indicative bps to executable wallet profit.')


def test():
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        dbpath=Path(directory)/'test.sqlite3'
        c=open_db(dbpath);c.close()
        class Collector:
            def __init__(self):self.rows=[];self.counts=Counter()
            def emit(self,kind,row):self.rows.append((kind,row))
        collector=Collector()
        def official(snap,size):
            amount=round(size*1e9)
            return [{'direction':'PUMP_TO_METEORA','local_end':amount+25000},
                    {'direction':'METEORA_TO_PUMP','local_end':amount-5000}]
        tapped=passive_tap(official,collector)
        import contextlib,io
        with contextlib.redirect_stdout(io.StringIO()):
            result=tapped({'token':'T','pump_pool':'P'},.010)
        assert result==official({},.010) and len(collector.rows)==2
        assert collector.counts['GROSS_POSITIVE_CANDIDATE']==1
        assert collector.counts['GROSS_NONPOSITIVE']==1
        def failed(snap,size):raise RuntimeError('SAE003_POOL_NOT_WARM')
        try:passive_tap(failed,collector)({'token':'T','pump_pool':'P'},.015)
        except RuntimeError:pass
        else:raise AssertionError('NATIVE_EXCEPTION_SWALLOWED')
        assert collector.counts['QUOTE_HOLD']==1
        slots=[]
        def original_price(self,token,row):slots.append(getattr(CTX,'slot',None))
        class Lane:pass
        passive_slot_tap(original_price)(Lane(),'T',(None,123,0,0))
        assert slots==[123] and getattr(CTX,'slot') is None
        assert len(GRID)==19 and GRID[0]==.010 and GRID[-1]==.100
        assert '[REDACTED]' in redact('api-key=top-secret')
        assert open_db(dbpath).execute('SELECT COUNT(*) FROM quotes').fetchone()[0]==0
    print('[ORACLE307_TEST_PASS] native_passthrough=TRUE independent_evidence=TRUE'+
          ' sdk_errors_visible=TRUE slot_provenance=TRUE grid19=TRUE sqlite=TRUE readonly=TRUE')


def main():
    p=argparse.ArgumentParser(description='ORACLE-307 original scanner restore; read-only')
    p.add_argument('--test',action='store_true');p.add_argument('--run',action='store_true')
    p.add_argument('--table',action='store_true');p.add_argument('--gate',action='store_true')
    p.add_argument('--seconds',type=float,default=120.0)
    p.add_argument('--grid',choices=['native','19'],default='native')
    p.add_argument('--max-warms',type=int,default=28)
    p.add_argument('--rows',type=int,default=25)
    args=p.parse_args()
    if args.test:test()
    elif args.run:run(args.seconds,args.grid,max(1,min(100,args.max_warms)))
    elif args.table:table(args.rows)
    elif args.gate:gate()
    else:p.error('Choose --test, --run, --table or --gate')

if __name__=='__main__':main()
