const fs=require("fs"),{Connection,PublicKey}=require("@solana/web3.js");
const M=require("@meteora-ag/dlmm"),DLMM=M.default||M.DLMM||M;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const PUMP=new PublicKey("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"),c=new Connection(RPC,"confirmed");
const A="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
function b58byte(n){if(n===0)return"1";let s="";while(n){s=A[n%58]+s;n=Math.floor(n/58)}return s}
const key=v=>!v?null:typeof v==="string"?v:typeof v.toBase58==="function"?v.toBase58():v.address||null;
function pk(b,o){try{return new PublicKey(b.subarray(o,o+32)).toBase58()}catch{return null}}
async function main(){
 console.log("[MTR-040] START");console.log("[SCOPE] memory-bounded partition proof; no signing; no sending");
 const raw=await DLMM.getLbPairs(c),rows=Array.isArray(raw)?raw:raw?.pairs||raw?.lbPairs||[],mints=new Set();
 for(const r of rows){const a=r.account||r,x=key(a.tokenXMint||a.tokenX?.mint),y=key(a.tokenYMint||a.tokenY?.mint);
  if(x)mints.add(x);if(y)mints.add(y)}
 console.log(`[METEORA_LBPAIR_COUNT] ${rows.length}`);console.log(`[METEORA_MINT_SET_COUNT] ${mints.size}`);
 let total=0,overlap=0;const candidates=[];
 for(let shard=0;shard<256;shard++){
  const rr=await c.getProgramAccounts(PUMP,{commitment:"confirmed",encoding:"base64",dataSlice:{offset:9,length:64},
   filters:[{memcmp:{offset:9,bytes:b58byte(shard)}}]});
  let valid=0,hit=0;
  for(const r of rr){const d=Array.isArray(r.account.data)?r.account.data[0]:r.account.data,b=Buffer.from(d,"base64");
   const base=pk(b,0),quote=pk(b,32);if(!base||!quote||base===quote)continue;valid++;total++;
   if(mints.has(base)){hit++;overlap++;candidates.push({pool:r.pubkey.toBase58(),base_mint:base,quote_mint:quote})}}
  fs.writeFileSync("mtr_040_checkpoint.json",JSON.stringify({completed_shard:shard,total,overlap,candidates},null,2));
  console.log(`[SHARD ${shard}/255] rpc=${rr.length} valid=${valid} hits=${hit} total=${total} overlap=${overlap}`);
 }
 fs.writeFileSync("mtr_040_candidates.json",JSON.stringify({schema:"MTR-040",execution_authority:false,
  signing:false,sending:false,pumpswap_pool_count:total,meteora_mint_count:mints.size,
  overlap_count:overlap,candidates},null,2));
 console.log(`[PUMPSWAP_POOL_COUNT] ${total}`);console.log(`[CROSS_VENUE_OVERLAP_COUNT] ${overlap}`);
 for(const x of candidates.slice(0,40))console.log(`[CANDIDATE] pool=${x.pool} base=${x.base_mint} quote=${x.quote_mint}`);
 console.log(overlap?"[RESULT] PHYSICAL_INTERSECTION_FOUND":"[RESULT] NO_INTERSECTION_FOUND");
 console.log(overlap?"[NEXT_GATE] RESOLVE_METEORA_PAIRS_AND_EXACT_QUOTES":"[NEXT_GATE] REASSESS_LAYOUT_OR_VENUE");
 console.log("[MTR-040] COMPLETE");
}
main().catch(e=>{console.error("[MTR-040] FAIL");console.error(e?.stack||e);process.exit(1)});