
const fs = require("fs");
const {Connection,PublicKey} = require("@solana/web3.js");
const _dlmm = require("@meteora-ag/dlmm");
const DLMM = _dlmm.default || _dlmm.DLMM || _dlmm;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const PUMP=new PublicKey("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
const WSOL="So11111111111111111111111111111111111111112";
const USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
const USDT="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB";
const c=new Connection(RPC,"confirmed");
const key=v=>!v?null:typeof v==="string"?v:typeof v.toBase58==="function"?v.toBase58():v.address||null;
function dec(b,o){try{return b.length>=o+32?new PublicKey(b.subarray(o,o+32)).toBase58():null}catch{return null}}
function cls(q){return q===WSOL?"WSOL_DIRECT":q===USDC?"USDC_DIRECT":q===USDT?"USDT_DIRECT":"OTHER"}
async function main(){
 console.log("[MTR-036] START"); console.log("[SCOPE] discovery only; signing=false; sending=false; canonical_executor=false");
 const mr=await DLMM.getLbPairs(c);
 const rows=Array.isArray(mr)?mr:Array.isArray(mr?.pairs)?mr.pairs:Array.isArray(mr?.lbPairs)?mr.lbPairs:[];
 const pairs=[],byMint=new Map();
 for(const r of rows){const a=r?.account||r,p=key(r?.publicKey||r?.pubkey),x=key(a?.tokenXMint||a?.tokenX?.mint),y=key(a?.tokenYMint||a?.tokenY?.mint);if(!p||!x||!y)continue;const z={lb_pair:p,token_x:x,token_y:y};pairs.push(z);for(const m of[x,y]){if(!byMint.has(m))byMint.set(m,[]);byMint.get(m).push(z)}}
 console.log(`[METEORA_LBPAIR_COUNT] ${pairs.length}`); console.log(`[METEORA_DISTINCT_MINT_COUNT] ${byMint.size}`);
 const pa=await c.getProgramAccounts(PUMP,{commitment:"confirmed",encoding:"base64"});
 const pools=[],qc=new Map(),bases=new Set(),cand=[];
 for(const r of pa){const raw=r.account.data,b64=Array.isArray(raw)?raw[0]:raw;if(typeof b64!=="string")continue;const b=Buffer.from(b64,"base64"),base=dec(b,9),quote=dec(b,41);if(!base||!quote||base===quote)continue;const p={pool:r.pubkey.toBase58(),base_mint:base,quote_mint:quote,account_bytes:b.length};pools.push(p);bases.add(base);qc.set(quote,(qc.get(quote)||0)+1);const mm=byMint.get(base)||[];if(mm.length)cand.push({...p,quote_class:cls(quote),meteora_pair_count:mm.length,meteora_pairs:mm})}
 const rank={WSOL_DIRECT:0,USDC_DIRECT:1,USDT_DIRECT:2,OTHER:3};cand.sort((a,b)=>(rank[a.quote_class]??9)-(rank[b.quote_class]??9)||b.meteora_pair_count-a.meteora_pair_count);
 const report={schema:"MTR-035",scope:"FULL_PUMPSWAP_QUOTE_UNIVERSE_TO_METEORA_MINT_INTERSECTION",execution_authority:false,signing:false,sending:false,canonical_executor_touched:false,rpc:RPC,pumpswap_program_accounts:pa.length,pumpswap_decoded_pools:pools.length,pumpswap_distinct_base_mints:bases.size,pumpswap_distinct_quote_mints:qc.size,meteora_lb_pairs:pairs.length,meteora_distinct_mints:byMint.size,overlap_candidates:cand.length,quote_universe:[...qc].sort((a,b)=>b[1]-a[1]).map(([mint,pool_count])=>({mint,pool_count,class:cls(mint)})),candidates:cand};
 fs.writeFileSync("mtr_036_candidates.json",JSON.stringify(report,null,2));
 console.log(`[PUMPSWAP_PROGRAM_ACCOUNT_COUNT] ${pa.length}`);console.log(`[PUMPSWAP_DECODED_POOL_COUNT] ${pools.length}`);console.log(`[PUMPSWAP_BASE_MINT_COUNT] ${bases.size}`);console.log(`[PUMPSWAP_QUOTE_MINT_COUNT] ${qc.size}`);console.log(`[CROSS_VENUE_OVERLAP_COUNT] ${cand.length}`);
 for(const x of cand.slice(0,30))console.log(`[CANDIDATE] class=${x.quote_class} pump_pool=${x.pool} base=${x.base_mint} quote=${x.quote_mint} meteora_pairs=${x.meteora_pair_count}`);
 console.log(cand.length?"[RESULT] PHYSICAL_CROSS_VENUE_INTERSECTION_FOUND":"[RESULT] NO_FULL_UNIVERSE_INTERSECTION");
 console.log(cand.length?"[NEXT_GATE] EXACT_BIDIRECTIONAL_QUOTE_PROOF":"[GATE] STOP_BEFORE_QUOTE_OR_EXECUTION_BUILD");
 console.log("[OUTPUT] mtr_036_candidates.json");console.log("[MTR-036] COMPLETE");
}
main().catch(e=>{console.error("[MTR-036] FAIL");console.error(e?.stack||e);process.exit(1)});
