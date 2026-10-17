const fs=require("fs");

console.log("[MTR-101] START");
console.log("[SCOPE] local liquidity-threshold surface; no RPC; no pricing");

const src="mtr_100_new_pool_physical_liquidity.json";
if(!fs.existsSync(src))throw Error("MTR_100_NOT_FOUND");

const j=JSON.parse(fs.readFileSync(src,"utf8"));
const rows=Array.isArray(j.rows)?j.rows:[];
const TH=[0.01,0.025,0.05,0.10,0.25,0.50,1,2,5,10,25,50,100];

console.log(`[INPUT_ROWS] ${rows.length}`);

const result=[];
for(const t of TH){
 const keep=rows.filter(r=>Number(r.quote_sol)>=t);
 const links=keep.reduce((n,r)=>n+Number(r.meteora_count||0),0);
 const bases=new Set(keep.map(r=>r.base_mint)).size;
 result.push({min_quote_sol:t,pools:keep.length,links,bases});
 console.log(`[THRESHOLD] min_sol=${t} pools=${keep.length} exact_links=${links} unique_bases=${bases}`);
}

const sorted=rows.slice().sort((a,b)=>Number(b.quote_sol)-Number(a.quote_sol));
const pct=[0.50,0.75,0.90,0.95,0.99];

for(const q of pct){
 if(!sorted.length)break;
 const i=Math.min(sorted.length-1,Math.floor((sorted.length-1)*q));
 const ascending=sorted.slice().reverse();
 console.log(`[PERCENTILE] p${Math.round(q*100)} quote_sol=${Number(ascending[i].quote_sol).toFixed(9)}`);
}

const target=0.010;
for(const mult of [2,5,10,25,50,100]){
 const min=target*mult;
 const keep=rows.filter(r=>Number(r.quote_sol)>=min);
 const links=keep.reduce((n,r)=>n+Number(r.meteora_count||0),0);
 console.log(`[HEADROOM] trade_sol=${target.toFixed(3)} reserve_multiple=${mult} min_reserve=${min.toFixed(3)} pools=${keep.length} exact_links=${links}`);
}

fs.writeFileSync("mtr_101_liquidity_threshold_surface.json",
 JSON.stringify({input_rows:rows.length,thresholds:result,target_trade_sol:target},null,2));

console.log("[RESULT] LIQUIDITY_THRESHOLD_SURFACE_CAPTURED");
console.log("[OUTPUT] mtr_101_liquidity_threshold_surface.json");
console.log("[RPC] NOT_USED");
console.log("[PRIVATE_KEY] NOT_USED");
console.log("[BROADCAST] FALSE");
console.log("[MTR-101] COMPLETE");
