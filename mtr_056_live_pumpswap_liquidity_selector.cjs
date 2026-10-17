const fs=require("fs"),{Connection,PublicKey,SystemProgram}=require("@solana/web3.js");
const P=require("@pump-fun/pump-swap-sdk");
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const W="So11111111111111111111111111111111111111112",c=new Connection(RPC,"confirmed");
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 console.log("[MTR-056] START");
 console.log("[SCOPE] live PumpSwap liquidity selection; no signing; no sending; executor untouched");
 const d=JSON.parse(fs.readFileSync("mtr_045_normalized_exact_pairs.json","utf8")),rows=d.rows||[];
 const on=new P.OnlinePumpAmmSdk(c),seen=new Set(),good=[];let tested=0,failed=0;
 for(const r of rows){
  if(good.length>=12||tested>=120)break;
  if(r.quote!==W||seen.has(r.pump_pool))continue;seen.add(r.pump_pool);tested++;
  try{
   const s=await on.swapSolanaState(new PublicKey(r.pump_pool),SystemProgram.programId);
   const br=BigInt(s.poolBaseAmount.toString()),qr=BigInt(s.poolQuoteAmount.toString());
   if(qr>=100000000n&&br>1000n){
    const x={pump_pool:r.pump_pool,base:r.base,quote:r.quote,base_reserve:br.toString(),
     quote_reserve:qr.toString(),quote_sol:Number(qr)/1e9,meteora_pools:r.meteora_pools};
    good.push(x);
    console.log(`[FUNDED] pump=${r.pump_pool} quote_sol=${x.quote_sol} base_raw=${br} meteora=${r.meteora_pools.length}`);
   }else console.log(`[REJECT_DUST] pump=${r.pump_pool} quote_raw=${qr} base_raw=${br}`);
  }catch(e){failed++;console.log(`[STATE_FAIL] pump=${r.pump_pool} ${String(e.message).slice(0,100)}`)}
  await sleep(120);
 }
 fs.writeFileSync("mtr_056_funded_pumpswap_candidates.json",JSON.stringify(
  {schema:"MTR-056",tested,failed,funded:good.length,rows:good,signing:false,sending:false},null,2));
 console.log(`[SUMMARY] tested=${tested} failed=${failed} funded=${good.length}`);
 if(!good.length)throw Error("NO_FUNDED_PUMPSWAP_CANDIDATES_IN_BOUNDED_SCAN");
 console.log("[RESULT] FUNDED_CROSS_VENUE_PUMPSWAP_SET_FOUND");
 console.log("[NEXT_GATE] LIVE_MULTI_SIZE_BIDIRECTIONAL_ROUNDTRIP_ON_FUNDED_SET");
 console.log("[OUTPUT] mtr_056_funded_pumpswap_candidates.json");
 console.log("[MTR-056] COMPLETE");
})().catch(e=>{console.error("[MTR-056] FAIL");console.error(e.stack||e);process.exit(1)});
