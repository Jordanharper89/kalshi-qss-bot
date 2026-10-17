const fs=require("fs");

console.log("[MTR-102] START");
console.log("[SCOPE] tiered replenishment manifest from physical Pump reserves; local only");

const src="mtr_100_new_pool_physical_liquidity.json";
if(!fs.existsSync(src))throw Error("MTR_100_NOT_FOUND");

const j=JSON.parse(fs.readFileSync(src,"utf8"));
const rows=Array.isArray(j.rows)?j.rows:[];

function tier(sol){
 if(sol>=100)return "ULTRA_HOT";
 if(sol>=50)return "HOT";
 if(sol>=25)return "ACTIVE";
 return "BACKGROUND";
}

const out={
 ULTRA_HOT:[],
 HOT:[],
 ACTIVE:[],
 BACKGROUND:[]
};

for(const r of rows){
 const q=Number(r.quote_sol||0);
 out[tier(q)].push({
  pump_pool:r.pump_pool,
  base_mint:r.base_mint,
  quote_sol:q,
  meteora_count:Number(r.meteora_count||0),
  meteora_pools:r.meteora_pools||[],
  base_raw:r.base_raw,
  quote_raw:r.quote_raw
 });
}

for(const k of Object.keys(out))
 out[k].sort((a,b)=>b.quote_sol-a.quote_sol);

function links(a){
 return a.reduce((n,r)=>n+r.meteora_count,0);
}

console.log(`[TIER] ULTRA_HOT pools=${out.ULTRA_HOT.length} links=${links(out.ULTRA_HOT)}`);
console.log(`[TIER] HOT pools=${out.HOT.length} links=${links(out.HOT)}`);
console.log(`[TIER] ACTIVE pools=${out.ACTIVE.length} links=${links(out.ACTIVE)}`);
console.log(`[TIER] BACKGROUND pools=${out.BACKGROUND.length} links=${links(out.BACKGROUND)}`);

const flat=[];
for(const r of out.ULTRA_HOT){
 for(const m of r.meteora_pools){
  flat.push({
   tier:"ULTRA_HOT",
   pump_pool:r.pump_pool,
   meteora_pool:m,
   base_mint:r.base_mint,
   quote_sol:r.quote_sol
  });
 }
}

fs.writeFileSync("mtr_102_tiered_replenishment_manifest.json",
 JSON.stringify({
  thresholds:{
   ultra_hot_min_sol:100,
   hot_min_sol:50,
   active_min_sol:25
  },
  target_trade_sol:0.010,
  tiers:out,
  ultra_hot_links:flat
 },null,2));

console.log(`[ULTRA_HOT_FLAT_LINKS] ${flat.length}`);

for(const r of out.ULTRA_HOT.slice(0,20))
 console.log(`[ULTRA] sol=${r.quote_sol.toFixed(6)} pump=${r.pump_pool} meteora=${r.meteora_count} base=${r.base_mint}`);

console.log("[RESULT] TIERED_REPLENISHMENT_MANIFEST_BUILT");
console.log("[OUTPUT] mtr_102_tiered_replenishment_manifest.json");
console.log("[RPC] NOT_USED");
console.log("[PRIVATE_KEY] NOT_USED");
console.log("[BROADCAST] FALSE");
console.log("[MTR-102] COMPLETE");
