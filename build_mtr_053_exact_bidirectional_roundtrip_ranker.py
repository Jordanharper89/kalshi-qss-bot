from pathlib import Path
T=Path("mtr_053_exact_bidirectional_roundtrip_ranker.cjs")
J=r"""const fs=require("fs"),{Connection,PublicKey,SystemProgram}=require("@solana/web3.js"),BN=require("bn.js");
const P=require("@pump-fun/pump-swap-sdk"),D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com",c=new Connection(RPC,"confirmed");
const input=new BN(10000000),W="So11111111111111111111111111111111111111112",U="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
(async()=>{
 console.log("[MTR-053] START");console.log("[SCOPE] exact roundtrip ranking from saved MTR-052 executable set; no signing; no sending");
 const d=JSON.parse(fs.readFileSync("mtr_052_executable_meteora_pools.json","utf8")),rows=d.rows||[];if(!rows.length)throw Error("NO_MTR052_ROWS");
 const on=new P.OnlinePumpAmmSdk(c),s=await on.swapSolanaState(new PublicKey(d.pump_pool),SystemProgram.programId);
 const a={slippage:0,baseReserve:s.poolBaseAmount,quoteReserve:s.poolQuoteAmount,virtualQuoteReserves:s.pool.virtualQuoteReserves,globalConfig:s.globalConfig,baseMintAccount:s.baseMintAccount,baseMint:s.baseMint,coinCreator:s.pool.coinCreator,creator:s.pool.creator,feeConfig:s.feeConfig,quoteMint:s.pool.quoteMint,isMayhemMode:s.pool.isMayhemMode,creatorFeeBps:s.pool.creatorFeeBps};
 const buy=P.buyQuoteInput({...a,quote:input}),p2mMid=buy.base,out=[];
 console.log(`[INPUT] wsol=${input} pump_usdc_out=${p2mMid} saved_candidates=${rows.length}`);
 for(const r of rows){
  if(!r.pump_to_meteora_out_wsol&&!r.meteora_to_pump_mid_usdc)continue;
  let A=null,B=null;
  if(r.pump_to_meteora_out_wsol){let f=new BN(r.pump_to_meteora_out_wsol),g=f.sub(input);A={final_wsol:f.toString(),gross_raw:g.toString(),gross_bps:Number(g.muln(10000).div(input))}}
  if(r.meteora_to_pump_mid_usdc){let mid=new BN(r.meteora_to_pump_mid_usdc),q=P.sellBaseInput({...a,base:mid}),f=q.uiQuote,g=f.sub(input);B={intermediate_usdc:mid.toString(),final_wsol:f.toString(),gross_raw:g.toString(),gross_bps:Number(g.muln(10000).div(input))}}
  out.push({pool:r.pool,pump_to_meteora:A,meteora_to_pump:B});
 }
 const flat=[];for(const r of out){if(r.pump_to_meteora)flat.push({pool:r.pool,direction:"PUMP_TO_METEORA",...r.pump_to_meteora});if(r.meteora_to_pump)flat.push({pool:r.pool,direction:"METEORA_TO_PUMP",...r.meteora_to_pump})}
 flat.sort((x,y)=>y.gross_bps-x.gross_bps);
 flat.slice(0,20).forEach((r,i)=>console.log(`[RANK ${i+1}] direction=${r.direction} pool=${r.pool} final_wsol=${r.final_wsol} gross_raw=${r.gross_raw} gross_bps=${r.gross_bps}`));
 const pos=flat.filter(x=>BigInt(x.gross_raw)>0n);
 console.log(`[SUMMARY] routes=${flat.length} positive_gross=${pos.length} best_bps=${flat.length?flat[0].gross_bps:"NA"}`);
 fs.writeFileSync("mtr_053_exact_roundtrip_ranking.json",JSON.stringify({schema:"MTR-053",input_wsol_raw:input.toString(),routes:flat,positive_gross:pos.length,signing:false,sending:false},null,2));
 console.log(pos.length?"[RESULT] POSITIVE_GROSS_ROUNDTRIP_FOUND":"[RESULT] NO_POSITIVE_GROSS_ROUNDTRIP_IN_MTR052_SET");
 console.log("[NEXT_GATE] FRESH_MULTI_SIZE_FEE_ADJUSTED_REQUOTE_OF_TOP_ROUTES");console.log("[OUTPUT] mtr_053_exact_roundtrip_ranking.json");console.log("[MTR-053] COMPLETE");
})().catch(e=>{console.error("[MTR-053] FAIL");console.error(e.stack||e);process.exit(1)});
"""
T.write_text(J,encoding="utf-8")
print(f"[BUILD] wrote {T}")
print("[BUILD] exact two-direction roundtrip economics from saved MTR-052 executable amounts")
print("[SCOPE] no rescan; no private key; no signing; no sending; canonical executor untouched")
