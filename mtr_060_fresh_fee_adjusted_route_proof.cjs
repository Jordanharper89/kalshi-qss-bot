const {Connection,PublicKey,SystemProgram}=require("@solana/web3.js");
const BN=require("bn.js"),P=require("@pump-fun/pump-swap-sdk");
const D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;
const fs=require("fs");

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
 "https://api.mainnet-beta.solana.com";
const PUMP="FnzKY6x7entQ1eR3D225dQyT7ybfka4PskBMQhb8L3CC";
const MET="4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4";
const W="So11111111111111111111111111111111111111112";
const INPUT=new BN("10000000");
const c=new Connection(RPC,"confirmed");
const clean=o=>JSON.parse(JSON.stringify(o,(k,v)=>
 typeof v==="bigint"?v.toString():BN.isBN(v)?v.toString():v));

(async()=>{
 console.log("[MTR-060] START");
 console.log("[SCOPE] fresh exact-route venue-fee proof; no signing; no sending; executor untouched");

 const slot0=await c.getSlot("confirmed");
 const on=new P.OnlinePumpAmmSdk(c);
 const s=await on.swapSolanaState(new PublicKey(PUMP),SystemProgram.programId);
 const m=await DLMM.create(c,new PublicKey(MET));

 const base=s.pool.baseMint.toBase58(),quote=s.pool.quoteMint.toBase58();
 const mx=m.tokenX.mint.address.toBase58(),my=m.tokenY.mint.address.toBase58();
 if(quote!==W)throw Error("PUMP_QUOTE_NOT_WSOL");
 if(!((mx===base&&my===W)||(my===base&&mx===W)))throw Error("PAIR_MISMATCH");

 const y2x=W===my;
 const bins=await m.getBinArrayForSwap(y2x);
 const mq=m.swapQuote(INPUT,y2x,new BN(50),bins);
 const mid=mq.outAmount;

 const common={
  slippage:0,baseReserve:s.poolBaseAmount,quoteReserve:s.poolQuoteAmount,
  virtualQuoteReserves:s.pool.virtualQuoteReserves,globalConfig:s.globalConfig,
  baseMintAccount:s.baseMintAccount,baseMint:s.pool.baseMint,
  coinCreator:s.pool.coinCreator,creator:s.pool.creator,feeConfig:s.feeConfig,
  quoteMint:s.pool.quoteMint,isMayhemMode:s.pool.isMayhemMode,
  creatorFeeBps:s.pool.creatorFeeBps
 };

 const pq=P.sellBaseInput({...common,base:mid});
 const final=pq.uiQuote;
 const gross=final.sub(INPUT);
 const bps=Number(gross.muln(10000).div(INPUT));
 const slot1=await c.getSlot("confirmed");

 console.log(`[SLOTS] start=${slot0} end=${slot1} delta=${slot1-slot0}`);
 console.log(`[ROUTE] WSOL -> ${base} -> WSOL`);
 console.log(`[INPUT] wsol_raw=${INPUT}`);
 console.log(`[METEORA_OUT] base_raw=${mid}`);
 console.log(`[METEORA_QUOTE_KEYS] ${Object.keys(mq).sort().join(",")}`);
 console.log(`[METEORA_QUOTE] ${JSON.stringify(clean(mq)).slice(0,5000)}`);
 console.log(`[PUMP_QUOTE_KEYS] ${Object.keys(pq).sort().join(",")}`);
 console.log(`[PUMP_QUOTE] ${JSON.stringify(clean(pq)).slice(0,5000)}`);
 console.log(`[FINAL] wsol_raw=${final}`);
 console.log(`[VENUE_ADJUSTED_EDGE] raw=${gross} bps=${bps}`);

 if(gross.lten(0))throw Error("FRESH_ROUTE_NOT_POSITIVE");
 if(bps>100000)throw Error("ECONOMIC_SANITY_REJECT");

 const report={schema:"MTR-060",slot_start:slot0,slot_end:slot1,pump:PUMP,meteora:MET,
  base,quote,input_wsol_raw:INPUT.toString(),meteora_base_out:mid.toString(),
  pump_wsol_out:final.toString(),venue_adjusted_edge_raw:gross.toString(),
  venue_adjusted_bps:bps,meteora_quote:clean(mq),pump_quote:clean(pq),
  network_fee_included:false,priority_fee_included:false,signing:false,sending:false};

 fs.writeFileSync("mtr_060_fresh_fee_adjusted_route_proof.json",JSON.stringify(report,null,2));
 console.log("[RESULT] FRESH_VENUE_ADJUSTED_ROUTE_POSITIVE");
 console.log("[COST_BOUNDARY] network_fee=false priority_fee=false");
 console.log("[NEXT_GATE] EXACT_TWO_LEG_TRANSACTION_CONSTRUCTION_AND_FEE_SIMULATION");
 console.log("[OUTPUT] mtr_060_fresh_fee_adjusted_route_proof.json");
 console.log("[MTR-060] COMPLETE");
})().catch(e=>{
 console.error("[MTR-060] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
