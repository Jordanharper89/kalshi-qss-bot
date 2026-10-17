const fs=require("fs"),{Connection,PublicKey,SystemProgram}=require("@solana/web3.js"),BN=require("bn.js");
const P=require("@pump-fun/pump-swap-sdk"),D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const W="So11111111111111111111111111111111111111112",U="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
const c=new Connection(RPC,"confirmed"),input=new BN(10000000);
(async()=>{
 console.log("[MTR-052] START");console.log("[SCOPE] executable Meteora selector for proven PumpSwap USDC/WSOL row; no signing; no sending");
 const d=JSON.parse(fs.readFileSync("mtr_045_normalized_exact_pairs.json","utf8")),r=d.rows.find(x=>x.base_mint===U&&x.quote_mint===W);if(!r)throw Error("NO_USDC_WSOL_ROW");
 const on=new P.OnlinePumpAmmSdk(c),s=await on.swapSolanaState(new PublicKey(r.pump_pool),SystemProgram.programId);
 const common={slippage:0,baseReserve:s.poolBaseAmount,quoteReserve:s.poolQuoteAmount,virtualQuoteReserves:s.pool.virtualQuoteReserves,globalConfig:s.globalConfig,baseMintAccount:s.baseMintAccount,baseMint:s.baseMint,coinCreator:s.pool.coinCreator,creator:s.pool.creator,feeConfig:s.feeConfig,quoteMint:s.pool.quoteMint,isMayhemMode:s.pool.isMayhemMode,creatorFeeBps:s.pool.creatorFeeBps};
 const buy=P.buyQuoteInput({...common,quote:input}),pumpBase=buy.base;
 console.log(`[PUMP] pool=${r.pump_pool} quote_in=${input} base_out=${pumpBase}`);
 console.log(`[METEORA_CANDIDATES] ${r.meteora_pools.length}`);
 let ok=[],fail=0;
 for(let i=0;i<r.meteora_pools.length;i++){
  const pk=r.meteora_pools[i];
  try{
   const dl=await DLMM.create(c,new PublicKey(pk)),x=dl.tokenX.publicKey.toBase58(),y=dl.tokenY.publicKey.toBase58();
   async function q(a,m){const y2x=m===y;if(m!==x&&m!==y)throw Error("MINT_MISMATCH");const bins=await dl.getBinArrayForSwap(y2x);return dl.swapQuote(a,y2x,new BN(50),bins).outAmount}
   let a=null,b=null,ea=null,eb=null;
   try{a=await q(pumpBase,U)}catch(e){ea=String(e.message||e)}
   try{b=await q(input,W)}catch(e){eb=String(e.message||e)}
   if(a||b){ok.push({pool:pk,x,y,pump_to_meteora_out_wsol:a&&a.toString(),meteora_to_pump_mid_usdc:b&&b.toString(),a_error:ea,b_error:eb});console.log(`[EXECUTABLE] pool=${pk} P2M=${a||"FAIL"} M2P_mid=${b||"FAIL"}`)}
   else fail++;
  }catch(e){fail++}
 }
 console.log(`[SUMMARY] tested=${r.meteora_pools.length} executable_any=${ok.length} failed_both=${fail}`);
 if(!ok.length)throw Error("NO_EXECUTABLE_METEORA_POOL_FOR_USDC_WSOL_ROW");
 fs.writeFileSync("mtr_052_executable_meteora_pools.json",JSON.stringify({schema:"MTR-052",pump_pool:r.pump_pool,input_wsol_raw:input.toString(),pump_base_out:pumpBase.toString(),rows:ok,signing:false,sending:false},null,2));
 console.log("[RESULT] EXECUTABLE_METEORA_POOL_SET_FOUND");console.log("[NEXT_GATE] EXACT_BIDIRECTIONAL_ROUNDTRIP_ON_EXECUTABLE_POOL");console.log("[OUTPUT] mtr_052_executable_meteora_pools.json");console.log("[MTR-052] COMPLETE");
})().catch(e=>{console.error("[MTR-052] FAIL");console.error(e.stack||e);process.exit(1)});
