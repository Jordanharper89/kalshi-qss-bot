from pathlib import Path
T=Path("mtr_047_live_bidirectional_quote_proof.cjs")
J=r"""const fs=require("fs"),{Connection,PublicKey}=require("@solana/web3.js"),BN=require("bn.js");
const P=require("@pump-fun/pump-swap-sdk"),D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||"https://api.mainnet-beta.solana.com";
const WSOL="So11111111111111111111111111111111111111112",c=new Connection(RPC,"confirmed");
const val=(o,n)=>{for(const k of n)if(o&&o[k]!=null)return o[k];return null}, bn=x=>BN.isBN(x)?x:new BN(String(x));
function dump(tag,o){console.log(`[${tag}] ${JSON.stringify(o,(k,v)=>typeof v==="bigint"?v.toString():BN.isBN(v)?v.toString():v)}`)}
(async()=>{
 console.log("[MTR-047] START");console.log("[SCOPE] live bidirectional quote proof; input=0.010 SOL; signing=false; sending=false");
 const d=JSON.parse(fs.readFileSync("mtr_045_normalized_exact_pairs.json","utf8")),r=d.rows.find(x=>x.base_mint===P.USDC_MINT.toBase58()&&x.quote_mint===WSOL)||d.rows[0];
 const pumpPool=new PublicKey(r.pump_pool),metPool=new PublicKey(r.meteora_pools[0]),input=new BN(10000000);
 console.log(`[PAIR] pump=${r.pump_pool} meteora=${r.meteora_pools[0]} base=${r.base_mint} quote=${r.quote_mint}`);
 const online=new P.OnlinePumpAmmSdk(c),offline=new P.PumpAmmSdk();
 const state=await online.swapSolanaState(pumpPool);
 console.log("[PUMP_STATE] PASS");
 const dl=await DLMM.create(c,metPool);console.log("[METEORA_STATE] PASS");
 const x=dl.tokenX.publicKey.toBase58(),y=dl.tokenY.publicKey.toBase58();console.log(`[METEORA_MINTS] x=${x} y=${y}`);
 async function mq(amount,inMint){
  const swapYtoX=inMint===y,bins=await dl.getBinArrayForSwap(swapYtoX);
  const q=dl.swapQuote(amount,swapYtoX,new BN(50),bins);
  return bn(val(q,["outAmount","amountOut"]));
 }
 // Direction A: Pump WSOL -> base, then Meteora base -> WSOL.
 const pqA=offline.buyQuoteInput(state,input);
 dump("PUMP_BUY_QUOTE",pqA);
 const midA=bn(val(pqA,["base","baseAmountOut","amountOut","outputAmount"]));
 if(midA.lte(new BN(0)))throw Error("PUMP_BUY_OUTPUT_NOT_RESOLVED");
 const finA=await mq(midA,r.base_mint),grossA=finA.sub(input),bpsA=Number(grossA.muln(10000).div(input));
 console.log(`[ROUNDTRIP] direction=PUMP_TO_METEORA input_wsol=${input} intermediate=${midA} final_wsol=${finA} gross_raw=${grossA} gross_bps=${bpsA}`);
 // Direction B: Meteora WSOL -> base, then Pump base -> WSOL.
 const midB=await mq(input,WSOL);
 const pqB=offline.sellBaseInput(state,midB);
 dump("PUMP_SELL_QUOTE",pqB);
 const finB=bn(val(pqB,["quote","quoteAmountOut","amountOut","outputAmount"]));
 if(finB.lte(new BN(0)))throw Error("PUMP_SELL_OUTPUT_NOT_RESOLVED");
 const grossB=finB.sub(input),bpsB=Number(grossB.muln(10000).div(input));
 console.log(`[ROUNDTRIP] direction=METEORA_TO_PUMP input_wsol=${input} intermediate=${midB} final_wsol=${finB} gross_raw=${grossB} gross_bps=${bpsB}`);
 const out={schema:"MTR-047",pair:r,input_wsol_raw:input.toString(),pump_to_meteora:{intermediate:midA.toString(),final_wsol:finA.toString(),gross_raw:grossA.toString(),gross_bps:bpsA},meteora_to_pump:{intermediate:midB.toString(),final_wsol:finB.toString(),gross_raw:grossB.toString(),gross_bps:bpsB},signing:false,sending:false};
 fs.writeFileSync("mtr_047_live_bidirectional_quotes.json",JSON.stringify(out,null,2));
 console.log("[RESULT] LIVE_BIDIRECTIONAL_QUOTE_PROOF_COMPLETE");console.log("[NEXT_GATE] BOUNDED_MULTI_PAIR_FEE_ADJUSTED_RANKING");console.log("[MTR-047] COMPLETE");
})().catch(e=>{console.error("[MTR-047] FAIL");console.error(e.stack||e);process.exit(1)});
"""
T.write_text(J,encoding="utf-8")
print(f"[BUILD] wrote {T}")
print("[BUILD] live two-direction PumpSwap/Meteora quote proof from physically verified SDK methods")
print("[SCOPE] 0.010 SOL quote input only; no signing; no sending; canonical executor untouched")
