const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const WATCH_MS=90000;
const c=new Connection(RPC,"confirmed");
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function mapPush(m,k,v){
 if(!m.has(k))m.set(k,[]);
 m.get(k).push(v);
}

(async()=>{
 console.log("[MTR-109] START");
 console.log("[SCOPE] event-driven deep-route trigger lane; no pricing; no signing; no sending");

 const f105="mtr_105_ultra_hot_meteora_reserve_filter.json";
 const f100="mtr_100_new_pool_physical_liquidity.json";
 if(!fs.existsSync(f105))throw Error("MTR_105_NOT_FOUND");
 if(!fs.existsSync(f100))throw Error("MTR_100_NOT_FOUND");

 const j105=JSON.parse(fs.readFileSync(f105,"utf8"));
 const j100=JSON.parse(fs.readFileSync(f100,"utf8"));

 const deep=(j105.rows||[]).filter(r=>Number(r.meteora_wsol_sol)>=1);
 const pumpMap=new Map((j100.rows||[]).map(r=>[r.pump_pool,r]));

 const accountRoutes=new Map();

 for(const r of deep){
  const p=pumpMap.get(r.pump_pool);
  if(!p||!p.quote_vault)continue;

  const route={
   pump_pool:r.pump_pool,
   meteora_pool:r.meteora_pool,
   base_mint:r.base_mint
  };

  mapPush(accountRoutes,p.quote_vault,{venue:"PUMP",...route});
  mapPush(accountRoutes,r.wsol_reserve,{venue:"METEORA",...route});
 }

 console.log(`[DEEP_LINKS] ${deep.length}`);
 console.log(`[TRIGGER_ACCOUNTS] ${accountRoutes.size}`);

 const events=[],subs=[];
 let subscribed=0,fail=0;

 for(const [addr,routes] of accountRoutes){
  try{
   const id=c.onAccountChange(
    new PublicKey(addr),
    (info,ctx)=>{
     const now=new Date().toISOString();
     const e={
      time:now,
      slot:ctx.slot,
      account:addr,
      routes
     };
     events.push(e);
     console.log(
      `[EVENT] time=${now} slot=${ctx.slot} account=${addr} affected=${routes.length} venues=${[...new Set(routes.map(x=>x.venue))].join(",")}`
     );
    },
    "confirmed"
   );
   subs.push(id);
   subscribed++;
  }catch(e){
   fail++;
  }

  if(subscribed%50===0)
   console.log(`[SUBSCRIBE] ok=${subscribed} fail=${fail}`);

  await sleep(20);
 }

 console.log(`[READY] subscriptions=${subscribed} failed=${fail} watch_seconds=${WATCH_MS/1000}`);
 console.log("[WATCH] waiting for physical account-change events");

 await sleep(WATCH_MS);

 const affected=new Set();
 for(const e of events)
  for(const r of e.routes)
   affected.add(`${r.pump_pool}|${r.meteora_pool}`);

 for(const id of subs){
  try{await c.removeAccountChangeListener(id)}catch{}
 }

 fs.writeFileSync("mtr_109_deep_event_trigger_lane.json",
  JSON.stringify({
   deep_links:deep.length,
   trigger_accounts:accountRoutes.size,
   subscriptions:subscribed,
   subscription_failures:fail,
   events:events.length,
   affected_routes:affected.size,
   observations:events
  },null,2));

 console.log(`[SUMMARY] deep_links=${deep.length} trigger_accounts=${accountRoutes.size} subscriptions=${subscribed} failures=${fail} events=${events.length} affected_routes=${affected.size}`);

 console.log(events.length?
  "[RESULT] DEEP_EVENT_TRIGGER_LANE_PHYSICALLY_ACTIVE":
  "[RESULT] NO_ACCOUNT_CHANGE_OBSERVED_IN_WINDOW");

 console.log("[OUTPUT] mtr_109_deep_event_trigger_lane.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-109] COMPLETE");
 process.exit(0);
})().catch(e=>{
 console.error("[MTR-109] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
