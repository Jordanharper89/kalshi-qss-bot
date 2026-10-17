const fs=require("fs");
const {Connection,PublicKey}=require("@solana/web3.js");
const BN=require("bn.js"),D=require("@meteora-ag/dlmm"),P=require("@pump-fun/pump-swap-sdk");
const DLMM=D.default||D.DLMM||D;
const RPC=process.env.QSB_SOLANA_RPC_URL||process.env.SOLANA_RPC_URL||
"https://api.mainnet-beta.solana.com";
const W=new PublicKey("So11111111111111111111111111111111111111112");
const USER=new PublicKey("CMth6wnNYKr4yaLWWioD4stRxk7ypX4gomqsdzArA5oR");
const INPUT=new BN("10000000"),FEE_REF=new BN("5000");
const c=new Connection(RPC,"confirmed"),sdk=new P.OnlinePumpAmmSdk(c);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function sellArgs(s,base){
 const {baseMint,baseMintAccount,feeConfig,globalConfig,pool,poolBaseAmount,poolQuoteAmount}=s;
 return {base,slippage:0,baseReserve:poolBaseAmount,quoteReserve:poolQuoteAmount,
 virtualQuoteReserves:pool.virtualQuoteReserves,globalConfig,baseMintAccount,baseMint,
 coinCreator:pool.coinCreator,creator:pool.creator,feeConfig,quoteMint:pool.quoteMint,
 isMayhemMode:pool.isMayhemMode,creatorFeeBps:pool.creatorFeeBps};
}
function buyArgs(s,quote){const a=sellArgs(s,new BN(0));delete a.base;a.quote=quote;return a}
function bps(x){return x.mul(new BN(10000)).div(INPUT).toString()}
function save(rows,done,holds){
 rows.sort((a,b)=>BigInt(a.gross)>BigInt(b.gross)?-1:BigInt(a.gross)<BigInt(b.gross)?1:0);
 fs.writeFileSync("mtr_106_deep_replenishment_exact_010_economics.json",
 JSON.stringify({done,holds,positive:rows.filter(x=>BigInt(x.gross)>0n).length,ranking:rows},null,2));
}

(async()=>{
 console.log("[MTR-106] START");
 console.log("[SCOPE] deep replenishment corrected exact 0.010-SOL economics");

 const src="mtr_105_ultra_hot_meteora_reserve_filter.json";
 if(!fs.existsSync(src))throw Error("MTR_105_NOT_FOUND");
 const j=JSON.parse(fs.readFileSync(src,"utf8"));
 const R=(j.rows||[]).filter(r=>Number(r.meteora_wsol_sol)>=1);
 console.log(`[DEEP_LINKS] ${R.length}`);
 console.log(`[INPUT_RAW] ${INPUT}`);

 const states=new Map(),out=[];
 let done=0,holds=0;

 for(const r of R){
  try{
   let s=states.get(r.pump_pool);
   if(!s){
    s=await sdk.swapSolanaState(new PublicKey(r.pump_pool),USER);
    states.set(r.pump_pool,s);
    await sleep(650);
   }
   if(!s.pool.quoteMint.equals(W)){holds++;continue}

   const m=await DLMM.create(c,new PublicKey(r.meteora_pool));
   const X=m.tokenX.mint.address,Y=m.tokenY.mint.address,base=s.baseMint;
   if(!((X.equals(base)&&Y.equals(W))||(Y.equals(base)&&X.equals(W)))){holds++;continue}

   try{
    const dir=W.equals(X),bins=await m.getBinArrayForSwap(dir);
    const mq=m.swapQuote(INPUT,dir,new BN(100),bins);
    const mid=new BN(mq.outAmount.toString());
    const pq=P.sellBaseInput(sellArgs(s,mid));
    const final=new BN(pq.uiQuote.toString()),gross=final.sub(INPUT),net=gross.sub(FEE_REF);
    const row={direction:"METEORA_TO_PUMP",pump:r.pump_pool,meteora:r.meteora_pool,
     meteora_wsol_sol:r.meteora_wsol_sol,middle:mid.toString(),final:final.toString(),
     gross:gross.toString(),gross_bps:bps(gross),net_ref:net.toString(),net_ref_bps:bps(net)};
    out.push(row);
    if(gross.gt(new BN(0)))
     console.log(`[POSITIVE] dir=M2P bps=${row.gross_bps} gross=${gross} pump=${r.pump_pool} meteora=${r.meteora_pool}`);
   }catch(e){holds++}

   try{
    const pq=P.buyQuoteInput(buyArgs(s,INPUT));
    const mid=new BN(pq.base.toString()),dir=base.equals(X);
    const bins=await m.getBinArrayForSwap(dir);
    const mq=m.swapQuote(mid,dir,new BN(100),bins);
    const final=new BN(mq.outAmount.toString()),gross=final.sub(INPUT),net=gross.sub(FEE_REF);
    const row={direction:"PUMP_TO_METEORA",pump:r.pump_pool,meteora:r.meteora_pool,
     meteora_wsol_sol:r.meteora_wsol_sol,middle:mid.toString(),final:final.toString(),
     gross:gross.toString(),gross_bps:bps(gross),net_ref:net.toString(),net_ref_bps:bps(net)};
    out.push(row);
    if(gross.gt(new BN(0)))
     console.log(`[POSITIVE] dir=P2M bps=${row.gross_bps} gross=${gross} pump=${r.pump_pool} meteora=${r.meteora_pool}`);
   }catch(e){holds++}

   done++;
   if(done%10===0){
    save(out,done,holds);
    console.log(`[CHECKPOINT] done=${done}/${R.length} quotes=${out.length} positive=${out.filter(x=>BigInt(x.gross)>0n).length} holds=${holds}`);
   }
  }catch(e){holds++}

  await sleep(800);
 }

 save(out,done,holds);
 out.sort((a,b)=>BigInt(a.gross)>BigInt(b.gross)?-1:BigInt(a.gross)<BigInt(b.gross)?1:0);
 const pos=out.filter(x=>BigInt(x.gross)>0n);

 console.log(`[SUMMARY] links=${R.length} done=${done} quotes=${out.length} positive=${pos.length} holds=${holds}`);
 for(const x of out.slice(0,20))
  console.log(`[TOP] dir=${x.direction} bps=${x.gross_bps} gross=${x.gross} net5000=${x.net_ref} pump=${x.pump} meteora=${x.meteora}`);

 console.log(pos.length?"[RESULT] DEEP_REPLENISHMENT_POSITIVES_FOUND":
 "[RESULT] DEEP_REPLENISHMENT_NO_010_POSITIVES");
 console.log("[NOTE] 5000 lamports remains historical network-fee reference");
 console.log("[OUTPUT] mtr_106_deep_replenishment_exact_010_economics.json");
 console.log("[PRIVATE_KEY] NOT_USED");
 console.log("[BROADCAST] FALSE");
 console.log("[MTR-106] COMPLETE");
})().catch(e=>{console.error("[MTR-106] FAIL");console.error(e.stack||e);process.exit(1)});
