const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const M=require("@meteora-ag/dlmm"),DLMM=M.default||M.DLMM||M;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const PUMP=new PublicKey("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
const c=new Connection(RPC,"confirmed");
const key=v=>!v?null:typeof v==="string"?v:typeof v.toBase58==="function"?v.toBase58():v.address||null;
function pk(b,o){try{return new PublicKey(b.subarray(o,o+32)).toBase58()}catch{return null}}
async function main(){
 console.log("[MTR-038] START");
 console.log("[SCOPE] mint-slice inventory; signing=false; sending=false; canonical_executor=false");
 const mr=await DLMM.getLbPairs(c),rows=Array.isArray(mr)?mr:mr?.pairs||mr?.lbPairs||[];
 const byMint=new Map(),pairs=[];
 for(const r of rows){const a=r.account||r,p=key(r.publicKey||r.pubkey),
  x=key(a.tokenXMint||a.tokenX?.mint),y=key(a.tokenYMint||a.tokenY?.mint);
  if(!p||!x||!y)continue;const z={lb_pair:p,token_x:x,token_y:y};pairs.push(z);
  for(const m of[x,y]){if(!byMint.has(m))byMint.set(m,[]);byMint.get(m).push(z)}}
 console.log(`[METEORA_LBPAIR_COUNT] ${pairs.length}`);
 console.log(`[METEORA_DISTINCT_MINT_COUNT] ${byMint.size}`);
 console.log("[PUMPSWAP] requesting only bytes 9..72 via dataSlice");
 const pa=await c.getProgramAccounts(PUMP,{commitment:"confirmed",encoding:"base64",
  dataSlice:{offset:9,length:64}});
 console.log(`[PUMPSWAP_SLICED_ACCOUNT_COUNT] ${pa.length}`);
 const quoteCounts=new Map(),bases=new Set(),cand=[];
 for(const r of pa){const raw=r.account.data,b64=Array.isArray(raw)?raw[0]:raw;
  if(typeof b64!=="string")continue;const b=Buffer.from(b64,"base64");
  const base=pk(b,0),quote=pk(b,32);if(!base||!quote||base===quote)continue;
  bases.add(base);quoteCounts.set(quote,(quoteCounts.get(quote)||0)+1);
  const mm=byMint.get(base)||[];if(mm.length)cand.push({pump_pool:r.pubkey.toBase58(),
   base_mint:base,quote_mint:quote,meteora_pair_count:mm.length,meteora_pairs:mm})}
 const quotes=[...quoteCounts].sort((a,b)=>b[1]-a[1]).map(([mint,pool_count])=>({mint,pool_count}));
 cand.sort((a,b)=>b.meteora_pair_count-a.meteora_pair_count);
 fs.writeFileSync("mtr_038_inventory.json",JSON.stringify({schema:"MTR-038",execution_authority:false,
  signing:false,sending:false,canonical_executor_touched:false,pumpswap_accounts:pa.length,
  distinct_base_mints:bases.size,distinct_quote_mints:quoteCounts.size,quote_universe:quotes,
  meteora_pairs:pairs.length,cross_venue_candidates:cand.length,candidates:cand},null,2));
 console.log(`[PUMPSWAP_BASE_MINT_COUNT] ${bases.size}`);
 console.log(`[PUMPSWAP_QUOTE_MINT_COUNT] ${quoteCounts.size}`);
 console.log("[PUMPSWAP_QUOTE_UNIVERSE]");
 for(const q of quotes.slice(0,40))console.log(`[QUOTE] mint=${q.mint} pools=${q.pool_count}`);
 console.log(`[CROSS_VENUE_OVERLAP_COUNT] ${cand.length}`);
 for(const x of cand.slice(0,40))console.log(`[CANDIDATE] pump_pool=${x.pump_pool} base=${x.base_mint} quote=${x.quote_mint} meteora_pairs=${x.meteora_pair_count}`);
 console.log(cand.length?"[RESULT] PHYSICAL_FULL_MINT_INTERSECTION_FOUND":"[RESULT] NO_FULL_MINT_INTERSECTION");
 console.log(cand.length?"[NEXT_GATE] EXACT_BIDIRECTIONAL_QUOTE_PROOF":"[NEXT_GATE] REASSESS_VENUE_INTERSECTION");
 console.log("[OUTPUT] mtr_038_inventory.json");console.log("[MTR-038] COMPLETE");
}
main().catch(e=>{console.error("[MTR-038] FAIL");console.error(e?.stack||e);process.exit(1)});