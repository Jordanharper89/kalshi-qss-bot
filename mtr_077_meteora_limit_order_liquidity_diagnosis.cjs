const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const MET=new PublicKey("4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const INPUT=new BN("10000000");
const c=new Connection(RPC,"confirmed");

function bn(v){
 try{return new BN(v?.toString?.()??String(v??0))}
 catch{return new BN(0)}
}
function dumpBin(tag,b){
 if(!b)return;
 const amountX=bn(b.amountX),amountY=bn(b.amountY);
 const open=bn(b.openOrderAmount);
 const processed=bn(b.processedOrderRemainingAmount);
 const totalOrder=open.add(processed);

 console.log(`[${tag}] binId=${b.binId}`);
 console.log(`[${tag}] amountX=${amountX} amountY=${amountY}`);
 console.log(`[${tag}] openOrderAmount=${open}`);
 console.log(`[${tag}] processedOrderRemainingAmount=${processed}`);
 console.log(`[${tag}] totalOrderAmount=${totalOrder}`);
 console.log(`[${tag}] limitOrderAskSide=${b.limitOrderAskSide}`);
 console.log(`[${tag}] price=${b.price}`);
}

(async()=>{
 console.log("[MTR-077] START");
 console.log("[SCOPE] LimitOrder pool liquidity diagnosis; read-only");

 const m=await DLMM.create(c,MET);
 const x=m.tokenX.mint.address,y=m.tokenY.mint.address;
 const y2x=W.equals(y);

 console.log(`[PAIR] ${MET.toBase58()}`);
 console.log(`[TOKEN_X] ${x.toBase58()}`);
 console.log(`[TOKEN_Y] ${y.toBase58()}`);
 console.log(`[FUNCTION_TYPE] ${m.lbPair.parameters.functionType}`);
 console.log(`[ACTIVE_ID] ${m.lbPair.activeId}`);
 console.log(`[DIRECTION_Y_TO_X] ${y2x}`);

 const arrays=await m.getBinArrayForSwap(y2x);
 console.log(`[BIN_ARRAYS] ${arrays.length}`);

 let found=0;
 for(const arr of arrays){
  const bins=arr.account?.bins||arr.bins||[];
  for(const b of bins){
   const ax=bn(b.amountX),ay=bn(b.amountY);
   const oo=bn(b.openOrderAmount);
   const pr=bn(b.processedOrderRemainingAmount);
   if(ax.gt(new BN(0))||ay.gt(new BN(0))||
      oo.gt(new BN(0))||pr.gt(new BN(0))){
    dumpBin(`BIN_${found}`,b);
    found++;
    if(found>=12)break;
   }
  }
  if(found>=12)break;
 }
 console.log(`[NONEMPTY_BINS_SHOWN] ${found}`);

 const q=m.swapQuote(INPUT,y2x,new BN(100),arrays);
 console.log(`[QUOTE_INPUT] ${INPUT}`);
 console.log(`[QUOTE_OUT] ${q.outAmount}`);
 console.log(`[QUOTE_MIN] ${q.minOutAmount}`);
 console.log(`[QUOTE_FEE] ${q.fee}`);
 console.log(`[QUOTE_PROTOCOL_FEE] ${q.protocolFee}`);
 console.log(`[QUOTE_BIN_ARRAYS] ${q.binArraysPubkey.map(x=>x.toBase58()).join(",")}`);

 console.log("[RESULT] LIMIT_ORDER_BIN_LIQUIDITY_CAPTURED");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-077] COMPLETE");
})().catch(e=>{
 console.error("[MTR-077] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
