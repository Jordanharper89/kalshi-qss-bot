from pathlib import Path

Path("mtr_115_multi_link_meta.cjs").write_text(r'''const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W="So11111111111111111111111111111111111111112";
const c=new Connection(RPC,"confirmed"),sleep=m=>new Promise(r=>setTimeout(r,m));

(async()=>{
 console.log("[MTR-115-META] START");
 const j=JSON.parse(fs.readFileSync("mtr_105_ultra_hot_meteora_reserve_filter.json","utf8"));
 const src=(j.rows||[]).filter(r=>Number(r.meteora_wsol_sol)>=1)
  .sort((a,b)=>Number(b.meteora_wsol_sol)-Number(a.meteora_wsol_sol));

 const groups=new Map();
 for(const r of src){
  if(!groups.has(r.pump_pool))groups.set(r.pump_pool,[]);
  const a=groups.get(r.pump_pool);
  if(!a.some(x=>x.meteora_pool===r.meteora_pool))a.push(r);
 }
 const eligible=[...groups.values()].filter(x=>x.length>=2)
  .sort((a,b)=>Number(b[0].meteora_wsol_sol)-Number(a[0].meteora_wsol_sol));

 const chosen=[];
 for(const g of eligible){
  for(const r of g.slice(0,3)){chosen.push(r);if(chosen.length>=12)break}
  if(chosen.length>=12)break;
 }
 if(chosen.length<8)throw Error("INSUFFICIENT_MULTI_LINK_GROUPS");

 const out=[];
 for(let i=0;i<chosen.length;i++){
  const r=chosen[i];
  try{
   const m=await DLMM.create(c,new PublicKey(r.meteora_pool));
   const x=String(m.tokenX.mint.address),y=String(m.tokenY.mint.address);
   if(!([x,y].includes(W)&&[x,y].includes(r.base_mint)))throw Error("PAIR_MINT_MISMATCH");
   out.push({...r,token_x:x,token_y:y});
   console.log(`[META] ${out.length}/${chosen.length} pump=${r.pump_pool} meteora=${r.meteora_pool}`);
  }catch(e){console.log(`[META_HOLD] ${String(e.message||e)}`)}
  await sleep(650);
 }
 fs.writeFileSync("mtr_115_multi_link_meta.json",JSON.stringify(out,null,2));
 console.log(`[META_SUMMARY] selected=${chosen.length} exact=${out.length}`);
 console.log("[MTR-115-META] COMPLETE");
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
''',encoding="utf-8")

Path("mtr_115_route_keyed_multi_link_cutover.py").write_text(r'''from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_execution import oracle_020_latest_state_exact_pricing_worker as q20
from qseries_v2.oracle_execution import oracle_025_single_hydration_exact_live_reuse as q25
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import live_account_stream as pd
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import merged_live_runtime as m
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_060b_existing_runtime_multidex_cutover as q60b

META=Path("mtr_115_multi_link_meta.json");OUT=Path("mtr_115_route_keyed_multi_link_cutover.json")
ORIG=q60b._ORIG_PREPARE
ST={"pairs":0,"tokens":0,"shared_accounts":0,"max_fanout":0,"fanout_events":0,"fanout_submissions":0}

def dec(x):
 raw,_=c.account(x)
 if len(raw)<45:raise RuntimeError("MINT_SHORT")
 return int(raw[44])

def hydrate(r):
 raw,_=c.account(r["pump_pool"]);pp=c.decode_pump_pool(raw)
 br,_=c.account(pp["base_vault"]);qr,_=c.account(pp["quote_vault"])
 lb,_=c.account(r["meteora_pool"]);arrays=c.dlmm_arrays(r["meteora_pool"])
 p=pd.PairState(r["base_mint"],r["pump_pool"],r["meteora_pool"],r["token_x"],r["token_y"],
  dec(r["token_x"]),dec(r["token_y"]),pp["base_vault"],pp["quote_vault"],
  pd._token_amount_from_raw(br),pd._token_amount_from_raw(qr),lb,list(arrays),None)
 p.dlmm_state=pd._build_dlmm_state(p);return p

def prepare(root):
 state=ORIG(root);pairs=[]
 for r in json.loads(META.read_text(encoding="utf-8")):
  try:
   t=time.perf_counter_ns();p=hydrate(r);pairs.append(p)
   print("[MTR115_WARM] token=%s pump=%s arrays=%d warm_ms=%.3f"%(
    p.token[:10],p.pump_pool[:10],len(p.arrays),(time.perf_counter_ns()-t)/1e6),flush=True)
  except Exception as e:print("[MTR115_HOLD] %s:%s"%(type(e).__name__,e),flush=True)
  time.sleep(.3)
 if not pairs:raise RuntimeError("NO_MULTI_LINK_PAIRS")

 multi={};single={}
 for i,p in enumerate(pairs):
  rows=[(p.pump_base_vault,"PUMP_BASE"),(p.pump_quote_vault,"PUMP_QUOTE"),
        (p.meteora_pool,"DLMM_POOL")]+[(a[1],"DLMM_ARRAY_%d"%j) for j,a in enumerate(p.arrays)]
  for a,k in rows:
   multi.setdefault(a,[]).append((i,k));single.setdefault(a,(i,k))
 state["pairs"]=pairs;state["preg"]=single;state["preg_multi"]=multi

 for token in list(state["eps"]):
  state["eps"][token]=[e for e in state["eps"][token] if e.venue not in ("PUMPSWAP","METEORA_DLMM")]
 for p in pairs:state["eps"][p.token].extend((m._pump_ep(p),m._dlmm_ep(p)))

 ST["pairs"]=len(pairs);ST["tokens"]=len({p.token for p in pairs})
 ST["shared_accounts"]=sum(len(v)>1 for v in multi.values());ST["max_fanout"]=max(map(len,multi.values()))
 print("[MTR115_REGISTRY] pairs=%d tokens=%d accounts=%d shared=%d max_fanout=%d"%(
  ST["pairs"],ST["tokens"],len(multi),ST["shared_accounts"],ST["max_fanout"]),flush=True)
 return state

def process(state,ev,counter,sim_lane):
 refs=state.get("preg_multi",{}).get(ev["address"])
 if not refs:return q20._original_process_event(state,ev,counter,sim_lane)
 if len(refs)>1:ST["fanout_events"]+=1
 for i,kind in refs:
  p=state["pairs"][i]
  try:changed=pd.apply_account_event(p,kind,ev["address"],ev["raw"],ev["slot"],ev["received_ns"])
  except Exception:counter["event_errors"]+=1;continue
  if not changed:continue
  counter["priced_events"]+=1
  key="%s|%s|%s"%(p.token,p.pump_pool,p.meteora_pool)
  q20._lane.submit(key,q20._pair_snapshot(p),ev["slot"],ev["received_ns"])
  if len(refs)>1:ST["fanout_submissions"]+=1

def main():
 print("[MTR-115] START",flush=True)
 q60b._ORIG_PREPARE=prepare
 q20._patched_process_event=process
 rc=q25.run(seconds=60.0)
 r=json.loads(Path("runtime_state/oracle/oracle_live_execution/oracle_020_latest_state_exact_pricing_worker.json").read_text())
 out={**ST,"submitted":r.get("submitted"),"processed":r.get("processed"),"stale":r.get("stale_drops"),
      "positive":r.get("positive"),"p99_start_ms":r.get("p99_event_start_ms"),"p99_scan_ms":r.get("p99_scan_ms"),
      "return_code":rc,"execution_authority":False,"broadcast":False,"private_key_used":False}
 OUT.write_text(json.dumps(out,indent=2,sort_keys=True))
 print("[SUMMARY] pairs=%d tokens=%d shared=%d max_fanout=%d fanout_events=%d fanout_submissions=%d submitted=%s processed=%s stale=%s p99_start_ms=%s p99_scan_ms=%s"%(
  ST["pairs"],ST["tokens"],ST["shared_accounts"],ST["max_fanout"],ST["fanout_events"],ST["fanout_submissions"],
  out["submitted"],out["processed"],out["stale"],out["p99_start_ms"],out["p99_scan_ms"]),flush=True)
 ok=ST["pairs"]>ST["tokens"] and ST["shared_accounts"]>0 and ST["fanout_events"]>0 and int(out["processed"] or 0)>0
 print("[RESULT] ROUTE_KEYED_MULTI_LINK_FANOUT_PASS" if ok else "[RESULT] ROUTE_KEYED_MULTI_LINK_FANOUT_NOT_CERTIFIED",flush=True)
 print("[PRIVATE_KEY] NOT_USED");print("[BROADCAST] FALSE");print("[MTR-115] COMPLETE")

if __name__=="__main__":main()
''',encoding="utf-8")

print("[BUILD] wrote MTR-115 metadata + route-keyed warm cutover")
print("[SCOPE] duplicate-token exact routes; shared-account fanout; no signing; no sending")