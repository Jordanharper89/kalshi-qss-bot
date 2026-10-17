const {Connection,PublicKey,SystemProgram}=require("@solana/web3.js");
const BN=require("bn.js"),P=require("@pump-fun/pump-swap-sdk");
const D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
 "https://api.mainnet-beta.solana.com";
const PUMP="FnzKY6x7entQ1eR3D225dQyT7ybfka4PskBMQhb8L3CC";
const MET="4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4";
const W="So11111111111111111111111111111111111111112";
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const c=new Connection(RPC,"confirmed");

function sig(name,fn){
 const s=String(fn).replace(/\s+/g," ");
 console.log(`[SIGNATURE] ${name} arity=${fn.length} source=${s.slice(0,1400)}`);
}

(async()=>{
 console.log("[MTR-061] START");
 console.log("[SCOPE] exact two-leg instruction contract; no private key; no signing; no sending");

 const on=new P.OnlinePumpAmmSdk(c);
 const ps=await on.swapSolanaState(new PublicKey(PUMP),USER);
 const m=await DLMM.create(c,new PublicKey(MET));

 const base=ps.pool.baseMint.toBase58(),quote=ps.pool.quoteMint.toBase58();
 const mx=m.tokenX.mint.address.toBase58(),my=m.tokenY.mint.address.toBase58();

 console.log(`[PAIR] pump_base=${base} pump_quote=${quote}`);
 console.log(`[PAIR] meteora_x=${mx} meteora_y=${my}`);
 if(quote!==W||!((mx===base&&my===W)||(my===base&&mx===W)))
  throw Error("PAIR_CONTRACT_MISMATCH");

 sig("PumpAmmSdk.sellBaseInput",P.PumpAmmSdk.prototype.sellBaseInput);
 sig("PumpAmmSdk.sellInstructions",P.PumpAmmSdk.prototype.sellInstructions);
 sig("DLMM.swap",m.swap);
 sig("DLMM.swapQuote",m.swapQuote);

 const y2x=W===my,bins=await m.getBinArrayForSwap(y2x);
 const mq=m.swapQuote(new BN("10000000"),y2x,new BN(50),bins);
 console.log(`[METEORA_BOUND] in=10000000 out=${mq.outAmount} min_out=${mq.minOutAmount}`);
 console.log(`[BIN_ARRAYS] count=${mq.binArraysPubkey.length} keys=${mq.binArraysPubkey.map(x=>x.toBase58()).join(",")}`);

 const common={
  slippage:0,baseReserve:ps.poolBaseAmount,quoteReserve:ps.poolQuoteAmount,
  virtualQuoteReserves:ps.pool.virtualQuoteReserves,globalConfig:ps.globalConfig,
  baseMintAccount:ps.baseMintAccount,baseMint:ps.pool.baseMint,
  coinCreator:ps.pool.coinCreator,creator:ps.pool.creator,feeConfig:ps.feeConfig,
  quoteMint:ps.pool.quoteMint,isMayhemMode:ps.pool.isMayhemMode,
  creatorFeeBps:ps.pool.creatorFeeBps
 };
 const pq=P.sellBaseInput({...common,base:mq.outAmount});
 console.log(`[PUMP_BOUND] base_in=${mq.outAmount} quote_out=${pq.uiQuote} min_quote=${pq.minQuote}`);

 const methods=Object.getOwnPropertyNames(Object.getPrototypeOf(m)).filter(x=>
  /swap|instruction|transaction/i.test(x)).sort();
 console.log(`[METEORA_METHODS] ${methods.join(",")}`);

 console.log("[RESULT] EXACT_TWO_LEG_INSTRUCTION_CONTRACT_CAPTURED");
 console.log("[NEXT_GATE] UNSIGNED_ATOMIC_TWO_LEG_TRANSACTION_BUILD");
 console.log("[MTR-061] COMPLETE");
})().catch(e=>{
 console.error("[MTR-061] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
