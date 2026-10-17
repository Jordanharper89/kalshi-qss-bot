const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const M=require("@meteora-ag/dlmm"),DLMM=M.default||M.DLMM||M;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const PUMP=new PublicKey("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
const WSOL="So11111111111111111111111111111111111111112";
const USDT="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB";
const c=new Connection(RPC,"confirmed");
const key=v=>!v?null:typeof v==="string"?v:typeof v.toBase58==="function"?v.toBase58():v.address||null;
function dec(b,o){try{return new PublicKey(b.subarray(o,o+32)).toBase58()}catch{return null}}
async function pumpByQuote(mint,label){
 console.log(`[PUMPSWAP_${label}] bounded memcmp query offset=41`);
 const rows=await c.getProgramAccounts(PUMP,{commitment:"confirmed",encoding:"base64",
  filters:[{memcmp:{offset:41,bytes:mint}}]});
 console.log(`[PUMPSWAP_${label}_POOL_COUNT] ${rows.length}`);
 return rows.map(r=>{const x=Array.isArray(r.account.data)?r.account.data[0]:r.account.data;
  const b=Buffer.from(x,"base64");return{pool:r.pubkey.toBase58(),base_mint:dec(b,9),
  quote_mint:dec(b,41),quote_class:label}}).filter(x=>x.base_mint&&x.quote_mint===mint);
}
async function main(){
 console.log("[MTR-037] START");
 console.log("[SCOPE] bounded WSOL/USDT discovery; signing=false; sending=false; canonical_executor=false");
 if(!DLMM||typeof DLMM.getLbPairs!=="function")throw Error("DLMM_CJS_EXPORT_FAILED");
 const raw=await DLMM.getLbPairs(c),rows=Array.isArray(raw)?raw:raw?.pairs||raw?.lbPairs||[];
 const byMint=new Map(),pairs=[];
 for(const r of rows){const a=r.account||r,p=key(r.publicKey||r.pubkey),
  x=key(a.tokenXMint||a.tokenX?.mint),y=key(a.tokenYMint||a.tokenY?.mint);
  if(!p||!x||!y)continue;const z={lb_pair:p,token_x:x,token_y:y};pairs.push(z);
  for(const m of[x,y]){if(!byMint.has(m))byMint.set(m,[]);byMint.get(m).push(z)}}
 console.log(`[METEORA_LBPAIR_COUNT] ${pairs.length}`);
 console.log(`[METEORA_DISTINCT_MINT_COUNT] ${byMint.size}`);
 const pump=[...await pumpByQuote(WSOL,"WSOL"),...await pumpByQuote(USDT,"USDT")],cand=[];
 for(const p of pump){const mm=byMint.get(p.base_mint)||[];
  if(mm.length)cand.push({...p,meteora_pair_count:mm.length,meteora_pairs:mm})}
 fs.writeFileSync("mtr_037_candidates.json",JSON.stringify({schema:"MTR-037",
  execution_authority:false,signing:false,sending:false,canonical_executor_touched:false,
  pumpswap_bounded_pools:pump.length,meteora_pairs:pairs.length,
  meteora_distinct_mints:byMint.size,overlap_candidates:cand.length,candidates:cand},null,2));
 console.log(`[BOUNDED_PUMPSWAP_POOL_COUNT] ${pump.length}`);
 console.log(`[CROSS_VENUE_OVERLAP_COUNT] ${cand.length}`);
 for(const x of cand.slice(0,40))console.log(`[CANDIDATE] class=${x.quote_class} pump_pool=${x.pool} base=${x.base_mint} quote=${x.quote_mint} meteora_pairs=${x.meteora_pair_count}`);
 console.log(cand.length?"[RESULT] PHYSICAL_PRIORITY_INTERSECTION_FOUND":"[RESULT] NO_WS0L_USDT_INTERSECTION");
 console.log(cand.length?"[NEXT_GATE] EXACT_BIDIRECTIONAL_QUOTE_PROOF":"[NEXT_GATE] BROADER_BOUNDED_QUOTE_DISCOVERY");
 console.log("[OUTPUT] mtr_037_candidates.json");console.log("[MTR-037] COMPLETE");
}
main().catch(e=>{console.error("[MTR-037] FAIL");console.error(e?.stack||e);process.exit(1)});