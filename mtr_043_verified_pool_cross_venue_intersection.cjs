const fs=require("fs"),{Connection,PublicKey}=require("@solana/web3.js");
const M=require("@meteora-ag/dlmm"),DLMM=M.default||M.DLMM||M;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const c=new Connection(RPC,"confirmed"),PUMP=new PublicKey("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
const DISC=Buffer.from("f19a6d0411b16dbc","hex");
const key=v=>!v?null:typeof v==="string"?v:typeof v.toBase58==="function"?v.toBase58():v.address||null;
function pk(b,o){try{return new PublicKey(b.subarray(o,o+32)).toBase58()}catch{return null}}
async function main(){
 console.log("[MTR-043] START");console.log("[SCOPE] verified real-pool intersection; no signing; no sending");
 const mr=await DLMM.getLbPairs(c),rows=Array.isArray(mr)?mr:mr?.pairs||mr?.lbPairs||[],mints=new Set();
 for(const r of rows){const a=r.account||r,x=key(a.tokenXMint||a.tokenX?.mint),y=key(a.tokenYMint||a.tokenY?.mint);
  if(x)mints.add(x);if(y)mints.add(y)}
 console.log(`[METEORA_LBPAIR_COUNT] ${rows.length}`);console.log(`[METEORA_MINT_COUNT] ${mints.size}`);
 console.log("[PUMPSWAP] querying verified dataSize=301 pool class");
 const pa=await c.getProgramAccounts(PUMP,{commitment:"confirmed",encoding:"base64",
  dataSlice:{offset:0,length:107},filters:[{dataSize:301}]});
 console.log(`[PUMPSWAP_SIZE301_COUNT] ${pa.length}`);
 let verified=0;const cand=[],quotes=new Map();
 for(const r of pa){const d=Array.isArray(r.account.data)?r.account.data[0]:r.account.data,b=Buffer.from(d,"base64");
  if(b.length<107||!b.subarray(0,8).equals(DISC))continue;
  const base=pk(b,43),quote=pk(b,75);if(!base||!quote||base===quote)continue;verified++;
  quotes.set(quote,(quotes.get(quote)||0)+1);
  if(mints.has(base))cand.push({pump_pool:r.pubkey.toBase58(),base_mint:base,quote_mint:quote})}
 const qu=[...quotes].sort((a,b)=>b[1]-a[1]).map(([mint,pools])=>({mint,pools}));
 fs.writeFileSync("mtr_043_intersection.json",JSON.stringify({schema:"MTR-043",execution_authority:false,
  signing:false,sending:false,pool_size:301,discriminator:"f19a6d0411b16dbc",base_offset:43,
  quote_offset:75,meteora_mints:mints.size,verified_pumpswap_pools:verified,
  quote_universe:qu,overlap_count:cand.length,candidates:cand},null,2));
 console.log(`[VERIFIED_PUMPSWAP_POOL_COUNT] ${verified}`);console.log(`[PUMPSWAP_QUOTE_MINT_COUNT] ${quotes.size}`);
 for(const q of qu.slice(0,20))console.log(`[QUOTE] mint=${q.mint} pools=${q.pools}`);
 console.log(`[CROSS_VENUE_OVERLAP_COUNT] ${cand.length}`);
 for(const x of cand.slice(0,50))console.log(`[CANDIDATE] pump_pool=${x.pump_pool} base=${x.base_mint} quote=${x.quote_mint}`);
 console.log(cand.length?"[RESULT] VERIFIED_CROSS_VENUE_INTERSECTION_FOUND":"[RESULT] NO_VERIFIED_INTERSECTION");
 console.log(cand.length?"[NEXT_GATE] RESOLVE_EXACT_METEORA_PAIRS_AND_BIDIRECTIONAL_QUOTES":"[NEXT_GATE] RECONCILE_METEORA_MINT_INDEX");
 console.log("[OUTPUT] mtr_043_intersection.json");console.log("[MTR-043] COMPLETE");
}
main().catch(e=>{console.error("[MTR-043] FAIL");console.error(e?.stack||e);process.exit(1)});