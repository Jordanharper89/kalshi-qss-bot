from pathlib import Path

Path("mtr_118_target_only_24_meta.cjs").write_text(r'''const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const W="So11111111111111111111111111111111111111112";
const c=new Connection(RPC,"confirmed"),sleep=m=>new Promise(r=>setTimeout(r,m));
(async()=>{
 console.log("[MTR-118-META] START");
 const j=JSON.parse(fs.readFileSync("mtr_105_ultra_hot_meteora_reserve_filter.json","utf8"));
 const src=(j.rows||[]).filter(r=>Number(r.meteora_wsol_sol)>=1)
  .sort((a,b)=>Number(b.meteora_wsol_sol)-Number(a.meteora_wsol_sol));
 const by=new Map();
 for(const r of src){
  if(!by.has(r.pump_pool))by.set(r.pump_pool,[]);
  const g=by.get(r.pump_pool);
  if(!g.some(x=>x.meteora_pool===r.meteora_pool))g.push(r);
 }
 const chosen=[];
 for(const g of by.values()){
  for(const r of g.slice(0,2)){chosen.push(r);if(chosen.length>=24)break}
  if(chosen.length>=24)break;
 }
 if(chosen.length<16)throw Error("INSUFFICIENT_TARGET_ROUTES:"+chosen.length);
 const out=[];
 for(let i=0;i<chosen.length;i++){
  const r=chosen[i];
  for(let a=1;a<=6;a++){
   try{
    const m=await DLMM.create(c,new PublicKey(r.meteora_pool));
    const x=String(m.tokenX.mint.address),y=String(m.tokenY.mint.address);
    if(!([x,y].includes(W)&&[x,y].includes(r.base_mint)))throw Error("PAIR_MINT_MISMATCH");
    out.push({...r,token_x:x,token_y:y});break;
   }catch(e){
    if(a===6)console.log(`[META_HOLD] pump=${r.pump_pool} reason=${String(e.message||e)}`);
    else await sleep(Math.min(600*(2**(a-1)),5000));
   }
  }
  console.log(`[META_PROGRESS] ${i+1}/${chosen.length} exact=${out.length}`);
  await sleep(500);
 }
 fs.writeFileSync("mtr_118_target_only_24_meta.json",JSON.stringify(out,null,2));
 console.log(`[META_SUMMARY] selected=${chosen.length} exact=${out.length}`);
 console.log("[MTR-118-META] COMPLETE");
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
''',encoding="utf-8")

Path("mtr_118_target_only_24_route_scale.py").write_text(r'''from __future__ import annotations
import json,time
from pathlib import Path
from collections import defaultdict
from qseries_v2.oracle_execution import oracle_018_exact_sdk_hot_lane_cutover as q18
from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m

META=Path("mtr_118_target_only_24_meta.json")
OUT=Path("mtr_118_target_only_24_route_scale.json")
ST={"pairs":0,"tokens":0,"accounts":0,"shared":0,"max_fanout":0,"fanout_events":0,"fanout_submissions":0}
PAIRS=[]

def dec(x):
 raw,_=c.account(x)
 if len(raw)<45:raise RuntimeError("MINT_SHORT")
 return int(raw[44])

def one(r):
 raw,_=c.account(r["pump_pool"]);pp=c.decode_pump_pool(raw)
 if pp["quote_mint"]!=c.WSOL:raise RuntimeError("PUMP_NOT_WSOL")
 br,_=c.account(pp["base_vault"]);qr,_=c.account(pp["quote_vault"])
 lb,_=c.account(r["meteora_pool"]);arr=c.dlmm_arrays(r["meteora_pool"])
 p=pd.PairState(r["base_mint"],r["pump_pool"],r["meteora_pool"],r["token_x"],r["token_y"],
  dec(r["token_x"]),dec(r["token_y"]),pp["base_vault"],pp["quote_vault"],
  pd._token_amount_from_raw(br),pd._token_amount_from_raw(qr),lb,list(arr),None)
 p.dlmm_state=pd._build_dlmm_state(p);return p

def hydrate(r):
 last=None
 for a in range(1,8):
  try:return one(r)
  except Exception as e:
   last=e
   if "429" not in str(e):raise
   time.sleep(min(.75*(2**(a-1)),6))
 raise last

def prepare_once(root):
 global PAIRS
 rows=json.loads(META.read_text(encoding="utf-8"));pairs=[]
 for n,r in enumerate(rows,1):
  try:
   t=time.perf_counter_ns();p=hydrate(r);pairs.append(p)
   print("[MTR118_WARM] %d/%d token=%s arrays=%d ms=%.1f"%(n,len(rows),p.token[:10],len(p.arrays),(time.perf_counter_ns()-t)/1e6),flush=True)
  except Exception as e:print("[MTR118_HOLD] %s:%s"%(type(e).__name__,str(e)[:160]),flush=True)
  time.sleep(.45)
 if len(pairs)<16:raise RuntimeError("MTR118_TOO_FEW_HYDRATED:"+str(len(pairs)))
 multi={};single={}
 for i,p in enumerate(pairs):
  refs=[(p.pump_base_vault,"PUMP_BASE"),(p.pump_quote_vault,"PUMP_QUOTE"),(p.meteora_pool,"DLMM_POOL")]
  refs += [(a[1],"DLMM_ARRAY_%d"%j) for j,a in enumerate(p.arrays)]
  for addr,k in refs:
   multi.setdefault(addr,[]).append((i,k));single.setdefault(addr,(i,k))
 eps=defaultdict(list)
 for p in pairs:eps[p.token].extend((m._pump_ep(p),m._dlmm_ep(p)))
 state={"landing":0,"pairs":pairs,"preg":single,"preg_multi":multi,"cstates":[],"creg":{},
        "observed":{},"xreg":{},"eps":eps,"addresses":list(multi)}
 PAIRS=pairs
 ST.update(pairs=len(pairs),tokens=len({p.token for p in pairs}),accounts=len(multi),
           shared=sum(len(v)>1 for v in multi.values()),max_fanout=max(map(len,multi.values())))
 print("[MTR118_TARGET] pairs=%d tokens=%d accounts=%d shared=%d max_fanout=%d"%(
  ST["pairs"],ST["tokens"],ST["accounts"],ST["shared"],ST["max_fanout"]),flush=True)
 return state,{"PUMPSWAP":{"priced_live":True},"METEORA_DLMM":{"priced_live":True}}

def process(state,ev,counter,sim_lane):
 refs=state.get("preg_multi",{}).get(ev["address"])
 if not refs:return
 if len(refs)>1:ST["fanout_events"]+=1
 for i,k in refs:
  p=state["pairs"][i]
  try:changed=pd.apply_account_event(p,k,ev["address"],ev["raw"],ev["slot"],ev["received_ns"])
  except Exception:counter["event_errors"]+=1;continue
  if not changed:continue
  counter["priced_events"]+=1
  key="%s|%s|%s"%(p.token,p.pump_pool,p.meteora_pool)
  q20._lane.submit(key,q20._pair_snapshot(p),ev["slot"],ev["received_ns"])
  if len(refs)>1:ST["fanout_submissions"]+=1

orig_install=q20.install
def install():
 lane=orig_install();seen=set()
 for p in PAIRS:
  if p.pump_pool in seen:continue
  seen.add(p.pump_pool);q18.worker().warm(p.pump_pool);lane.warmed.add(p.pump_pool)
 print("[MTR118_PREWARM] pumps=%d failures=0"%len(seen),flush=True)
 return lane

def main():
 print("[MTR-118] START",flush=True)
 print("[SCOPE] target-only 24-route exact 0.010 warm scale",flush=True)
 q20.FAST_SIZES=(0.010,);q20.FULL_SIZE_CURVE=(0.010,);q20.EXPAND_SIZES=()
 q20._patched_process_event=process;q20.install=install;q25.prepare_once=prepare_once
 m.MAX_ACCOUNTS=2048;m.SHARD_SIZE=48
 rc=q25.run(seconds=90.0)
 r=json.loads(Path("runtime_state/oracle/oracle_live_execution/oracle_020_latest_state_exact_pricing_worker.json").read_text())
 out={**ST,"submitted":r.get("submitted"),"processed":r.get("processed"),"stale":r.get("stale_drops"),
      "positive":r.get("positive"),"best":r.get("best"),"p99_start_ms":r.get("p99_event_start_ms"),
      "p99_scan_ms":r.get("p99_scan_ms"),"return_code":rc,"execution_authority":False,
      "broadcast":False,"private_key_used":False}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True,default=str),encoding="utf-8")
 print("[SUMMARY] pairs=%d tokens=%d accounts=%d fanout_events=%d submitted=%s processed=%s stale=%s positive=%s p99_start_ms=%s p99_scan_ms=%s"%(
  ST["pairs"],ST["tokens"],ST["accounts"],ST["fanout_events"],out["submitted"],out["processed"],out["stale"],
  out["positive"],out["p99_start_ms"],out["p99_scan_ms"]),flush=True)
 ok=ST["pairs"]>=16 and int(out["processed"] or 0)>0 and int(out["stale"] or 0)==0 and float(out["p99_start_ms"] or 1e9)<250
 print("[RESULT] TARGET_ONLY_24_ROUTE_SCALE_PASS" if ok else "[RESULT] TARGET_ONLY_24_ROUTE_SCALE_NOT_CERTIFIED",flush=True)
 if int(out["positive"] or 0)>0:print("[NEXT] FRESH_POSITIVE_PRESENT_FOR_ATOMIC_HANDOFF",flush=True)
 else:print("[NEXT] NO_010_POSITIVE_OBSERVED_IN_WINDOW",flush=True)
 print("[PRIVATE_KEY] NOT_USED");print("[BROADCAST] FALSE");print("[MTR-118] COMPLETE")
if __name__=="__main__":main()
''',encoding="utf-8")

print("[BUILD] wrote mtr_118_target_only_24_meta.cjs")
print("[BUILD] wrote mtr_118_target_only_24_route_scale.py")
print("[SCOPE] target-only exact 0.010 lane; no signing; no sending")
