const fs=require("fs");
const {PublicKey}=require("@solana/web3.js");
const WSOL="So11111111111111111111111111111111111111112";
function addr(v){if(!v)return null;if(typeof v==="string")return v;if(v.lb_pair)return v.lb_pair;if(v.publicKey)return String(v.publicKey);if(v.pubkey)return String(v.pubkey);return null}
function main(){
 console.log("[MTR-045R] START");
 console.log("[SCOPE] MTR-044 contract normalization only; signing=false; sending=false; executor=false");
 if(!fs.existsSync("mtr_044_exact_pairs.json"))throw Error("MISSING_MTR_044_EXACT_PAIRS_JSON");
 const d=JSON.parse(fs.readFileSync("mtr_044_exact_pairs.json","utf8"));
 const rows=Array.isArray(d)?d:(d.candidates||d.exact_pairs||d.pairs||d.intersections||d.rows||[]);
 console.log(`[MTR044_SCHEMA_KEYS] ${Object.keys(d).join(",")}`);
 console.log(`[MTR044_ROW_COUNT] ${rows.length}`);
 if(!rows.length)throw Error("NO_MTR_044_ROWS_AFTER_CANDIDATES_NORMALIZATION");
 const out=[];
 for(const r of rows){
  const pump=r.pump_pool||r.pump||r.pumpPool||r.pool;
  const base=r.base_mint||r.base||r.baseMint,quote=r.quote_mint||r.quote||r.quoteMint;
  let ms=r.meteora_pairs||r.meteora_pools||r.meteoraPools||r.meteora||[];
  if(!Array.isArray(ms))ms=String(ms).split(",").filter(Boolean);
  ms=ms.map(addr).filter(Boolean);
  if(!pump||!base||!quote||!ms.length)continue;
  try{new PublicKey(pump);new PublicKey(base);new PublicKey(quote);for(const x of ms)new PublicKey(x)}catch{continue}
  if(base!==WSOL&&quote!==WSOL)continue;
  out.push({pump_pool:pump,base_mint:base,quote_mint:quote,meteora_pools:ms});
 }
 console.log(`[NORMALIZED_WSOL_EXACT_PAIR_ROWS] ${out.length}`);
 if(!out.length)throw Error("NO_NORMALIZED_WS0L_EXACT_PAIR_ROWS");
 let links=0;for(const r of out)links+=r.meteora_pools.length;
 console.log(`[NORMALIZED_PUMP_METEORA_LINKS] ${links}`);
 for(const r of out.slice(0,20))console.log(`[NORMALIZED] pump=${r.pump_pool} base=${r.base_mint} quote=${r.quote_mint} meteora_count=${r.meteora_pools.length} first_meteora=${r.meteora_pools[0]}`);
 fs.writeFileSync("mtr_045_normalized_exact_pairs.json",JSON.stringify({schema:"MTR-045R",source:"mtr_044_exact_pairs.json",execution_authority:false,signing:false,sending:false,rows:out},null,2));
 console.log("[RESULT] MTR044_EXACT_PAIR_CONTRACT_PHYSICALLY_NORMALIZED");
 console.log("[NEXT_GATE] LIVE_BIDIRECTIONAL_QUOTE_API_PROOF");
 console.log("[OUTPUT] mtr_045_normalized_exact_pairs.json");
 console.log("[MTR-045R] COMPLETE");
}
try{main()}catch(e){console.error("[MTR-045R] FAIL");console.error(e.stack||e);process.exit(1)}
