from pathlib import Path
T=Path("mtr_044_exact_pair_intersection.cjs")
J=r'''const fs=require("fs"),{Connection,PublicKey}=require("@solana/web3.js");
const M=require("@meteora-ag/dlmm"),DLMM=M.default||M.DLMM||M;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const c=new Connection(RPC,"confirmed"),PUMP=new PublicKey("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
const DISC=Buffer.from("f19a6d0411b16dbc","hex");
const key=v=>!v?null:typeof v==="string"?v:typeof v.toBase58==="function"?v.toBase58():v.address||null;
const pair=(a,b)=>a<b?`${a}|${b}`:`${b}|${a}`;
function pk(b,o){try{return new PublicKey(b.subarray(o,o+32)).toBase58()}catch{return null}}
async function main(){
 console.log("[MTR-044] START");console.log("[SCOPE] exact two-mint pair intersection; no signing; no sending");
 const mr=await DLMM.getLbPairs(c),rows=Array.isArray(mr)?mr:mr?.pairs||mr?.lbPairs||[],mi=new Map();
 for(const r of rows){const a=r.account||r,p=key(r.publicKey||r.pubkey),x=key(a.tokenXMint||a.tokenX?.mint),y=key(a.tokenYMint||a.tokenY?.mint);
  if(!p||!x||!y||x===y)continue;const k=pair(x,y);if(!mi.has(k))mi.set(k,[]);
  mi.get(k).push({lb_pair:p,token_x:x,token_y:y})}
 console.log(`[METEORA_LBPAIR_COUNT] ${rows.length}`);console.log(`[METEORA_EXACT_PAIR_KEYS] ${mi.size}`);
 const pa=await c.getProgramAccounts(PUMP,{commitment:"confirmed",encoding:"base64",dataSlice:{offset:0,length:107},filters:[{dataSize:301}]});
 let verified=0;const hits=[];
 for(const r of pa){const d=Array.isArray(r.account.data)?r.account.data[0]:r.account.data,b=Buffer.from(d,"base64");
  if(b.length<107||!b.subarray(0,8).equals(DISC))continue;
  const base=pk(b,43),quote=pk(b,75);if(!base||!quote||base===quote)continue;verified++;
  const mm=mi.get(pair(base,quote));if(mm)hits.push({pump_pool:r.pubkey.toBase58(),base_mint:base,quote_mint:quote,meteora_pairs:mm})}
 hits.sort((a,b)=>b.meteora_pairs.length-a.meteora_pairs.length);
 fs.writeFileSync("mtr_044_exact_pairs.json",JSON.stringify({schema:"MTR-044",execution_authority:false,
  signing:false,sending:false,verified_pumpswap_pools:verified,meteora_pair_keys:mi.size,
  exact_pair_intersections:hits.length,candidates:hits},null,2));
 console.log(`[VERIFIED_PUMPSWAP_POOL_COUNT] ${verified}`);
 console.log(`[EXACT_PAIR_INTERSECTION_COUNT] ${hits.length}`);
 for(const x of hits.slice(0,100))console.log(`[EXACT_PAIR] pump=${x.pump_pool} base=${x.base_mint} quote=${x.quote_mint} meteora_count=${x.meteora_pairs.length} meteora=${x.meteora_pairs.map(z=>z.lb_pair).join(",")}`);
 console.log(hits.length?"[RESULT] EXACT_CROSS_VENUE_PAIRS_FOUND":"[RESULT] NO_EXACT_CROSS_VENUE_PAIRS");
 console.log(hits.length?"[NEXT_GATE] EXACT_BIDIRECTIONAL_EXECUTABLE_QUOTES":"[NEXT_GATE] REASSESS_ROUTE_TOPOLOGY");
 console.log("[OUTPUT] mtr_044_exact_pairs.json");console.log("[MTR-044] COMPLETE");
}
main().catch(e=>{console.error("[MTR-044] FAIL");console.error(e?.stack||e);process.exit(1)});'''
T.write_text(J,encoding="utf-8")
print(f"[BUILD] wrote {T}")
print("[BUILD] exact unordered PumpSwap pair -> Meteora pair intersection")
print("[SCOPE] read-only; no signing; no sending; canonical executor untouched")