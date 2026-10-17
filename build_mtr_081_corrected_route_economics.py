from pathlib import Path

target=Path("mtr_081_corrected_route_economics.cjs")
target.write_text(r'''const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js");
const D=require("@meteora-ag/dlmm");
const P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";

const MET=new PublicKey("4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4");
const PUMP=new PublicKey("FnzKY6x7entQ1eR3D225dQyT7ybfka4PskBMQhb8L3CC");
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const INPUT=new BN("10000000");
const c=new Connection(RPC,"confirmed");

function b(v){return new BN(v.toString())}

(async()=>{
 console.log("[MTR-081] START");
 console.log("[SCOPE] corrected Meteora->Pump gross economics; read-only");

 const m=await DLMM.create(c,MET);
 const X=m.tokenX.mint.address,Y=m.tokenY.mint.address;

 if(!Y.equals(W))throw Error("EXPECTED_METEORA_TOKEN_Y_WSOL");

 const swapForY=false;
 const bins=await m.getBinArrayForSwap(swapForY);
 const mq=m.swapQuote(INPUT,swapForY,new BN(100),bins);

 console.log(`[METEORA_X] ${X.toBase58()}`);
 console.log(`[METEORA_Y] ${Y.toBase58()}`);
 console.log(`[METEORA_INPUT] ${INPUT}`);
 console.log(`[METEORA_OUT] ${mq.outAmount}`);
 console.log(`[METEORA_MIN] ${mq.minOutAmount}`);
 console.log(`[METEORA_FEE] ${mq.fee}`);

 const Online=P.OnlinePumpAmmSdk;
 const sdk=new Online(c);
 const state=await sdk.swapSolanaState(PUMP,USER);

 const pb=state.pool?.baseMint||state.baseMint;
 const pq=state.pool?.quoteMint||state.quoteMint;
 console.log(`[PUMP_BASE] ${pb.toBase58()}`);
 console.log(`[PUMP_QUOTE] ${pq.toBase58()}`);

 if(!pb.equals(X))throw Error("PUMP_BASE_NOT_METEORA_X");
 if(!pq.equals(W))throw Error("PUMP_QUOTE_NOT_WSOL");

 const q=P.sellBaseInput({
  ...state,
  base:b(mq.outAmount),
  slippage:0
 });

 console.log(`[PUMP_BASE_IN] ${mq.outAmount}`);
 console.log(`[PUMP_UI_QUOTE] ${q.uiQuote}`);
 console.log(`[PUMP_MIN_QUOTE] ${q.minQuote}`);
 console.log(`[PUMP_INTERNAL_QUOTE] ${q.internalQuoteAmountOut}`);

 const finalRaw=b(q.internalQuoteAmountOut);
 const gross=finalRaw.sub(INPUT);
 const bps=gross.mul(new BN(10000)).div(INPUT);

 console.log(`[FINAL_WSOL_RAW] ${finalRaw}`);
 console.log(`[GROSS_RAW] ${gross}`);
 console.log(`[GROSS_BPS] ${bps}`);

 if(gross.gt(new BN(0)))
  console.log("[RESULT] CORRECTED_ROUTE_GROSS_POSITIVE");
 else
  console.log("[RESULT] CORRECTED_ROUTE_GROSS_NOT_POSITIVE");

 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-081] COMPLETE");
})().catch(e=>{
 console.error("[MTR-081] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
''',encoding="utf-8")

print(f"[BUILD] wrote {target}")
print("[BUILD] corrected Meteora-to-Pump route economics")
print("[SCOPE] live quote/state only; no private key; no signing; no sending")