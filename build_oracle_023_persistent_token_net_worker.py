from pathlib import Path
import py_compile, textwrap

ROOT=Path.cwd()
SUB=ROOT/'qseries_v2'/'oracle_execution'
NODE=ROOT/'qseries_v2'/'oracle_strategy_intelligence'/'solana_money'/'qsb059d_pump_native'
SUB.mkdir(parents=True,exist_ok=True)
NODE.mkdir(parents=True,exist_ok=True)

MOD=SUB/'oracle_023_persistent_token_net_worker.py'
TEST=ROOT/'test_oracle_023_persistent_token_net_worker.py'
RUN=ROOT/'run_oracle_023_persistent_token_net_worker.py'
JS=NODE/'oracle023_token_net_worker.mjs'

js_src=r'''
import readline from "node:readline";
import {createRequire} from "node:module";
const require=createRequire(import.meta.url);
const {Connection,PublicKey}=require("@solana/web3.js");
const {TOKEN_PROGRAM_ID,TOKEN_2022_PROGRAM_ID,getMint,getTransferFeeConfig,calculateEpochFee}=require("@solana/spl-token");
const rpc=process.env.SOLANA_RPC_URL || "https://api.mainnet-beta.solana.com";
const connection=new Connection(rpc,"confirmed");
const cache=new Map();
let epoch=null;
async function refreshEpoch(){ const e=await connection.getEpochInfo("confirmed"); epoch=BigInt(e.epoch); return epoch; }
async function warm(mintText){
  const mint=new PublicKey(mintText);
  const info=await connection.getAccountInfo(mint,"confirmed");
  if(!info) throw new Error("MINT_NOT_FOUND");
  if(info.owner.equals(TOKEN_PROGRAM_ID)){
    const row={program:TOKEN_PROGRAM_ID.toBase58(),cfg:null}; cache.set(mintText,row); return row;
  }
  if(!info.owner.equals(TOKEN_2022_PROGRAM_ID)) throw new Error("UNKNOWN_TOKEN_PROGRAM:"+info.owner.toBase58());
  const m=await getMint(connection,mint,"confirmed",TOKEN_2022_PROGRAM_ID);
  const cfg=getTransferFeeConfig(m);
  const row={program:TOKEN_2022_PROGRAM_ID.toBase58(),cfg}; cache.set(mintText,row);
  if(epoch===null) await refreshEpoch();
  return row;
}
async function net(mintText,grossText){
  let row=cache.get(mintText); if(!row) row=await warm(mintText);
  const gross=BigInt(String(grossText)); let fee=0n;
  if(row.program===TOKEN_2022_PROGRAM_ID.toBase58() && row.cfg){ if(epoch===null) await refreshEpoch(); fee=calculateEpochFee(row.cfg,epoch,gross); }
  const received=gross-fee; if(received<=0n) throw new Error("NET_RECEIVED_NONPOSITIVE");
  return {program:row.program,gross:gross.toString(),fee:fee.toString(),net:received.toString()};
}
const rl=readline.createInterface({input:process.stdin,crlfDelay:Infinity});
for await (const line of rl){
  if(!line.trim()) continue;
  let req;
  try{
    req=JSON.parse(line); let result;
    if(req.op==="warm") result=await warm(String(req.mint));
    else if(req.op==="net") result=await net(String(req.mint),String(req.gross));
    else if(req.op==="refresh_epoch") result={epoch:(await refreshEpoch()).toString()};
    else if(req.op==="stats") result={cached_mints:cache.size,epoch:epoch===null?null:epoch.toString()};
    else throw new Error("UNKNOWN_OP:"+req.op);
    console.log(JSON.stringify({id:req.id,ok:true,...result}));
  }catch(e){ console.log(JSON.stringify({id:req?.id ?? null,ok:false,reason:e?.stack ?? e?.message ?? String(e)})); }
}
'''

module_src=r'''
from __future__ import annotations
import argparse,json,os,statistics,subprocess,threading,time
from pathlib import Path
from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_019_venue_native_reserve_feed_cutover as q19
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REAL_MONEY_MOVED=False
NODEDIR=Path('qseries_v2/oracle_strategy_intelligence/solana_money/qsb059d_pump_native')
WORKER_JS=NODEDIR/'oracle023_token_net_worker.mjs'
_worker=None
class TokenNetWorker:
    def __init__(self):
        self.proc=subprocess.Popen(['node',WORKER_JS.name],cwd=str(NODEDIR),stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,env=dict(os.environ))
        self.lock=threading.Lock(); self.seq=0
    def request(self,payload):
        with self.lock:
            self.seq+=1; req={'id':self.seq,**payload}
            self.proc.stdin.write(json.dumps(req,separators=(',',':'))+'\n'); self.proc.stdin.flush()
            line=self.proc.stdout.readline()
            if not line:
                err=''
                try: err=self.proc.stderr.read()
                except Exception: pass
                raise RuntimeError('TOKEN_NET_WORKER_DIED:'+err[-2000:])
            row=json.loads(line)
            if int(row.get('id',-1))!=self.seq: raise RuntimeError('TOKEN_NET_RESPONSE_ORDER')
            if not row.get('ok'): raise RuntimeError('TOKEN_NET_WORKER:'+str(row.get('reason')))
            return row
    def warm(self,mint): return self.request({'op':'warm','mint':str(mint)})
    def net(self,mint,gross):
        row=self.request({'op':'net','mint':str(mint),'gross':int(gross)})
        return {'gross':int(row['gross']),'fee':int(row['fee']),'net':int(row['net']),'program':row.get('program')}
    def refresh_epoch(self): return self.request({'op':'refresh_epoch'})
    def stats(self): return self.request({'op':'stats'})
    def close(self):
        try:
            if self.proc.poll() is None: self.proc.terminate(); self.proc.wait(timeout=3)
        except Exception:
            try:self.proc.kill()
            except Exception:pass

def worker():
    global _worker
    if _worker is None: _worker=TokenNetWorker()
    return _worker

def token_net(mint,gross): return int(worker().net(mint,int(gross))['net'])
def install_hot_token_net(): q18.token_net=token_net; return token_net

def pct(xs,p):
    s=sorted(xs); return s[min(len(s)-1,int(len(s)*p))] if s else None

def run(iterations=20):
    state=q19.persistent.m.prepare(Path.cwd()); pairs=list(state.get('pairs') or [])
    if not pairs: raise RuntimeError('NO_LIVE_PAIR_STATE')
    mint=pairs[0].token; w=worker()
    t=time.perf_counter_ns(); warm=w.warm(mint); warm_ms=(time.perf_counter_ns()-t)/1e6; w.refresh_epoch()
    print('[ORACLE-023] PERSISTENT TOKEN NET WORKER',flush=True)
    print('[TOKEN] %s'%mint,flush=True)
    print('[WARM] program=%s warm_ms=%.3f'%(warm.get('program'),warm_ms),flush=True)
    print('[SEMANTICS] @solana/spl-token calculateEpochFee preserved',flush=True)
    print('[HOT_PATH] no RPC / no Node spawn per quote',flush=True)
    print('[PRIVATE_KEY] not required',flush=True); print('[BROADCAST] disabled',flush=True)
    gross_values=(1000,10000,100000,1000000)
    old_rows={g:q18.q14.engine.net_received(mint,g) for g in gross_values}
    vals=[]
    for g in gross_values:
        for i in range(int(iterations)):
            t=time.perf_counter_ns(); new=w.net(mint,g); ms=(time.perf_counter_ns()-t)/1e6; vals.append(ms)
            if new!=old_rows[g]: raise RuntimeError('PARITY_FAIL gross=%d old=%r new=%r'%(g,old_rows[g],new))
        print('[ORACLE023_PARITY] gross=%d fee=%d net=%d calls=%d'%(g,new['fee'],new['net'],iterations),flush=True)
    summary={'calls':len(vals),'p50_ms':statistics.median(vals),'p95_ms':pct(vals,.95),'max_ms':max(vals),'warm_ms':warm_ms,'worker_stats':w.stats()}
    report={'oracle_build':'ORACLE-023','token':mint,'summary':summary,'exact_parity':True,'persistent_worker':True,'execution_authority':False,'paper_only':True,'real_money_moved':False,'broadcast':False}
    out=Path('runtime_state/oracle/oracle_live_execution/oracle_023_persistent_token_net_worker.json'); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    print('[ORACLE023_SUMMARY] '+json.dumps(summary,sort_keys=True),flush=True); print('[REPORT] %s'%out,flush=True); print('[BROADCAST] disabled',flush=True)
    return 0

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--iterations',type=int,default=20); a=ap.parse_args(argv); return run(a.iterations)
if __name__=='__main__': raise SystemExit(main())
'''

test_src=r'''
import inspect,unittest
from qseries_v2.oracle_execution import oracle_023_persistent_token_net_worker as q23
class T(unittest.TestCase):
    def test_safety(self): self.assertFalse(q23.EXECUTION_AUTHORITY); self.assertTrue(q23.PAPER_ONLY); self.assertFalse(q23.REAL_MONEY_MOVED)
    def test_persistent_process(self):
        s=inspect.getsource(q23.TokenNetWorker); self.assertIn('subprocess.Popen',s); self.assertNotIn('subprocess.run',s)
    def test_hot_patch(self): self.assertIn('q18.token_net=token_net',inspect.getsource(q23.install_hot_token_net))
    def test_no_private_key_or_broadcast(self):
        s=inspect.getsource(q23); self.assertNotIn('QSB_SOLANA_PRIVATE_KEY',s); self.assertNotIn('sendTransaction',s)
if __name__=='__main__': unittest.main(verbosity=2)
'''

run_src="""from qseries_v2.oracle_execution.oracle_023_persistent_token_net_worker import main\nif __name__=='__main__': raise SystemExit(main())\n"""

JS.write_text(textwrap.dedent(js_src).lstrip(),encoding='utf-8')
MOD.write_text(textwrap.dedent(module_src).lstrip(),encoding='utf-8')
TEST.write_text(textwrap.dedent(test_src).lstrip(),encoding='utf-8')
RUN.write_text(run_src,encoding='utf-8')
for f in (MOD,TEST,RUN): py_compile.compile(str(f),doraise=True)
print('[PASS] ORACLE-023 persistent token-net worker installed')
print('[SEMANTICS] same @solana/spl-token getMint/getTransferFeeConfig/calculateEpochFee')
print('[WARM] mint owner + Token-2022 config + epoch outside quote loop')
print('[HOT_PATH] persistent IPC; zero RPC and zero Node spawn per net quote')
print('[PARITY] physical old-vs-new output equality gate included')
print('[PRIVATE_KEY] not required')
print('[BROADCAST] disabled')
print('[OWNER] ORACLE')
