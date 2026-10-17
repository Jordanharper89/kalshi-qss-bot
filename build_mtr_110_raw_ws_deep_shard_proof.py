from pathlib import Path

p=Path("mtr_110_raw_ws_deep_shard_proof.cjs")
p.write_text(r'''const fs=require("fs");
const WebSocket=require("ws");

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const WS=process.env.QSB_SOLANA_WS_URL||
RPC.replace(/^https:/,"wss:").replace(/^http:/,"ws:");
const WATCH_MS=60000,ROUTES=12;

function sleep(ms){return new Promise(r=>setTimeout(r,ms))}
function add(m,k,v){if(!m.has(k))m.set(k,[]);m.get(k).push(v)}

(async()=>{
 console.log("[MTR-110] START");
 console.log("[SCOPE] raw WebSocket bounded deep-route shard proof");

 const j105=JSON.parse(fs.readFileSync("mtr_105_ultra_hot_meteora_reserve_filter.json","utf8"));
 const j100=JSON.parse(fs.readFileSync("mtr_100_new_pool_physical_liquidity.json","utf8"));

 const pump=new Map((j100.rows||[]).map(r=>[r.pump_pool,r]));
 const deep=(j105.rows||[])
  .filter(r=>Number(r.meteora_wsol_sol)>=1)
  .sort((a,b)=>Number(b.meteora_wsol_sol)-Number(a.meteora_wsol_sol))
  .slice(0,ROUTES);

 const acctRoutes=new Map();
 for(const r of deep){
  const p=pump.get(r.pump_pool);
  if(!p?.quote_vault)continue;
  const route={pump_pool:r.pump_pool,meteora_pool:r.meteora_pool,base_mint:r.base_mint};
  add(acctRoutes,p.quote_vault,{venue:"PUMP",...route});
  add(acctRoutes,r.wsol_reserve,{venue:"METEORA",...route});
 }

 console.log(`[ROUTES] ${deep.length}`);
 console.log(`[ACCOUNTS] ${acctRoutes.size}`);
 console.log(`[WS] ${WS}`);

 const ws=new WebSocket(WS);
 const pending=new Map(),subToAccount=new Map(),events=[];
 let nextId=1;

 ws.on("message",buf=>{
  let m;
  try{m=JSON.parse(buf.toString())}catch{return}

  if(m.id&&pending.has(m.id)){
   const x=pending.get(m.id);pending.delete(m.id);x(m);return;
  }

  if(m.method==="accountNotification"){
   const sid=String(m.params?.subscription);
   const account=subToAccount.get(sid);
   if(!account)return;
   const routes=acctRoutes.get(account)||[];
   const e={time:new Date().toISOString(),slot:m.params?.result?.context?.slot,
    account,routes};
   events.push(e);
   console.log(`[EVENT] slot=${e.slot} account=${account} affected=${routes.length}`);
  }
 });

 await new Promise((resolve,reject)=>{
  const t=setTimeout(()=>reject(Error("WS_OPEN_TIMEOUT")),10000);
  ws.once("open",()=>{clearTimeout(t);resolve()});
  ws.once("error",reject);
 });

 console.log("[WS_OPEN] TRUE");

 async function subscribe(account){
  const id=nextId++;
  const response=new Promise((resolve,reject)=>{
   const t=setTimeout(()=>{
    pending.delete(id);reject(Error("SUBSCRIBE_TIMEOUT"));
   },7000);
   pending.set(id,m=>{clearTimeout(t);resolve(m)});
  });

  ws.send(JSON.stringify({
   jsonrpc:"2.0",id,method:"accountSubscribe",
   params:[account,{encoding:"base64",commitment:"confirmed"}]
  }));

  const r=await response;
  if(r.error)throw Error(JSON.stringify(r.error));
  subToAccount.set(String(r.result),account);
  return r.result;
 }

 let ok=0,fail=0;
 for(const account of acctRoutes.keys()){
  try{
   const sid=await subscribe(account);
   ok++;
   console.log(`[SUBSCRIBED] ${ok}/${acctRoutes.size} sid=${sid} account=${account}`);
  }catch(e){
   fail++;
   console.log(`[SUBSCRIBE_FAIL] account=${account} reason=${String(e.message||e)}`);
  }
  await sleep(250);
 }

 console.log(`[READY] subscriptions=${ok} failures=${fail} watch_seconds=${WATCH_MS/1000}`);
 await sleep(WATCH_MS);

 const affected=new Set();
 for(const e of events)
  for(const r of e.routes)affected.add(`${r.pump_pool}|${r.meteora_pool}`);

 fs.writeFileSync("mtr_110_raw_ws_deep_shard_proof.json",JSON.stringify({
  routes:deep.length,accounts:acctRoutes.size,subscriptions:ok,failures:fail,
  events:events.length,affected_routes:affected.size,observations:events
 },null,2));

 console.log(`[SUMMARY] routes=${deep.length} accounts=${acctRoutes.size} subscriptions=${ok} failures=${fail} events=${events.length} affected_routes=${affected.size}`);
 console.log(ok===acctRoutes.size?
  "[RESULT] RAW_WS_SHARD_SUBSCRIPTIONS_PASS":
  "[RESULT] RAW_WS_SHARD_SUBSCRIPTIONS_INCOMPLETE");
 console.log("[OUTPUT] mtr_110_raw_ws_deep_shard_proof.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-110] COMPLETE");
 ws.close();
})().catch(e=>{
 console.error("[MTR-110] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] raw WebSocket bounded deep-route shard proof")
print("[SCOPE] 12 deepest routes; sequential subscribe acknowledgements; no pricing/signing/sending")