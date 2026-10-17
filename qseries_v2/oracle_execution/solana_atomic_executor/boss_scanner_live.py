
"""ORACLE-388 bounded 0.010-0.100 dynamic scanner: frozen Q25/Q20/Q18, no execution.
Publish best independently measured amount per direction to original 12-column SQLite WAL.
"""
from __future__ import annotations
import argparse,builtins,contextlib,hashlib,json,os,pathlib,sqlite3,subprocess,sys,threading,time,uuid
from collections import Counter
ROOT=pathlib.Path('runtime_state/oracle/final_boss_dual')
DB=ROOT/'candidate_bus.sqlite3'
LOCK=ROOT/'scanner.lock'
STATUS=ROOT/'scanner_status.json'
INVENTORY=ROOT/'scanner_inventory.json'
STAGED=ROOT/'staged_discovery.json'
LIVE=ROOT/'scanner_live.json'
BASELINE=ROOT/'frozen_scanner_hashes.json'
SCHEMA=1
SIZE_MIN_LAMPORTS=10_000_000
SIZE_MAX_LAMPORTS=100_000_000
SIZE_STEP_LAMPORTS=5_000_000
SIZE_CURVE_SOL=tuple(round(0.010+i*0.005,3) for i in range(19))
SOURCES={'SQ':pathlib.Path('runtime_state/oracle/final_boss/sq_candidates.json'),
         'UNIVERSAL':pathlib.Path('runtime_state/oracle/final_boss/universal_candidates.json')}
FREEZE={'q18':'qseries_v2/oracle_execution/oracle_018_exact_sdk_hot_lane_cutover.py',
        'q20':'qseries_v2/oracle_execution/oracle_020_latest_state_exact_pricing_worker.py',
        'q25':'qseries_v2/oracle_execution/oracle_025_single_hydration_exact_live_reuse.py'}

def emit(k,v):print('['+k+'] '+json.dumps(v,sort_keys=True,default=str),flush=True)
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    tmp.write_text(json.dumps(obj,sort_keys=True,indent=2),encoding='utf-8');os.replace(tmp,path)
def audit():
    result={}
    for name,fn in FREEZE.items():
        p=pathlib.Path(fn)
        if not p.is_file():raise RuntimeError('FROZEN_SOURCE_MISSING:'+fn)
        result[name]=hashlib.sha256(p.read_bytes()).hexdigest()
    return result

def connect():
    ROOT.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(str(DB),timeout=5,isolation_level=None,check_same_thread=False)
    c.execute('PRAGMA busy_timeout=5000')
    c.execute('PRAGMA journal_mode=WAL')
    c.execute('PRAGMA synchronous=NORMAL')
    c.execute('CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,producer TEXT NOT NULL,token TEXT NOT NULL,pump_pool TEXT NOT NULL,meteora_pool TEXT NOT NULL,direction TEXT NOT NULL,size_lamports INTEGER NOT NULL,gross_lamports INTEGER NOT NULL,slot INTEGER NOT NULL,generation INTEGER NOT NULL,created_ns INTEGER NOT NULL,source TEXT NOT NULL)')
    c.execute('CREATE INDEX IF NOT EXISTS events_created ON events(created_ns)')
    c.execute('CREATE TABLE IF NOT EXISTS heartbeat(name TEXT PRIMARY KEY,producer TEXT,unix_ns INTEGER,epoch INTEGER,admitted INTEGER,emitted INTEGER)')
    return c

def latest_feed():
    rows=[]
    for source,p in SOURCES.items():
        try:
            obj=json.loads(p.read_text(encoding='utf-8'))
            if obj.get('schema')!='oracle-final-boss-candidates-v1' or obj.get('source')!=source:continue
            if not 0<=time.time()-float(obj.get('generated_at',0))<=120:continue
            for x in (obj.get('candidates') or [])[:128]:
                if isinstance(x,dict) and x.get('token') and x.get('pump_pool'):
                    rows.append(dict(x,source=source))
        except (OSError,ValueError,TypeError,AttributeError):continue
    return rows

def select_rows(original):
    grouped={}
    from_disk=[]
    try:
        o=json.loads(STAGED.read_text(encoding='utf-8'))
        if 0<=time.time()-float(o['generated_at'])<=600 and isinstance(o.get('rows'),list):
            from_disk=o['rows'][:112]
    except (OSError,ValueError,TypeError,KeyError):pass
    for row in list(original)+from_disk+latest_feed():
        if not isinstance(row,dict):continue
        token=row.get('token');pump=row.get('pump_pool')
        if not isinstance(token,str) or not isinstance(pump,str) or len(token)<32 or len(pump)<32:continue
        key=(token,pump);r=grouped.setdefault(key,dict(token=token,pump_pool=pump,sources=set()))
        src=str(row.get('source') or 'LIVE_TAPE').upper()
        r['sources'].add('MRIYA' if src.startswith('MRIYA') else src)
    order={'MRIYA':5,'SQ':4,'UNIVERSAL':3,'LIVE_TAPE':2}
    data=[]
    for v in grouped.values():
        src=sorted(v['sources']);v['sources']=src
        v['rank']=max((order.get(s,1) for s in src),default=1)+min(2,(len(src)-1)*.5)
        data.append(v)
    return sorted(data,key=lambda x:(-x['rank'],x['token']))

@contextlib.contextmanager
def one_process():
    ROOT.mkdir(parents=True,exist_ok=True)
    try:fd=os.open(str(LOCK),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    except FileExistsError:raise RuntimeError('SCANNER_ALREADY_RUNNING_CHECK_LOCK:'+str(LOCK))
    with os.fdopen(fd,'w',encoding='utf-8') as w:w.write(str(os.getpid()))
    try:yield
    finally:
        try:
            if LOCK.read_text(encoding='utf-8')==str(os.getpid()):LOCK.unlink()
        except OSError:pass

def stage_discovery():
    # Run in a separate process; never mutate the active scanner's Python globals.
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine
    rows=select_rows(engine.raw_candidate_universe(pathlib.Path.cwd()))
    save(STAGED,dict(generated_at=time.time(),rows=rows[:112],candidates=len(rows)))
    emit('BOSS322_DISCOVERY_STAGED',dict(candidates=len(rows),live_subscriptions_changed=False))
    return 0

def choose_direction_best(rows):
    best={}
    for op in rows:
        if not isinstance(op,dict):continue
        direction=op.get('direction')
        size=op.get('start')
        gross=op.get('local_net')
        if direction not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):continue
        if type(size) is not int or not SIZE_MIN_LAMPORTS<=size<=SIZE_MAX_LAMPORTS:continue
        if type(gross) is not int or gross<=0:continue
        current=best.get(direction)
        if current is None or (gross, -size)>(int(current['local_net']),-int(current['start'])):
            best[direction]=op
    return best

def scan_epoch(seconds,pairs,accounts,epoch,producer):
    from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
    from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
    from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import engine,live_account_stream as pd,merged_live_runtime as merged
    c=connect();mu=threading.Lock();tls=threading.local();stats=Counter();generation=Counter()
    last_best={};seen_best={}
    started=time.monotonic()
    status='STARTING';error=None
    from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import persistent_profit_runtime as persistent
    from qseries_v2.oracle_execution.oracle_014_venue_native_fast_lane import NullSimulationLane
    old_sim=persistent.SimulationLane;old_persist_pairs=persistent.MAX_PAIRS
    original_print=builtins.print
    def live_print(*args,**kwargs):
        msg=' '.join(map(str,args))
        if msg.startswith('[HEARTBEAT]'):
            stats['legacy_heartbeats_ignored']+=1;return
        if msg.startswith(('[HOT_SIGNAL_INITIAL]','[HOT_SIGNAL]')):
            stats['legacy_hot_ignored']+=1
            if stats['legacy_hot_ignored']==1:
                original_print('[BOSS322_LEGACY_IGNORED] preliminary hot signals do NOT enter candidate bus',flush=True)
            return
        if msg.startswith('[ORACLE020_SCAN_REPLACED]'):
            stats['coalesced_scan']+=1;return
        if msg.startswith('[WS_RECOVER]') and '429' in msg:stats['ws_429']+=1
        return original_print(*args,**kwargs)
    old_print=getattr(q20,'print',None);had_print='print' in q20.__dict__
    original=(engine.raw_candidate_universe,engine.MAX_TOKENS,engine.DISCOVERY_BUDGET,
              pd.MAX_PAIRS,merged.MAX_ACCOUNTS,q25.prepare_once,q18.exact_snapshot_opportunities,
              q20.LatestStateLane._price,q20.FAST_SIZES,q20.EXPAND_SIZES)
    prior={};ranked=[]
    def discovery(root):
        nonlocal ranked
        ranked=select_rows(original[0](root))
        return [dict(token=r['token'],pump_pool=r['pump_pool'],source=r['sources'][0]) for r in ranked[:max(96,pairs*4)]]
    def prepare(root):
        state,cap=original[5](root)
        mapped={r['token']:r['sources'] for r in ranked}
        out=[]
        for p in state.get('pairs') or []:
            token=str(p.token)
            out.append(dict(token=token,pump_pool=str(p.pump_pool),meteora_pool=str(p.meteora_pool),
                            sources=mapped.get(token,['UNATTRIBUTED'])))
        report=dict(build='ORACLE322',epoch=epoch,capacity=pairs,admitted=len(out),
                    accounts=len(state.get('addresses') or []),pairs=out,producer=producer)
        save(INVENTORY,report)
        emit('BOSS322_INVENTORY',{k:v for k,v in report.items() if k!='pairs'})
        prior.update({x['token']:x for x in out})
        return state,cap
    def scan(self,token,row):
        tls.slot=int(row[1]);generation[str(token)]+=1
        tls.generation=generation[str(token)];tls.row_generation=int(row[3]);tls.lane=self
        tls.quote_rows=[]
        stats['exact_snapshots_started']+=1
        try:
            # Original Q20 optimizer evaluates the complete Q20 canonical size curve.
            # Collect its exact Q18 quotes; publish only after Q20 finishes this snapshot.
            try:
                value=original[7](self,token,row)
            except ValueError as exc:
                # Frozen Q20 calls max(rows) after its last size. When ALL exact
                # sizes fail DLMM_PARTIAL, a missing quote is a clean HOLD,
                # never a candidate and never a reason to fake an output.
                if not tls.quote_rows and 'max() iterable argument is empty' in str(exc):
                    stats['no_complete_quotes']+=1
                    return None
                raise
            candidates=choose_direction_best(tls.quote_rows)
            if not candidates:return value
            if self.newer_waiting(token,int(tls.row_generation)):
                stats['superseded_candidate']+=1;return value
            pool=prior.get(str(token))
            if not pool or not tls.quote_rows:return value
            # Identical token/pump identity; Meteora matched via verified scanner inventory.
            for direction,op in candidates.items():
                if str(op.get('pump_pool'))!=pool['pump_pool']:continue
                met=op.get('meteora') or {}
                if isinstance(met,dict) and met.get('address')!=pool['meteora_pool']:continue
                size=int(op['start']);gross=int(op['local_net'])
                data=(producer,str(token),pool['pump_pool'],pool['meteora_pool'],direction,
                      size,gross,int(tls.slot),int(tls.generation),time.time_ns(),','.join(pool['sources']))
                with mu:
                    c.execute('INSERT INTO events(producer,token,pump_pool,meteora_pool,direction,size_lamports,gross_lamports,slot,generation,created_ns,source) VALUES(?,?,?,?,?,?,?,?,?,?,?)',data)
                    stats['positive']+=1;stats['gross_positive_010']+=1
                emit('BOSS322_EXACT_CANDIDATE',dict(token=str(token)[:12],direction=direction,
                     slot=int(tls.slot),gross_lamports=gross,size_lamports=size,
                     size_sol=size/1e9,net_certified=False,selection='Q20_BEST_PER_DIRECTION_0.010_TO_0.100'))
            return value
        finally:
            tls.slot=0;tls.generation=0;tls.row_generation=0;tls.lane=None;tls.quote_rows=[]
    def quiet(*args,**kwargs):
        msg=' '.join(map(str,args))
        if msg.startswith('[ORACLE020_EXACT_LATEST]') and 'net=-' in msg:
            stats['quiet_negative_quote']+=1;return
        return builtins.print(*args,**kwargs)
    def price(snap,size):
        try:rows=original[6](snap,size)
        except RuntimeError as exc:
            if str(exc)=='DLMM_PARTIAL':
                stats['size_partial_skips']+=1;return []
            raise
        if getattr(tls,'slot',0)>0 and str(snap.get('token') or '') in prior:
            with mu:
                tls.quote_rows.extend(rows)
                stats['snapshots_010']+=1  # compatibility name, now counts all 19-size quote evaluations
                stats['quotes_010']+=len(rows)  # compatibility name, now counts all accepted sized quotes
                for op in rows:
                    direction=op.get('direction')
                    if direction not in ('PUMP_TO_METEORA','METEORA_TO_PUMP'):continue
                    if type(op.get('start')) is not int or not SIZE_MIN_LAMPORTS<=int(op['start'])<=SIZE_MAX_LAMPORTS:continue
                    key=(str(snap['token']),direction)
                    val=dict(token=str(snap['token'])[:12],direction=direction,
                      slot=int(tls.slot),gross_lamports=int(op.get('local_net') or 0),
                      gross_bps=round(float(op.get('local_bps') or 0),2),
                      observed_mono=time.monotonic(),size_sol=int(op['start'])/1e9)
                    prev=last_best.get(key)
                    if prev is None or val['gross_lamports']>prev['gross_lamports'] or prev['slot']!=val['slot']:
                        last_best[key]=val
                    seen_best[str(snap['token'])]=time.monotonic()
        return rows
    done=threading.Event()
    def heartbeat():
        last_show=0.0;prev_snap=0;prev_t=time.monotonic()
        while not done.wait(1):
            with mu:
                c.execute('INSERT INTO heartbeat(name,producer,unix_ns,epoch,admitted,emitted) VALUES(?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET producer=excluded.producer,unix_ns=excluded.unix_ns,epoch=excluded.epoch,admitted=excluded.admitted,emitted=excluded.emitted',
                          ('scanner',producer,time.time_ns(),epoch,len(prior),stats['positive']))
                now=time.monotonic()
                if now-last_show>=6:
                    recent=[dict(v,age_ms=int((now-v['observed_mono'])*1000))
                            for v in last_best.values() if now-v['observed_mono']<=15]
                    for v in recent:v.pop('observed_mono',None)
                    recent.sort(key=lambda x:x['gross_lamports'],reverse=True)
                    volume=stats['snapshots_010'];span=max(.01,now-prev_t)
                    total=stats['quotes_010'];per_sec=round((volume-prev_snap)/span,2)
                    status=dict(build='ORACLE322',status='RUNNING',epoch=epoch,admitted=len(prior),
                        accounts=stats['subscribed_accounts'],exact_snapshots_started=stats['exact_snapshots_started'],
                        snapshots_010=volume,quotes_010=total,rate_010_snapshots_per_s=per_sec,
                        exact_gross_positive_010=stats['gross_positive_010'],candidates_to_executor=stats['positive'],
                        unique_tokens_recent=len({v['token'] for v in recent}),
                        recent_quotes=recent[:5],coalesced_scans=stats['coalesced_scan'],
                        websocket_429=stats['ws_429'],legacy_hot_ignored=stats['legacy_hot_ignored'],
                        size_selection='BEST_POSITIVE_GROSS_PER_DIRECTION_0.010_TO_0.100_SOL',
                        size_curve_min_sol=0.010,size_curve_max_sol=0.100,size_curve_count=len(SIZE_CURVE_SOL),
                        sized_snapshots=volume,sized_quotes=total,
                        incomplete_size_skips=stats['size_partial_skips'],no_complete_quotes=stats['no_complete_quotes'],
                        legacy_simulation_disabled=True,signing=False,broadcast=False)
                    save(LIVE,status);save(STATUS,status)
                    emit('BOSS322_LIVE_MARKET',status)
                    prev_snap=volume;prev_t=now;last_show=now
    try:
        engine.raw_candidate_universe=discovery
        engine.MAX_TOKENS=max(56,pairs*2);engine.DISCOVERY_BUDGET=max(96,pairs*4)
        pd.MAX_PAIRS=pairs;merged.MAX_ACCOUNTS=accounts
        q25.prepare_once=prepare;q18.exact_snapshot_opportunities=price
        q20.LatestStateLane._price=scan
        persistent.SimulationLane=NullSimulationLane
        persistent.MAX_PAIRS=pairs
        builtins.print=live_print
        q20.print=quiet
        q20.FAST_SIZES=SIZE_CURVE_SOL;q20.EXPAND_SIZES=()
        hb=threading.Thread(target=heartbeat,daemon=True);hb.start()
        emit('BOSS322_SCANNER_START',dict(producer=producer,pair_target=pairs,selection='Q20_BEST_PER_DIRECTION_0.010_TO_0.100',size_curve_min_sol=0.010,
             size_curve_max_sol=0.100,size_curve_count=len(SIZE_CURVE_SOL),
             frozen='Q25->Q20->Q18',legacy_simulation_disabled=True,signing=False,broadcast=False))
        emit('BOSS322_EXECUTOR_OWNS_SIM',dict(legacy_simulator='DISABLED',rpc_simulations_in_scanner=0))
        q25.run(float(seconds))
        status='COMPLETED';error=None
    except Exception as exc:
        status='FAILED';error=type(exc).__name__+':'+str(exc)[:140]
    finally:
        done.set()
        builtins.print=original_print
        persistent.SimulationLane=old_sim
        persistent.MAX_PAIRS=old_persist_pairs
        (engine.raw_candidate_universe,engine.MAX_TOKENS,engine.DISCOVERY_BUDGET,
         pd.MAX_PAIRS,merged.MAX_ACCOUNTS,q25.prepare_once,q18.exact_snapshot_opportunities,
         q20.LatestStateLane._price,q20.FAST_SIZES,q20.EXPAND_SIZES)=original
        if had_print:q20.print=old_print
        else:del q20.print
        with mu:
            c.execute('INSERT INTO heartbeat(name,producer,unix_ns,epoch,admitted,emitted) VALUES(?,?,?,?,?,?) ON CONFLICT(name) DO UPDATE SET unix_ns=excluded.unix_ns,producer=excluded.producer,epoch=excluded.epoch,admitted=excluded.admitted,emitted=excluded.emitted',
                      ('scanner',producer,time.time_ns(),epoch,len(prior),stats['positive']))
        c.close()
        save(STATUS,dict(build='ORACLE322',status=status,error=error,epoch=epoch,admitted=len(prior),
                         quotes_010=stats['quotes_010'],gross_positive_010=stats['gross_positive_010'],
                         candidates_to_executor=stats['positive'],websocket_429=stats['ws_429'],
                         legacy_simulation_disabled=True,suppressed_negative=stats['quiet_negative_quote'],
                         elapsed_s=round(time.monotonic()-started,2),
                         execution=False,broadcast=False))
        emit('BOSS322_EPOCH_END',dict(status=status,quotes_010=stats['quotes_010'],gross_positive_010=stats['gross_positive_010'],candidates_to_executor=stats['positive'],no_complete_quotes=stats['no_complete_quotes'],error=error))
    return 0 if status=='COMPLETED' else 2

def tests():
    import tempfile,unittest
    class T(unittest.TestCase):
        def test_sources_dedupe(self):
            # Isolate the fixture: a user's actual staged_discovery.json may contain 40+ live rows.
            with tempfile.TemporaryDirectory() as d:
                with unittest.mock.patch.dict(globals(),{'STAGED':pathlib.Path(d)/'absent.json'}), \
                     unittest.mock.patch(__name__+'.latest_feed',return_value=[]):
                    r=select_rows([dict(token='a'*44,pump_pool='b'*44,source='LIVE_TAPE'),
                                   dict(token='a'*44,pump_pool='b'*44,source='MRIYA')])
                    self.assertEqual(len(r),1)
                    self.assertEqual(set(r[0]['sources']),{'LIVE_TAPE','MRIYA'})
        def test_real_staging_joined_with_deduplication(self):
            with tempfile.TemporaryDirectory() as d:
                staged=pathlib.Path(d)/'staged_discovery.json'
                save(staged,{'generated_at':time.time(),'rows':[
                    {'token':'a'*44,'pump_pool':'b'*44,'source':'SQ'},
                    {'token':'c'*44,'pump_pool':'d'*44,'source':'UNIVERSAL'}]})
                with unittest.mock.patch.dict(globals(),{'STAGED':staged}), \
                     unittest.mock.patch(__name__+'.latest_feed',return_value=[]):
                    r=select_rows([{'token':'a'*44,'pump_pool':'b'*44,'source':'MRIYA'}])
                    self.assertEqual(len(r),2)
                    merged=[x for x in r if x['token']=='a'*44]
                    self.assertEqual(len(merged),1)
                    self.assertEqual(set(merged[0]['sources']),{'MRIYA','SQ'})
        def test_expired_staging_excluded(self):
            with tempfile.TemporaryDirectory() as d:
                staged=pathlib.Path(d)/'expired.json'
                save(staged,{'generated_at':time.time()-601,'rows':[
                    {'token':'c'*44,'pump_pool':'d'*44,'source':'SQ'}]})
                with unittest.mock.patch.dict(globals(),{'STAGED':staged}), \
                     unittest.mock.patch(__name__+'.latest_feed',return_value=[]):
                    r=select_rows([{'token':'a'*44,'pump_pool':'b'*44,'source':'MRIYA'}])
                    self.assertEqual(len(r),1)
                    self.assertEqual(r[0]['token'],'a'*44)
        def test_bus(self):
            global ROOT,DB
            root,db=ROOT,DB
            try:
                with tempfile.TemporaryDirectory() as t:
                    ROOT=pathlib.Path(t);DB=ROOT/'bus.sqlite3';c=connect()
                    c.execute('INSERT INTO events(producer,token,pump_pool,meteora_pool,direction,size_lamports,gross_lamports,slot,generation,created_ns,source) VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                        ('x','t','p','m','PUMP_TO_METEORA',50_000_000,1,3,4,time.time_ns(),'SQ'))
                    self.assertEqual(c.execute('SELECT COUNT(*) FROM events').fetchone()[0],1)
                    c.close()
            finally:ROOT,DB=root,db
        def test_dynamic_size_bus(self):
            quotes=[dict(direction='PUMP_TO_METEORA',start=10_000_000,local_net=100),
                dict(direction='PUMP_TO_METEORA',start=50_000_000,local_net=400),
                dict(direction='METEORA_TO_PUMP',start=25_000_000,local_net=30)]
            got=choose_direction_best(quotes)
            self.assertEqual(got['PUMP_TO_METEORA']['start'],50_000_000)
            self.assertEqual(got['METEORA_TO_PUMP']['start'],25_000_000)
        def test_bounded_curve(self):
            self.assertEqual(SIZE_CURVE_SOL[0],.010)
            self.assertEqual(SIZE_CURVE_SOL[-1],.100)
            self.assertEqual(len(SIZE_CURVE_SOL),19)
            self.assertEqual(len(set(SIZE_CURVE_SOL)),19)
        def test_bounded_selection_both_directions(self):
            quotes=[dict(direction='PUMP_TO_METEORA',start=1_000_000,local_net=900_000),
                    dict(direction='PUMP_TO_METEORA',start=10_000_000,local_net=700),
                    dict(direction='PUMP_TO_METEORA',start=100_000_000,local_net=800),
                    dict(direction='PUMP_TO_METEORA',start=105_000_000,local_net=900_000),
                    dict(direction='METEORA_TO_PUMP',start=70_000_000,local_net=900)]
            q=choose_direction_best(quotes)
            self.assertEqual(q['PUMP_TO_METEORA']['start'],100_000_000)
            self.assertEqual(q['METEORA_TO_PUMP']['start'],70_000_000)
        def test_no_positive_quote_admitted(self):
            self.assertEqual(choose_direction_best([
                dict(direction='PUMP_TO_METEORA',start=10_000_000,local_net=-1)]),{})
        def test_independent_worker_import(self):
            self.assertIn('q25',FREEZE);self.assertIn('q20',FREEZE);self.assertIn('q18',FREEZE)
        def test_frozen_source_paths(self):self.assertEqual(set(FREEZE),{'q18','q20','q25'})
    import unittest.mock
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(T)
    r=unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if r.wasSuccessful() else 1

def main():
    ap=argparse.ArgumentParser()
    m=ap.add_mutually_exclusive_group(required=True)
    for f in ('test','audit','status','run','stage'):m.add_argument('--'+f,action='store_true')
    ap.add_argument('--seconds',type=int,default=3600)
    ap.add_argument('--epochs',type=int,default=0,help='0=continuous, restart only between long scanner epochs')
    ap.add_argument('--pairs',type=int,default=28);ap.add_argument('--accounts',type=int,default=1280)
    ap.add_argument('--worker',action='store_true',help=argparse.SUPPRESS)
    ap.add_argument('--epoch',type=int,default=1,help=argparse.SUPPRESS)
    ap.add_argument('--producer',default='',help=argparse.SUPPRESS)
    ap.add_argument('--stage-interval',type=int,default=180)
    a=ap.parse_args()
    if a.stage:return stage_discovery()
    if a.test:return tests()
    if a.audit:emit('BOSS322_FROZEN_AUDIT',audit());return 0
    if a.status:
        emit('BOSS322_STATUS',json.loads(STATUS.read_text()) if STATUS.is_file() else {'status':'NOT_STARTED'});return 0
    if not 1<=a.pairs<=28 or a.accounts<256 or a.seconds<60 or a.epochs<0:raise RuntimeError('INVALID_SCANNER_CONFIGURATION')
    if not a.worker:
        if not os.getenv('SOLANA_RPC_URL','').startswith('https://') or not os.getenv('SOLANA_WS_URL','').startswith('wss://'):
            raise RuntimeError('RPC_WS_REQUIRED')
        # Parent stays alive while children are cleanly reconstructed at each epoch boundary.
        with one_process():
            frozen=audit()
            if BASELINE.is_file() and json.loads(BASELINE.read_text(encoding='utf-8'))!=frozen:
                raise RuntimeError('FROZEN_Q25_Q20_Q18_HASH_CHANGED_REFUSE_START')
            if not BASELINE.is_file():save(BASELINE,frozen)
            epoch=1;prod=uuid.uuid4().hex
            stage_stop=threading.Event()
            def stage_loop():
                while not stage_stop.wait(max(120,a.stage_interval)):
                    e=os.environ.copy();e.pop('QSB_SOLANA_PRIVATE_KEY',None);e['QSB_LIVE_ARM']='NO'
                    try:subprocess.run([sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.boss_scanner_live','--stage'],
                          env=e,timeout=90,check=False)
                    except (OSError,subprocess.TimeoutExpired):pass
            stage_thread=threading.Thread(target=stage_loop,daemon=True,name='boss322-discovery-stage')
            stage_thread.start()
            try:
                while a.epochs==0 or epoch<=a.epochs:
                    e=os.environ.copy();e.pop('QSB_SOLANA_PRIVATE_KEY',None);e['QSB_LIVE_ARM']='NO'
                    cmd=[sys.executable,'-m','qseries_v2.oracle_execution.solana_atomic_executor.boss_scanner_live',
                     '--run','--worker','--seconds',str(a.seconds),'--pairs',str(a.pairs),'--accounts',str(a.accounts),
                     '--epoch',str(epoch),'--producer',prod]
                    rc=subprocess.call(cmd,env=e)
                    if rc:
                        emit('BOSS322_EPOCH_RESTART',dict(epoch=epoch,returncode=rc,backoff_s=5));time.sleep(5)
                    epoch+=1
            finally:stage_stop.set()
        return 0
    if os.getenv('QSB_SOLANA_PRIVATE_KEY') or os.getenv('QSB_LIVE_ARM','NO').upper()!='NO':raise RuntimeError('SCANNER_SECRET_ISOLATION_REQUIRED')
    if not a.producer:raise RuntimeError('PRODUCER_ID_REQUIRED')
    return scan_epoch(a.seconds,a.pairs,a.accounts,a.epoch,a.producer)
if __name__=='__main__':raise SystemExit(main())
