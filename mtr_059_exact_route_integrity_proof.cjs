const {Connection,PublicKey,SystemProgram}=require("@solana/web3.js");
const BN=require("bn.js"),P=require("@pump-fun/pump-swap-sdk");
const D=require("@meteora-ag/dlmm"),DLMM=D.default||D.DLMM||D;

const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
 "https://api.mainnet-beta.solana.com";
const PUMP="FnzKY6x7entQ1eR3D225dQyT7ybfka4PskBMQhb8L3CC";
const MET="4pANrqEvjad4xEghrCbAAJfBm8KyNvYMKk1cuGW8erE4";
const WSOL="So11111111111111111111111111111111111111112";
const c=new Connection(RPC,"confirmed");
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const SIZES=[new BN("1000000"),new BN("10000000")];

async function mintInfo(pk){
 const x=await c.getParsedAccountInfo(new PublicKey(pk),"confirmed");
 const v=x.value&&x.value.data&&x.value.data.parsed&&x.value.data.parsed.info;
 if(!v)throw Error("MINT_PARSE_FAILED_"+pk);
 return {mint:pk,decimals:v.decimals,supply:v.supply};
}

async function tokenBalance(pk){
 const x=await c.getTokenAccountBalance(new PublicKey(pk),"confirmed");
 return {raw:x.value.amount,decimals:x.value.decimals,ui:x.value.uiAmountString};
}

async function meteoraQuote(pool,input,inMint){
 const x=pool.tokenX.mint.address.toBase58(),y=pool.tokenY.mint.address.toBase58();
 if(inMint!==x&&inMint!==y)throw Error("METEORA_INPUT_MINT_NOT_IN_POOL");
 const swapYtoX=inMint===y;
 const bins=await pool.getBinArrayForSwap(swapYtoX);
 const q=pool.swapQuote(input,swapYtoX,new BN(50),bins);
 return {out:q.outAmount,x,y,swapYtoX};
}

(async()=>{
 console.log("[MTR-059] START");
 console.log("[SCOPE] one exact route integrity proof; no signing; no sending; executor untouched");

 const on=new P.OnlinePumpAmmSdk(c);
 const s=await on.swapSolanaState(new PublicKey(PUMP),SystemProgram.programId);
 const m=await DLMM.create(c,new PublicKey(MET));

 const base=s.pool.baseMint.toBase58(),quote=s.pool.quoteMint.toBase58();
 const mx=m.tokenX.mint.address.toBase58(),my=m.tokenY.mint.address.toBase58();

 console.log(`[PUMP_MINTS] base=${base} quote=${quote}`);
 console.log(`[METEORA_MINTS] x=${mx} y=${my}`);
 if(quote!==WSOL)throw Error("PUMP_QUOTE_NOT_WSOL");
 if(!((mx===base&&my===WSOL)||(my===base&&mx===WSOL)))
  throw Error("EXACT_PAIR_MISMATCH");

 const bi=await mintInfo(base),wi=await mintInfo(WSOL);
 console.log(`[DECIMALS] base=${bi.decimals} wsol=${wi.decimals}`);

 const pb=await tokenBalance(s.pool.poolBaseTokenAccount);
 const pq=await tokenBalance(s.pool.poolQuoteTokenAccount);
 console.log(`[PUMP_VAULTS] base_raw=${pb.raw} quote_raw=${pq.raw}`);
 console.log(`[PUMP_STATE] base_raw=${s.poolBaseAmount} quote_raw=${s.poolQuoteAmount}`);

 console.log(`[METEORA_ACTIVE_ID] ${m.lbPair.activeId}`);
 console.log(`[METEORA_BIN_STEP] ${m.lbPair.binStep}`);

 const common={
  slippage:0,baseReserve:s.poolBaseAmount,quoteReserve:s.poolQuoteAmount,
  virtualQuoteReserves:s.pool.virtualQuoteReserves,globalConfig:s.globalConfig,
  baseMintAccount:s.baseMintAccount,baseMint:s.pool.baseMint,
  coinCreator:s.pool.coinCreator,creator:s.pool.creator,feeConfig:s.feeConfig,
  quoteMint:s.pool.quoteMint,isMayhemMode:s.pool.isMayhemMode,
  creatorFeeBps:s.pool.creatorFeeBps
 };

 const rows=[];
 for(const input of SIZES){
  const mq=await meteoraQuote(m,input,WSOL);
  const mid=mq.out;
  const sell=P.sellBaseInput({...common,base:mid});
  const final=sell.uiQuote;
  const gross=final.sub(input);
  const bps=Number(gross.muln(10000).div(input));

  console.log(`[M2P] input_wsol=${input} meteora_base=${mid} pump_wsol=${final} gross_raw=${gross} gross_bps=${bps}`);
  rows.push({input_wsol:input.toString(),meteora_base:mid.toString(),
   pump_wsol:final.toString(),gross_raw:gross.toString(),gross_bps:bps});

  await sleep(1200);
 }

 const stable=rows.every(x=>x.gross_bps>0&&x.gross_bps<100000);
 if(!stable)throw Error("ROUTE_INTEGRITY_RANGE_REJECTED");

 const fs=require("fs");
 fs.writeFileSync("mtr_059_exact_route_integrity_proof.json",JSON.stringify({
  schema:"MTR-059",pump:PUMP,meteora:MET,base,quote,
  base_decimals:bi.decimals,wsol_decimals:wi.decimals,
  pump_base_vault:pb,pump_quote_vault:pq,rows,
  signing:false,sending:false
 },null,2));

 console.log("[RESULT] EXACT_ROUTE_RAW_UNIT_INTEGRITY_PASS");
 console.log("[NEXT_GATE] FRESH_FEE_ADJUSTED_ROUTE_PROOF");
 console.log("[OUTPUT] mtr_059_exact_route_integrity_proof.json");
 console.log("[MTR-059] COMPLETE");
})().catch(e=>{
 console.error("[MTR-059] FAIL");
 console.error(e.stack||e);
 process.exit(1);
});
