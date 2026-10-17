from pathlib import Path
T=Path("mtr_051_live_bidirectional_pure_quote_proof.cjs")
J=r"""const fs=require("fs"),{Connection,PublicKey,SystemProgram}=require("@solana/web3.js"),BN=require("bn.js");
const P=require("@pump-fun/pump-swap-sdk"),D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const WSOL="So11111111111111111111111111111111111111112",USDC="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
const c=new Connection(RPC,"confirmed"),input=new BN(10000000),slippage=0;
const S=x=>BN.isBN(x)?x.toString():String(x);
(async()=>{
 console.log("[MTR-051] START");console.log("[SCOPE] pure PumpSwap economics + live Meteora quotes; 0.010 SOL; signing=false; sending=false");
 const d=JSON.parse(fs.readFileSync("mtr_045_normalized_exact_pairs.json","utf8"));
 const r=d.rows.find(x=>x.base_mint===USDC&&x.quote_mint===WSOL);if(!r)throw Error("NO_USDC_WSOL_ROW");
 const pp=new PublicKey(r.pump_pool),mp=new PublicKey(r.meteora_pools[0]),online=new P.OnlinePumpAmmSdk(c);
 const s=await online.swapSolanaState(pp,SystemProgram.programId),dl=await DLMM.create(c,mp);
 const x=dl.tokenX.publicKey.toBase58(),y=dl.tokenY.publicKey.toBase58();
 console.log(`[PAIR] pump=${pp} meteora=${mp} meteora_x=${x} meteora_y=${y}`);
 const args=extra=>({slippage,baseReserve:s.poolBaseAmount,quoteReserve:s.poolQuoteAmount,virtualQuoteReserves:s.pool.virtualQuoteReserves,globalConfig:s.globalConfig,baseMintAccount:s.baseMintAccount,baseMint:s.baseMint,coinCreator:s.pool.coinCreator,creator:s.pool.creator,feeConfig:s.feeConfig,quoteMint:s.pool.quoteMint,isMayhemMode:s.pool.isMayhemMode,creatorFeeBps:s.pool.creatorFeeBps,...extra});
 async function mq(amount,inMint){if(inMint!==x&&inMint!==y)throw Error("METEORA_MINT_MISMATCH");const y2x=inMint===y,bins=await dl.getBinArrayForSwap(y2x),q=dl.swapQuote(amount,y2x,new BN(50),bins);return q.outAmount}
 const buy=P.buyQuoteInput(args({quote:input}));const midA=buy.base;
 console.log(`[PUMP_PURE_BUY] quote_in=${input} base_out=${midA} max_quote=${buy.maxQuote}`);
 const finA=await mq(midA,USDC),gA=finA.sub(input),bpA=Number(gA.muln(10000).div(input));
 console.log(`[ROUNDTRIP] direction=PUMP_TO_METEORA input_wsol=${input} intermediate_usdc=${midA} final_wsol=${finA} gross_raw=${gA} gross_bps=${bpA}`);
 const midB=await mq(input,WSOL);const sell=P.sellBaseInput(args({base:midB}));const finB=sell.uiQuote,gB=finB.sub(input),bpB=Number(gB.muln(10000).div(input));
 console.log(`[PUMP_PURE_SELL] base_in=${midB} quote_out=${finB} min_quote=${sell.minQuote}`);
 console.log(`[ROUNDTRIP] direction=METEORA_TO_PUMP input_wsol=${input} intermediate_usdc=${midB} final_wsol=${finB} gross_raw=${gB} gross_bps=${bpB}`);
 fs.writeFileSync("mtr_051_live_bidirectional_pure_quotes.json",JSON.stringify({schema:"MTR-051",pump_pool:String(pp),meteora_pool:String(mp),input_wsol_raw:S(input),pump_to_meteora:{intermediate_usdc:S(midA),final_wsol:S(finA),gross_raw:S(gA),gross_bps:bpA},meteora_to_pump:{intermediate_usdc:S(midB),final_wsol:S(finB),gross_raw:S(gB),gross_bps:bpB},signing:false,sending:false},null,2));
 console.log("[RESULT] LIVE_BIDIRECTIONAL_PURE_QUOTE_PROOF_COMPLETE");console.log("[NEXT_GATE] BOUNDED_MULTI_PAIR_MULTI_SIZE_FEE_ADJUSTED_RANKING");console.log("[OUTPUT] mtr_051_live_bidirectional_pure_quotes.json");console.log("[MTR-051] COMPLETE");
})().catch(e=>{console.error("[MTR-051] FAIL");console.error(e.stack||e);process.exit(1)});
"""
T.write_text(J,encoding="utf-8")
print(f"[BUILD] wrote {T}")
print("[BUILD] exact live two-direction economics using exported PumpSwap pure quote functions")
print("[SCOPE] 0.010 SOL quote-only; no private key; no signing; no sending; canonical executor untouched")
