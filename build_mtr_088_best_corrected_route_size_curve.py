from pathlib import Path

p=Path("mtr_088_best_corrected_route_size_curve.cjs")
p.write_text(r'''const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const PUMP=new PublicKey("Gf7sXMoP8iRw4iiXmJ1nq4vxcRycbGXy5RL8a8LnTd3v");
const MET=new PublicKey("5rCf1DM8LjKTw4YqhnoLcngyZYeNnQqztScTogYHAS6");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const SIZES=["1000000","2500000","5000000","7500000","10000000",
             "12500000","15000000","20000000","30000000","50000000"].map(x=>new BN(x));
const FEE_REF=new BN("5000");
const c=new Connection(RPC,"confirmed");

function sellArgs(s,base){
 const {baseMint,baseMintAccount,feeConfig,globalConfig,pool,poolBaseAmount,poolQuoteAmount}=s;
 return {base,slippage:0,baseReserve:poolBaseAmount,quoteReserve:poolQuoteAmount,
  virtualQuoteReserves:pool.virtualQuoteReserves,globalConfig,baseMintAccount,baseMint,
  coinCreator:pool.coinCreator,creator:pool.creator,feeConfig,quoteMint:pool.quoteMint,
  isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps};
}
function buyArgs(s,quote){const a=sellArgs(s,new BN(0));delete a.base;a.quote=quote;return a}
function bps(v,input){return v.mul(new BN(10000)).div(input)}

(async()=>{
 console.log("[MTR-088] START");
 console.log("[SCOPE] best corrected route multi-size economics; read-only");

 const sdk=new P.OnlinePumpAmmSdk(c);
 const s=await sdk.swapSolanaState(PUMP,USER);
 const m=await DLMM.create(c,MET);
 const X=m.tokenX.mint.address,Y=m.tokenY.mint.address,base=s.baseMint;

 if(!s.pool.quoteMint.equals(W))throw Error("PUMP_NOT_WSOL_QUOTED");
 if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W))))
  throw Error("PAIR_MINT_MISMATCH");

 console.log(`[PUMP] ${PUMP}`);
 console.log(`[METEORA] ${MET}`);
 console.log(`[BASE] ${base}`);
 console.log(`[TOKEN_X] ${X}`);
 console.log(`[TOKEN_Y] ${Y}`);

 const out=[];

 for(const input of SIZES){
  try{
   const wToBase=W.equals(X);
   const bins=await m.getBinArrayForSwap(wToBase);
   const mq=m.swapQuote(input,wToBase,new BN(100),bins);
   const pq=P.sellBaseInput(sellArgs(s,new BN(mq.outAmount.toString())));
   const final=new BN(pq.uiQuote.toString());
   const gross=final.sub(input),net=gross.sub(FEE_REF);
   const row={direction:"METEORA_TO_PUMP",size:input.toString(),
    middle:mq.outAmount.toString(),final:final.toString(),gross:gross.toString(),
    gross_bps:bps(gross,input).toString(),net_ref:net.toString(),
    net_ref_bps:bps(net,input).toString()};
   out.push(row);
   console.log(`[SIZE] dir=M2P in=${input} gross=${gross} bps=${row.gross_bps} net5000=${net} net_bps=${row.net_ref_bps}`);
  }catch(e){console.log(`[HOLD] dir=M2P in=${input} ${String(e.message||e).slice(0,100)}`)}

  try{
   const pq=P.buyQuoteInput(buyArgs(s,input));
   const mid=new BN(pq.base.toString());
   const baseToW=base.equals(X);
   const bins=await m.getBinArrayForSwap(baseToW);
   const mq=m.swapQuote(mid,baseToW,new BN(100),bins);
   const final=new BN(mq.outAmount.toString());
   const gross=final.sub(input),net=gross.sub(FEE_REF);
   const row={direction:"PUMP_TO_METEORA",size:input.toString(),
    middle:mid.toString(),final:final.toString(),gross:gross.toString(),
    gross_bps:bps(gross,input).toString(),net_ref:net.toString(),
    net_ref_bps:bps(net,input).toString()};
   out.push(row);
   console.log(`[SIZE] dir=P2M in=${input} gross=${gross} bps=${row.gross_bps} net5000=${net} net_bps=${row.net_ref_bps}`);
  }catch(e){console.log(`[HOLD] dir=P2M in=${input} ${String(e.message||e).slice(0,100)}`)}
 }

 out.sort((a,b)=>BigInt(a.net_ref)>BigInt(b.net_ref)?-1:BigInt(a.net_ref)<BigInt(b.net_ref)?1:0);
 fs.writeFileSync("mtr_088_best_corrected_route_size_curve.json",JSON.stringify({ranking:out},null,2));

 const positive=out.filter(x=>BigInt(x.net_ref)>0n);
 const best=out[0];
 console.log(`[BEST] dir=${best?.direction} size=${best?.size} gross_bps=${best?.gross_bps} net_ref=${best?.net_ref} net_ref_bps=${best?.net_ref_bps}`);
 console.log(positive.length?"[RESULT] CORRECTED_ROUTE_NET_REFERENCE_POSITIVE":
  "[RESULT] CORRECTED_ROUTE_NET_REFERENCE_NOT_POSITIVE");
 console.log("[NOTE] 5000 lamports is historical fee reference; exact atomic fee must be recomputed later");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-088] COMPLETE");
})().catch(e=>{console.error("[MTR-088] FAIL");console.error(e.stack||e);process.exit(1)});
''',encoding="utf-8")

print(f"[BUILD] wrote {p}")
print("[BUILD] best corrected route size-curve diagnostic")
print("[SCOPE] read-only; 5000-lamport historical fee reference; no signing; no sending")